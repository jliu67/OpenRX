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
TASK = "<!-- openrx:task:v2 -->"
MESSAGE = "<!-- openrx:message:v2 -->"
SUMMARY = "<!-- openrx:state:v1 -->"
BOT = "github-actions[bot]"
LEGACY_ROLES = ("coordinator", "research", "benchmark", "tooling", "simulation", "rtl", "review", "all")
STATUSES = ("ready", "claimed", "blocked", "review", "done", "closed", "open")
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
    """Only a fixed first-line command affects task state; prose is never executed."""
    first = (body or "").splitlines()
    first = first[0].strip() if first else ""
    if not first.startswith("/openrx "):
        return None
    words = first.split()
    if len(words) == 2 and words[1] in ("join", "block", "done", "reopen"):
        return words[1], ""
    if len(words) == 3:
        if words[1] == "route" and words[2] in LEGACY_ROLES:
            return "join", ""  # Legacy role-based routing now joins the shared pool.
        if words[1] in ("claim", "heartbeat", "release", "blocked", "review") and SESSION.fullmatch(words[2]):
            return words[1], words[2]
    raise ValueError("invalid command or agent/session identifier")


def parse_dependencies(body: str) -> tuple[list[int], list[str]]:
    """Accept explicit issue dependencies; malformed declarations fail closed."""
    sections = re.findall(r"^### Dependencies[ \t]*\n(.*?)(?=^### |\Z)", body.replace("\r\n", "\n"), re.M | re.S)
    if not sections:
        return [], []
    if len(sections) != 1:
        return [], ["Duplicate Dependencies sections."]
    refs, errors, none_seen = [], [], False
    for line in sections[0].splitlines():
        entry = line.strip()
        if not entry or (entry.startswith("<!--") and entry.endswith("-->")):
            continue
        if re.fullmatch(r"-\s*None", entry, flags=re.I):
            none_seen = True
            continue
        match = re.fullmatch(r"-\s*#([1-9][0-9]*)", entry)
        if not match:
            errors.append("Invalid dependency: use - #123 or - None.")
        else:
            refs.append(int(match.group(1)))
    if none_seen and refs:
        errors.append("None cannot be mixed with issue dependencies.")
    if len(set(refs)) != len(refs):
        errors.append("Duplicate issue dependency.")
    return sorted(set(refs)), errors


def reduce_thread(issue: dict, comments: list[dict], writers: set[str], now: dt.datetime,
                  issues_by_number: dict[int, dict] | None = None) -> dict | None:
    """Replay issue comments: only this task issue can confer an advisory claim."""
    body = issue.get("body") or ""
    trusted_body = (issue.get("user") or {}).get("login") in writers
    enrolled = trusted_body and any(m in body for m in (THREAD, TASK, MESSAGE))
    kind = "message" if MESSAGE in body or (THREAD in body and
        (issue.get("title") or "").lower().startswith("[agent message]")) else "task"
    refs, errors = parse_dependencies(body) if kind == "task" else ([], [])
    index = issues_by_number or {}
    blocked = [n for n in refs if n == issue.get("number") or n not in index or
               index[n].get("state") != "closed" or index[n].get("state_reason") != "completed"]
    state = {"protocol": 2, "kind": kind, "status": "open" if kind == "message" else "ready",
             "claim": None, "dependencies": refs, "blocked_by": blocked, "last_command_id": None,
             "warnings": errors.copy(), "audit": []}

    def expire(at: dt.datetime) -> None:
        claim = state["claim"]
        if claim and timestamp(claim["expires_at"]) <= at:
            state.update(claim=None, status="ready")

    for item in sorted(comments, key=lambda x: int(x["id"])):
        txt = item.get("body") or ""
        lines = txt.splitlines()
        if not lines or not lines[0].strip().startswith("/openrx "):
            continue
        actor, cid = (item.get("user") or {}).get("login", ""), int(item["id"])
        op, result = "invalid", "accepted"
        try:
            if actor not in writers:
                raise ValueError("author lacks repository write permission")
            if item.get("updated_at") != item.get("created_at"):
                raise ValueError("edited command ignored; append instead")
            op, arg = command(txt)
            at = timestamp(item["created_at"])
            if at > now:
                raise ValueError("future-dated command")
            expire(at)
            if op == "join":
                enrolled = True
            elif not enrolled:
                if op != "claim":
                    raise ValueError("thread not enrolled; join or claim first")
                enrolled, kind = True, "task"
                state.update(kind="task", status="ready")
            if op == "claim":
                if kind != "task":
                    raise ValueError("messages cannot be claimed")
                if errors:
                    raise ValueError("invalid dependencies")
                if blocked:
                    raise ValueError("unmet issue dependencies: " + ", ".join(f"#{n}" for n in blocked))
                if state["status"] not in ("ready", "claimed"):
                    raise ValueError("blocked/review/done task; reopen first")
                claim = state["claim"]
                if claim and (claim["actor"], claim["session"]) != (actor, arg):
                    raise ValueError("another session holds the unexpired claim")
                state.update(status="claimed", claim={"actor": actor, "session": arg, "expires_at": iso(at + LEASE)})
            elif op in ("heartbeat", "release", "blocked", "review"):
                claim = state["claim"]
                if not claim or (claim["actor"], claim["session"]) != (actor, arg):
                    raise ValueError("command requires matching active actor/session")
                if op == "heartbeat":
                    claim["expires_at"] = iso(at + LEASE)
                else:
                    state.update(claim=None, status={"release": "ready", "blocked": "blocked", "review": "review"}[op])
            elif op == "block":
                if kind != "task" or state["claim"]:
                    raise ValueError("cannot block message or claimed task")
                state["status"] = "blocked"
            elif op == "done":
                if state["status"] != "review":
                    raise ValueError("done requires review status")
                state["status"] = "done"
            elif op == "reopen":
                if kind != "task" or state["claim"]:
                    raise ValueError("cannot reopen message or active claim")
                state["status"] = "ready"
        except (ValueError, TypeError, KeyError) as exc:
            result = "rejected: " + str(exc)
        state["last_command_id"] = cid
        state["audit"].append({"comment_id": cid, "command": op, "result": result})
    if not enrolled:
        return None
    expire(now)
    if kind == "task":
        if errors:
            state["warnings"].append("Fix malformed dependencies before claiming.")
        if (blocked or errors) and state["status"] == "ready":
            state["status"] = "blocked"
        elif (blocked or errors) and state["status"] == "claimed":
            state["warnings"].append("Prerequisites now unmet; claimant should stop and coordinate.")
    if issue.get("state") == "closed":
        state.update(claim=None, status="closed")
    state["audit"] = state["audit"][-20:]
    return state


