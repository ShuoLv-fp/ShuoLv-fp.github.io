#!/usr/bin/env python3
"""Fail if removed paths or private probes remain in reachable Git history."""

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import subprocess


REMOVED_PREFIXES = ("phd_application_agent", "phd-advisor-summary")
TEXT_SUFFIXES = {
    ".css", ".csv", ".html", ".js", ".json", ".md", ".py", ".txt", ".xml", ".yaml", ".yml"
}


def git(repo, *args, input_bytes=None):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def normalize(value):
    return " ".join(value.split()).strip()


def candidate_values(text, word_counts):
    candidates = set()
    for match in re.finditer(r'"(?:[^"\\]|\\.)*"', text):
        try:
            candidates.add(normalize(json.loads(match.group(0))))
        except (json.JSONDecodeError, TypeError):
            pass
    for line in text.splitlines():
        cleaned = normalize(re.sub(r"^[\s>*#\-+0-9.)]+", "", line))
        if cleaned:
            candidates.add(cleaned)
        tokens = re.findall(r"[\w@.+-]+", cleaned, flags=re.UNICODE)
        for count in word_counts:
            if 0 < count <= 12 and len(tokens) >= count:
                for start in range(len(tokens) - count + 1):
                    candidates.add(" ".join(tokens[start:start + count]))
    return candidates


def verify_history(repo_root, manifest_path):
    repo_root = Path(repo_root).resolve()
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    objects = git(repo_root, "rev-list", "--objects", "--all").decode("utf-8", errors="replace").splitlines()
    entries = []
    removed = []
    for line in objects:
        oid, separator, path = line.partition(" ")
        entries.append((oid, path if separator else ""))
        if path and any(path == prefix or path.startswith(f"{prefix}/") for prefix in REMOVED_PREFIXES):
            removed.append(oid)
    if removed:
        raise RuntimeError(f"removed path remains in {len(set(removed))} reachable object(s)")

    leak = manifest["leakCheck"]
    key = bytes.fromhex(leak["key"])
    probes = {item["digest"] for item in leak["probes"]}
    word_counts = {item["words"] for item in leak["probes"]}
    paths_by_oid = {}
    for oid, path in entries:
        if path:
            paths_by_oid.setdefault(oid, set()).add(path)
    object_ids = sorted(paths_by_oid)
    checks = git(
        repo_root,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        input_bytes=("\n".join(object_ids) + "\n").encode("ascii"),
    ).decode("ascii", errors="replace")

    matched = []
    for line in checks.splitlines():
        oid, object_type, size_text = line.split()
        if object_type != "blob" or int(size_text) > 5_000_000:
            continue
        paths = paths_by_oid.get(oid, set())
        if not any(Path(path).suffix.lower() in TEXT_SUFFIXES for path in paths):
            continue
        text = git(repo_root, "cat-file", "blob", oid).decode("utf-8", errors="ignore")
        for candidate in candidate_values(text, word_counts):
            digest = hmac.new(key, candidate.encode("utf-8"), hashlib.sha256).hexdigest()
            if digest in probes:
                matched.append(oid)
                break
    if matched:
        raise RuntimeError(f"private probe remains in {len(set(matched))} reachable object(s)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    verify_history(args.repo, args.manifest)
    print("Rewritten history verification passed; removed paths and private probes are absent.")


if __name__ == "__main__":
    main()
