#!/usr/bin/env python3
"""Verify local or remote private workflow data without printing records."""

import argparse
from getpass import getpass
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

try:
    from .prepare_private_migration import COLLECTIONS, canonical_bytes
except ImportError:
    from prepare_private_migration import COLLECTIONS, canonical_bytes


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def record_counts(seed):
    return {
        "profile": 1,
        **{name: len(seed[name]) for name in COLLECTIONS if name != "profile"},
    }


def collection_hashes(seed):
    return {name: sha256_bytes(canonical_bytes(seed[name])) for name in COLLECTIONS}


def normalize_json_numbers(value):
    if isinstance(value, dict):
        return {key: normalize_json_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_json_numbers(item) for item in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def semantic_collection_hashes(seed):
    return {
        name: sha256_bytes(canonical_bytes(normalize_json_numbers(seed[name])))
        for name in COLLECTIONS
    }


def remote_opener(cookie_jar):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    opener.addheaders = [("User-agent", "Shuo-PhD-Agent-Verifier/1.0")]
    return opener


def verify_seed(seed_path, manifest_path):
    seed_path = Path(seed_path)
    manifest_path = Path(manifest_path)
    seed_bytes = seed_path.read_bytes()
    seed = json.loads(seed_bytes)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if seed.get("schemaVersion") != 1 or manifest.get("schemaVersion") != 1:
        raise RuntimeError("schema version mismatch")
    if sha256_bytes(seed_bytes) != manifest["seed"]["sha256"]:
        raise RuntimeError("seed hash mismatch")
    if len(seed_bytes) != manifest["seed"]["bytes"]:
        raise RuntimeError("seed size mismatch")
    if record_counts(seed) != manifest["counts"]:
        raise RuntimeError("record count mismatch")
    if collection_hashes(seed) != manifest["collectionHashes"]:
        raise RuntimeError("collection hash mismatch")


def verify_remote(remote, seed_path, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    seed = json.loads(Path(seed_path).read_text(encoding="utf-8"))
    base = remote.rstrip("/")
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("remote verification requires HTTPS")
    password = os.environ.get("PHD_AGENT_VERIFY_PASSWORD") or getpass("Workflow password: ")
    cookie_jar = http.cookiejar.CookieJar()
    opener = remote_opener(cookie_jar)
    login_request = urllib.request.Request(
        f"{base}/api/login",
        data=json.dumps({"password": password}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener.open(login_request, timeout=20) as response:
            if response.status != 200:
                raise RuntimeError("remote login failed")
        with opener.open(f"{base}/api/bootstrap", timeout=30) as response:
            remote_state = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"remote verification failed with HTTP {error.code}") from None
    finally:
        password = ""

    if record_counts(remote_state) != manifest["counts"]:
        raise RuntimeError("remote record count mismatch")
    if semantic_collection_hashes(remote_state) != semantic_collection_hashes(seed):
        raise RuntimeError("remote collection hash mismatch")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--remote")
    args = parser.parse_args()
    verify_seed(args.seed, args.manifest)
    if args.remote:
        verify_remote(args.remote, args.seed, args.manifest)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    print("Private migration verification passed.")
    print("Record counts:", json.dumps(manifest["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
