#!/usr/bin/env python3
"""Create ignored private backups and a Cloudflare import bundle."""

import argparse
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import shutil


COLLECTIONS = ("profile", "faculty", "programs", "applications", "artifacts")


def canonical_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def normalize_probe(value):
    return " ".join(str(value).split()).strip()


def probe_values(seed):
    values = set()
    for faculty in seed["faculty"]:
        for key in ("name", "display_name"):
            value = normalize_probe(faculty.get(key, ""))
            if len(value) >= 6:
                values.add(value)
    for artifact in seed["artifacts"]:
        for key in ("subject", "content"):
            value = normalize_probe(artifact.get(key, ""))
            if len(value) >= 6:
                values.add(value)
    return sorted(values)


def tree_digest(root):
    digest = hashlib.sha256()
    count = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        count += 1
    return count, digest.hexdigest()


def write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def prepare(source_root, private_root):
    source_root = Path(source_root).resolve()
    private_root = Path(private_root).resolve()
    data_root = source_root / "data"
    missing = [name for name in COLLECTIONS if not (data_root / f"{name}.json").is_file()]
    if missing:
        raise FileNotFoundError("missing required workflow collections")

    private_root.mkdir(parents=True, exist_ok=True)
    snapshot_root = private_root / "local-app-snapshot"
    if snapshot_root.exists():
        raise FileExistsError("local-app-snapshot already exists; preserve it before rerunning")

    def ignored(directory, names):
        blocked = {"__pycache__", ".DS_Store", "private_data"}
        if Path(directory).resolve() == source_root and private_root.parent == source_root:
            blocked.add(private_root.name)
        return [name for name in names if name in blocked]

    shutil.copytree(source_root, snapshot_root, ignore=ignored)

    loaded = {
        name: json.loads((data_root / f"{name}.json").read_text(encoding="utf-8"))
        for name in COLLECTIONS
    }
    seed = {
        "schemaVersion": 1,
        "revision": 0,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        **loaded,
    }
    seed_path = private_root / "cloudflare-seed.json"
    write_json(seed_path, seed)

    probe_key = secrets.token_bytes(32)
    probes = []
    for value in probe_values(seed):
        probes.append({
            "characters": len(value),
            "words": len(re.findall(r"[\w@.+-]+", value, flags=re.UNICODE)),
            "digest": hmac.new(probe_key, value.encode("utf-8"), hashlib.sha256).hexdigest(),
        })

    snapshot_count, snapshot_hash = tree_digest(snapshot_root)
    counts = {
        "profile": 1,
        **{name: len(loaded[name]) for name in COLLECTIONS if name != "profile"},
    }
    collection_hashes = {
        name: sha256_bytes(canonical_bytes(loaded[name])) for name in COLLECTIONS
    }
    manifest = {
        "schemaVersion": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "collectionHashes": collection_hashes,
        "seed": {
            "bytes": seed_path.stat().st_size,
            "sha256": sha256_bytes(seed_path.read_bytes()),
        },
        "snapshot": {"files": snapshot_count, "treeSha256": snapshot_hash},
        "leakCheck": {"key": probe_key.hex(), "probes": probes},
    }
    write_json(private_root / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--private", required=True, type=Path)
    args = parser.parse_args()
    manifest = prepare(args.source, args.private)
    print("Prepared private migration bundle.")
    print("Record counts:", json.dumps(manifest["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