def label_catalog() -> dict[str, str]:
    return {"agent:thread": "5319e7", "agent:task": "1d76db", "agent:message": "5319e7",
            **{f"agent:status:{x}": "0e8a16" for x in STATUSES}}


def desired_labels(state: dict) -> set[str]:
    return {"agent:thread", f"agent:{state['kind']}", f"agent:status:{state['status']}"}


def render(state: dict) -> str:
    ticks = chr(96)
    deps = ", ".join(f"#{n}" for n in state["dependencies"]) or "None declared"
    blocked = ", ".join(f"#{n}" for n in state["blocked_by"]) or "None"
    return (SUMMARY + "\n## OpenRX shared coordination state\n\n"
            "Automated indexing only; not an AI reply or proof an agent is running.\n\n"
            f"**Kind:** {state['kind']} · **Status:** {state['status']}\n\n"
            f"**Dependencies:** {deps} · **Unmet:** {blocked}\n\n"
            "Claims on this task expire after four hours; read original comments and UTC expiry. "
            "The owner-designated manager may assign bounded scopes; task claims remain advisory. "
            "No autonomous model execution is provided.\n\n"
            + ticks*3 + "json\n" + json.dumps(state, indent=2, sort_keys=True)
            + "\n" + ticks*3 + "\n\n"
            "Latest 20 commands shown; history remains in issue comments. "
            "A done status is reported completion, not independent validation.")


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
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "OpenRX-agent-router-v2"}
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


def reconcile_issue(api, issue: dict, now: dt.datetime, permission_cache: dict,
                    issues_by_number: dict[int, dict] | None = None) -> bool:
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
    state = reduce_thread(issue, comments, writers, now, issues_by_number)
    if state is None:
        return False
    wanted = desired_labels(state)
    current = {x["name"] for x in issue.get("labels", [])}
    missing = sorted(wanted - current)
    if missing:
        api.request("POST", f"/issues/{number}/labels", {"labels": missing})
    # Remove only our managed status/recipient labels; never replace human labels.
    for name in sorted(current - wanted):
        if name.startswith(("agent:to:", "agent:status:")) or name in ("agent:task", "agent:message"):
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
    index = {int(item["number"]): item for item in issues if "pull_request" not in item}
    count = 0
    for issue in issues:
        count += reconcile_issue(api, issue, now, cache, index)
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
