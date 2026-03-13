#!/usr/bin/env python3
"""Smoke checks for Archsmith API."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def request(method: str, url: str, payload: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        parsed = json.loads(body) if body else {"detail": exc.reason}
        return exc.code, parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test Archsmith API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    checks: list[tuple[str, bool, str]] = []

    status, body = request("GET", f"{base}/health")
    checks.append(("health", status == 200 and body.get("status") == "ok", f"status={status}"))

    status, body = request("POST", f"{base}/v1/start", {"icon_set": "aws4"})
    session_id = body.get("session_id") if status == 200 else None
    checks.append(("start", status == 200 and bool(session_id), f"status={status}"))

    status, body = request(
        "POST",
        f"{base}/v1/chat",
        {
            "session_id": session_id,
            "message": "api gateway, lambda, dynamodb",
            "file_name": "api-smoke",
        },
    )
    checks.append(("chat-generate", status == 200 and body.get("validation", {}).get("ok") is True, f"status={status}"))

    status, body = request(
        "POST",
        f"{base}/v1/chat",
        {
            "session_id": session_id,
            "message": "add sqs and connect lambda -> sqs -> dynamodb",
        },
    )
    checks.append(("chat-update", status == 200 and body.get("validation", {}).get("ok") is True, f"status={status}"))

    query = urllib.parse.urlencode({"session_id": session_id})
    status, body = request("GET", f"{base}/v1/file?{query}")
    checks.append(("file", status == 200 and body.get("xml_content", "").startswith("<?xml"), f"status={status}"))

    status, body = request("GET", f"{base}/v1/session/{session_id}")
    checks.append(("session", status == 200 and body.get("session_id") == session_id, f"status={status}"))

    failed = False
    for name, ok, detail in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {name} ({detail})")
        if not ok:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
