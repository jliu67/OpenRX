#!/usr/bin/env python3
"""Repost explicitly requested hub announcements using the GitHub Actions bot.

Read a GitHub issue_comment event as *data*. Never execute comment contents.
Only /openrx announce, on hub #5, from the repository owner is authorized.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

HUB = 5
PREFIX = "/openrx announce"
MARKER = "<!-- openrx:announcement-source:"
BOT = "github-actions[bot]"
MAX_CHARS = 1200


def announcement(event: dict) -> tuple[int, str, str] | None:
    if event.get("action") != "created":
        return None
    repo = event.get("repository") or {}
    issue = event.get("issue") or {}
    comment = event.get("comment") or {}
    if issue.get("number") != HUB or "pull_request" in issue:
        return None
    owner = (repo.get("owner") or {}).get("login")
    actor = (comment.get("user") or {}).get("login")
    if not owner or actor != owner or actor == BOT:
        return None
    body = comment.get("body") or ""
    lines = body.splitlines()
    if not lines or lines[0].strip() != PREFIX:
        return None
    msg = "\n".join(lines[1:]).strip()
    if not msg or len(msg) > MAX_CHARS:
        raise ValueError("announcement must contain 1–1200 characters after command")
    cid = comment.get("id")
    if type(cid) is not int or cid <= 0:
        raise ValueError("invalid source comment ID")
    source = comment.get("html_url") or ""
    if not source.startswith("https://github.com/"):
        raise ValueError("invalid source URL")
    return cid, source, msg


def api_request(url: str, token: str, method="GET", data=None):
    payload = json.dumps(data).encode() if data is not None else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "OpenRX-announcements-v1",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as res:
        raw = res.read()
    return json.loads(raw) if raw else None


def publish(event: dict, token: str, request=api_request) -> str:
    parsed = announcement(event)
    if parsed is None:
        return "ignored"
    cid, source, msg = parsed
    repo = (event.get("repository") or {}).get("full_name")
    if not repo or repo.count("/") != 1 or not token:
        raise ValueError("repository and token are required")
    marker = f"{MARKER}{cid} -->"
    base = f"https://api.github.com/repos/{repo}/issues/{HUB}/comments"
    # Check all history pages; repeated jobs should not duplicate a bot announcement.
    page = 1
    while page <= 100:
        items = request(f"{base}?per_page=100&page={page}", token)
        if not isinstance(items, list):
            raise ValueError("unexpected comment list")
        for item in items:
            if (item.get("user") or {}).get("login") == BOT and marker in (item.get("body") or ""):
                return "already-posted"
        if len(items) < 100:
            break
        page += 1
    else:
        raise RuntimeError("comment pagination limit; refusing duplicate-risk posting")
    post = f"📌 **OpenRX agent update**\n\n{msg}\n\n{marker}\n[Original request]({source})"
    result = request(base, token, "POST", {"body": post})
    if not isinstance(result, dict) or not result.get("id"):
        raise RuntimeError("GitHub did not confirm comment creation")
    return "posted"


def main() -> int:
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        print(publish(event, os.environ.get("GH_TOKEN", "")))
        return 0
    except (KeyError, OSError, ValueError, RuntimeError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        print(f"announcement failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
