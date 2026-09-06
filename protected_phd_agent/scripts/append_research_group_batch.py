#!/usr/bin/env python3
"""Append a private faculty batch without echoing records or credentials."""

import argparse
import getpass
import json
from pathlib import Path
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request


MAX_BATCH_BYTES = 10 * 1024 * 1024
MAX_RESPONSE_BYTES = 64 * 1024
SAFE_OUTPUT_FIELDS = (
    "revision",
    "submitted",
    "appended",
    "skipped",
    "previousFacultyTotal",
    "facultyTotal",
    "featuredTotal",
    "artifactTotal",
)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--batch", required=True, type=Path)
    parser.add_argument("--secret-file", type=Path)
    parser.add_argument("--allow-http-localhost", action="store_true")
    return parser.parse_args()


def validate_base_url(value, allow_http_localhost):
    parsed = urllib.parse.urlparse(value)
    is_local_http = (
        allow_http_localhost
        and parsed.scheme == "http"
        and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    )
    if parsed.scheme != "https" and not is_local_http:
        raise ValueError("--url must use HTTPS")
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("invalid --url")
    return value.rstrip("/")


def read_secret(secret_file):
    if secret_file is None:
        secret = getpass.getpass("Migration secret: ").strip()
    else:
        resolved = secret_file.resolve()
        info = resolved.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("secret file must be a regular file")
        if stat.S_IMODE(info.st_mode) != 0o600:
            raise ValueError("secret file permissions must be 0600")
        secret = resolved.read_text(encoding="utf-8").strip()
    if len(secret) < 32:
        raise ValueError("migration secret is too short")
    return secret


def read_batch(batch_path):
    resolved = batch_path.resolve()
    size = resolved.stat().st_size
    if size <= 0 or size > MAX_BATCH_BYTES:
        raise ValueError("batch file size is invalid")
    payload = resolved.read_bytes()
    parsed = json.loads(payload)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("faculty"), list):
        raise ValueError("batch must contain a faculty array")
    return payload


def read_bounded(response):
    payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("append response is too large")
    return payload


def append_batch(base_url, batch_payload, secret):
    request = urllib.request.Request(
        f"{base_url}/api/admin/faculty/append",
        data=batch_payload,
        method="POST",
        headers={
            "authorization": f"Bearer {secret}",
            "content-type": "application/json",
            "user-agent": "shuo-phd-agent-private-append/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(read_bounded(response))
    if not isinstance(payload, dict):
        raise ValueError("append response must be a JSON object")
    missing = [field for field in SAFE_OUTPUT_FIELDS if field not in payload]
    if missing:
        raise ValueError("append response is missing aggregate fields")
    return {field: payload[field] for field in SAFE_OUTPUT_FIELDS}


def main():
    arguments = parse_arguments()
    try:
        base_url = validate_base_url(arguments.url, arguments.allow_http_localhost)
        secret = read_secret(arguments.secret_file)
        batch = read_batch(arguments.batch)
        result = append_batch(base_url, batch, secret)
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read(MAX_RESPONSE_BYTES + 1))
            message = payload.get("error", "request rejected") if isinstance(payload, dict) else "request rejected"
        except (ValueError, json.JSONDecodeError):
            message = "request rejected"
        print(f"append failed: HTTP {error.code}: {message}", file=sys.stderr)
        return 1
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as error:
        print(f"append failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
