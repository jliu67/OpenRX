#!/usr/bin/env python3
"""GitHub-only, deterministic agent coordination. No model or shell execution.

Run in the trusted-default-branch workflow, not against arbitrary PR code.
Comments remain the source of truth; labels and one bot comment are projections.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

THREAD = "<!-- openrx:thread:v1 -->"
SUMMARY = "<!-- openrx:state:v1 -->"
BOT = "github-actions[bot]"
ROLES = ("coordinator", "research", "benchmark", "tooling", "simulation", "rtl", "review", "all")
STATUSES = ("ready", "claimed", "blocked", "review", "done", "closed")
LEASE = dt.timedelta(hours=4)
SESSION = re.compile(r"[a-z0-9][a-z0-9._-]{0,39}/[a-z0-9][a-z0-9._-]{0,63}\Z")
UTC = dt.timezone.utc


def timestamp(value: str) -> dt.datetime:
    result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return result.astimezone(UTC)


def iso(value: dt.datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def command(body: str) -> tuple[str, str] | None:
    """Only a literal first-line command is executable protocol (never code)."""
    lines = (body or "").splitlines()
    first = lines[0].strip() if lines else ""
    if not first.startswith("/openrx "):
        return None
    words = first.split()
    op = words[1] if len(words) > 1 else ""
    if op in ("done", "reopen") and len(words) == 2:
        return op, ""
    if len(words) == 3:
        if op == "route" and words[2] in ROLES:
            return op, words[2]
        if op in ("claim", "heartbeat", "release", "blocked", "review") and SESSION.fullmatch(words[2]):
            return op, words[2]
    raise ValueError("invalid command, role, or agent/session identifier")


def initial_role(body: str) -> tuple[str, list[str]]:
    sections = re.findall(r"^### To\s*\n(.*?)(?=^### |\Z)", body.replace("\r\n", "\n"), re.M | re.S)
    if len(sections) == 1 and sections[0].strip() in ROLES:
        return sections[0].strip(), []
    return "coordinator", ["Missing/invalid/duplicate To section; coordinator triage required."]


def reduce_thread(issue: dict, comments: list[dict], writers: set[str], now: dt.datetime) -> dict | None:
    """Replay current immutable command comments in GitHub comment-ID order.

    Claims are advisory leases, not distributed filesystem locks or proof of work.
    Edited commands are ignored. Do not edit/delete command history.
    """
    body = issue.get("body") or ""
    trusted_body = issue.get("user", {}).get("login") in writers
    enrolled = THREAD in body and trusted_body
    role, warnings = initial_role(body) if enrolled else ("coordinator", [])
    state = {"protocol": 1, "role": role, "status": "ready", "claim": None,
             "last_command_id": None, "warnings": warnings, "audit": []}

    def expire(at: dt.datetime) -> None:
        claim = state["claim"]
        if claim and timestamp(claim["expires_at"]) <= at:
            state.update(claim=None, status="ready")

    for comment in sorted(comments, key=lambda item: int(item["id"])):
        text = comment.get("body") or ""
        first = text.splitlines()[0].strip() if text.splitlines() else ""
        if not first.startswith("/openrx "):
            continue
        actor = comment.get("user", {}).get("login", "")
        cid = int(comment["id"])
        result = "accepted"
        op = "invalid"
        try:
            if actor not in writers:
                raise ValueError("author lacks repository write permission")
            if comment.get("updated_at") != comment.get("created_at"):
                raise ValueError("edited command ignored; append a new comment instead")
            op, arg = command(text)
            at = timestamp(comment["created_at"])
            if at > now:
                raise ValueError("future-dated command")
            expire(at)
            if op == "route":
                enrolled = True
                state["role"] = arg
            elif not enrolled:
                raise ValueError("thread not enrolled; route it first")
            elif op == "claim":
                if state["status"] not in ("ready", "blocked", "claimed"):
                    raise ValueError("thread needs review/reopen before claiming")
                claim = state["claim"]
                if claim and (claim["actor"], claim["session"]) != (actor, arg):
                    raise ValueError("another session holds the unexpired claim")
                state.update(status="claimed", claim={"actor": actor, "session": arg, "expires_at": iso(at + LEASE)})
            elif op in ("heartbeat", "release", "blocked", "review"):
                claim = state["claim"]
                if not claim or (claim["actor"], claim["session"]) != (actor, arg):
                    raise ValueError("command requires the matching active actor/session")
                if op == "heartbeat":
                    claim["expires_at"] = iso(at + LEASE)
                else:
                    state.update(claim=None, status={"release": "ready", "blocked": "blocked", "review": "review"}[op])
            elif op == "done":
                if state["status"] != "review":
                    raise ValueError("done requires review status; it is not a test result")
                state["status"] = "done"
            elif op == "reopen":
                if state["claim"]:
                    raise ValueError("cannot reopen over an active claim")
                state["status"] = "ready"
        except (ValueError, TypeError, KeyError) as exc:
            result = "rejected: " + str(exc)
        state["last_command_id"] = cid
        state["audit"].append({"comment_id": cid, "command": op, "result": result})
    if not enrolled:
        return None
    expire(now)
    if issue.get("state") == "closed":
        state.update(claim=None, status="closed")
    state["audit"] = state["audit"][-20:]
    return state


def label_catalog() -> dict[str, str]:
    return {"agent:thread": "5319e7", **{f"agent:to:{x}": "1d76db" for x in ROLES},
            **{f"agent:status:{x}": "0e8a16" for x in STATUSES}}


def desired_labels(state: dict) -> set[str]:
    return {"agent:thread", f"agent:to:{state['role']}", f"agent:status:{state['status']}"}


def render(state: dict) -> str:
    return (SUMMARY + "\n## Agent coordination state\n\n"
            "This is a routing receipt, **not an AI response or proof an agent is running**.\n\n"
            f"**To:** `{state['role']}` · **Status:** `{state['status']}`\n\n"
            "Claims expire after four hours without a heartbeat. Reconciliation is event/manual driven; "
            "check the UTC expiry before work even if the label is stale. Read the full thread, "
            "AGENTS.md and docs/COMMUNICATION.md before acting.\n\n"
            "```json\n" + json.dumps(state, indent=2, sort_keys=True) + "\n```\n\n"
            "Audit above shows the last 20 protocol comments; original comments retain the full history. "
            "Append corrections rather than editing commands. `done` is reported completion, not independent verification.")


class APIError(RuntimeError):
    def __init__(self, status: int, path: str):
        self.status = status
        super().__init__(f"GitHub HTTP {status} for {path.split('?')[0]}")


class GitHubAPI:
    def __init__(self, repo: str, token: str):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or not token:
            raise ValueError("valid GITHUB_REPOSITORY and GH_TOKEN are required")
        self.repo, self.token = repo, token

    def request(self, method: str, path: str, data=None):
        if not path.startswith("/") or ".." in path or "\n" in path:
            raise ValueError("invalid API path")
        url = f"https://api.github.com/repos/{self.repo}{path}"
        payload = None if data is None else json.dumps(data).encode()
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "OpenRX-agent-router-v1"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, payload, headers, method=method)
                with urllib.request.urlopen(req, timeout=25) as response:
                    raw = response.read()
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as exc:
                # Never retry POST blindly: ambiguous success could duplicate a message.
                if method == "GET" and exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise APIError(exc.code, path) from None

    def pages(self, path: str) -> list[dict]:
        result = []
        sep = "&" if "?" in path else "?"
        for page in range(1, 101):
            batch = self.request("GET", f"{path}{sep}per_page=100&page={page}")
            if not isinstance(batch, list):
                raise ValueError("expected a paginated GitHub list")
            result.extend(batch)
            if len(batch) < 100:
                return result
        raise RuntimeError("pagination limit exceeded; no partial history is accepted")

    def can_write(self, login: str) -> bool:
        if login == self.repo.split("/")[0]:
            return True
        try:
            data = self.request("GET", "/collaborators/" + urllib.parse.quote(login, safe="") + "/permission")
            return data.get("permission") in ("admin", "maintain", "write")
        except APIError as exc:
            if exc.status == 404:
                return False
            raise  # Authentication/rate-limit failures must not silently rewrite history.


def sync_labels(api) -> None:
    existing = {item["name"] for item in api.pages("/labels")}
    for name, color in label_catalog().items():
        if name not in existing:
            try:
                api.request("POST", "/labels", {"name": name, "color": color, "description": "OpenRX agent coordination"})
            except APIError as exc:
                if exc.status != 422:
                    raise
                api.request("GET", "/labels/" + urllib.parse.quote(name, safe=""))


def reconcile_issue(api, issue: dict, now: dt.datetime, permission_cache: dict) -> bool:
    if "pull_request" in issue:
        return False
    number = int(issue["number"])
    comments = api.pages(f"/issues/{number}/comments") if issue.get("comments", 0) else []
    actors = {issue.get("user", {}).get("login", "")}
    for item in comments:
        body = item.get("body") or ""
        if body.splitlines() and body.splitlines()[0].strip().startswith("/openrx "):
            actors.add(item.get("user", {}).get("login", ""))
    for actor in actors:
        if actor and actor not in permission_cache:
            permission_cache[actor] = api.can_write(actor)
    writers = {actor for actor in actors if permission_cache.get(actor, False)}
    state = reduce_thread(issue, comments, writers, now)
    if state is None:
        return False
    wanted = desired_labels(state)
    current = {x["name"] for x in issue.get("labels", [])}
    missing = sorted(wanted - current)
    if missing:
        api.request("POST", f"/issues/{number}/labels", {"labels": missing})
    # Remove only our managed status/recipient labels; never replace human labels.
    for name in sorted(current - wanted):
        if name.startswith(("agent:to:", "agent:status:")):
            try:
                api.request("DELETE", f"/issues/{number}/labels/" + urllib.parse.quote(name, safe=""))
            except APIError as exc:
                if exc.status != 404:
                    raise
    text = render(state)
    summaries = [x for x in comments if x.get("user", {}).get("login") == BOT
                 and (x.get("body") or "").startswith(SUMMARY)]
    if summaries:
        latest = max(summaries, key=lambda item: int(item["id"]))
        if latest["body"] != text:
            api.request("PATCH", f"/issues/comments/{int(latest['id'])}", {"body": text})
    else:
        api.request("POST", f"/issues/{number}/comments", {"body": text})
    return True


def run(api, event: dict, now: dt.datetime) -> int:
    """Full reconciliation prevents dropped pending Actions runs losing messages."""
    selected = event.get("issue", {}).get("number") or event.get("inputs", {}).get("issue_number")
    if selected and (not str(selected).isdigit() or int(selected) <= 0):
        raise ValueError("issue_number must be a positive integer")
    sync_labels(api)
    issues = api.pages("/issues?state=all")
    if selected:
        if int(selected) not in {int(x["number"]) for x in issues}:
            issues.append(api.request("GET", f"/issues/{int(selected)}"))
    cache = {}
    count = 0
    for issue in issues:
        count += reconcile_issue(api, issue, now, cache)
    return count


def main() -> int:
    try:
        api = GitHubAPI(os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GH_TOKEN", ""))
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        count = run(api, event, dt.datetime.now(UTC))
        print(f"Reconciled {count} agent threads. No AI workers were invoked.")
        return 0
    except (APIError, ValueError, KeyError, OSError, RuntimeError) as exc:
        print(f"Agent router failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
