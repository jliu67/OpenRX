# GitHub-native agent communication

Protocol version: 1. Hub: [issue #5](https://github.com/jliu67/OpenRandomX/issues/5).
Implementation/validation task: [#6](https://github.com/jliu67/OpenRandomX/issues/6).

## What exists, and what does not

GitHub Issues and comments are the message store. Role/status labels are the inbox and board views. Pull requests carry code review. Markdown preserves durable goals, decisions and handoffs. The bounded `Agent message router` workflow reconstructs claim/routing state and maintains one bot receipt per enrolled issue. No external database, queue, model API key or service is needed for this coordination layer.

**This is not an autonomous AI worker.** It does not run models, execute instructions in messages, launch ChatGPT conversations, buy compute, assign imaginary agents, or mine cryptocurrency. An agent invoked in an authorized environment reads its inbox and responds through the same GitHub API. Nothing in a message overrides AGENTS.md, user authorization or the project's evidence gates.

## Where information belongs

| Surface | Use |
|---|---|
| Issue #5 | Cross-task announcements and links; keep open |
| Agent task/message issue | Scope, questions, claims, replies, results and handoffs |
| Issue labels | `agent:thread`, one `agent:to:ROLE`, one `agent:status:STATUS` |
| Pull request | Proposed changes and review against a recorded base commit |
| docs/TASKS.md | Durable project overview and milestone status |
| memory/STATE.md / HANDOFF.md | Current evidence-backed state and next executable steps |
| memory/DECISIONS.md / SESSION_LOG.md | Consequential decisions and append-only session history |

Do not create one giant editable chat Markdown file. Concurrent agents should append issue comments, work on separate branches when scopes overlap, and reconcile documentation through expected-head commits or reviewed PRs.

## Agent startup

Read AGENTS.md and its required project files, then issue #5 and the relevant task's latest comments. Choose a unique lowercase `agent/session` ID, for example `chatgpt/20261008-tooling-01`; the ID is a declared role/session, not a separate authenticated GitHub identity.

Search `is:issue is:open label:agent:thread label:agent:to:tooling` for a role inbox. Also inspect `label:agent:to:all` and the `review`/`blocked` queues. Add `label:agent:status:ready` to find unclaimed work. State labels are cached views, not authority over the actual thread or UTC lease expiry.

Use **New issue → Agent task** or **Agent message or handoff**. Replace the `To` field with exactly one supported role: `coordinator`, `research`, `benchmark`, `tooling`, `simulation`, `rtl`, `review`, `all`. The hidden `openrx:thread:v1` marker enrolls a writer-authored template issue. Missing, duplicate or invalid recipients are routed to coordinator with a warning. Existing issues can be enrolled without replacing their body by a writer posting `/openrx route ROLE`.

Claim a task before editing; include base SHA, files/scope, acceptance and intended work in the same comment below the first command line. Wait for a bot receipt whose claim matches your GitHub actor and session and whose expiry is still in the future. If no receipt arrives, do not assume exclusive ownership: inspect the workflow or coordinate explicitly on the thread.

## Commands

Post a new comment with the command on its first line. Put ordinary explanation, evidence and handoff text underneath. Example IDs below are examples, not running agents.

| Command | Meaning |
|---|---|
| `/openrx route tooling` | Enroll/reroute to a role inbox; does not change claim ownership |
| `/openrx claim agent/session` | Claim ready/blocked work for four hours; reject a competing live claim |
| `/openrx heartbeat agent/session` | Renew your matching unexpired claim for four hours from this comment |
| `/openrx release agent/session` | Release your matching claim; return to ready |
| `/openrx blocked agent/session` | Release your claim and mark blocked; explain dependency below |
| `/openrx review agent/session` | Release your claim and request review; link code/tests and limitations |
| `/openrx done` | Mark reported completion after review status; not independent verification |
| `/openrx reopen` | Return a non-claimed thread to ready for more work |

Control commands require the repository owner's account or a GitHub-confirmed writer/maintainer/admin. Read-only users cannot claim, release, reroute or complete work. Matching actor **and** session are required for renew/release/blocked/review. Separate agents sharing one GitHub account are not security-isolated from each other; session IDs prevent accidental confusion, not deliberate impersonation.

Only the first line is parsed, using a strict allowlist; message prose and shell/code snippets are never executed. Do not edit/delete command comments: edited commands are ignored and replay uses the current comment history. Append a correction/new command instead. Claims expire on the next reconciliation after four hours without renewal. Check `expires_at` yourself: there is no continuous timer or scheduled worker. Re-claim after expiry; a late heartbeat cannot resurrect an expired claim.

`review` and `done` block new claims until reopen. Closing an issue clears its projected claim and marks `closed`, which is distinct from successful completion. On reopening, post `/openrx reopen` before resuming. The router does not close issues, merge PRs or enforce independent review. A maintainer verifies evidence and closes completed tasks separately.

## Handoffs and message acknowledgement

A receiving agent should reply explicitly with its session ID, the original message link and what it accepts or cannot do. A bot receipt merely confirms routing/indexing; it is never a claim that the recipient read the message.

Every substantive handoff records: task/message link, session, base/result commits or PR, changed files, commands/tests actually run, failures and skipped checks, evidence class, blockers, and the next action with acceptance criteria. Release or block the editing claim before ending. Update STATE.md and HANDOFF.md, append SESSION_LOG.md, and preserve consequential decisions. Store large raw evidence as reviewed files or explicit artifact links with retention caveats.

Use fresh remote-head checks before publishing. Never force-push over another agent's work. A claim is an **advisory coordination lease**, not a Git lock, transactional reservation, or proof an agent is currently executing.

## Automation, recovery and limits

The workflow runs on issue/comment lifecycle events, relevant default-branch code pushes, or manual dispatch. It checks out trusted default-branch code at a SHA-pinned checkout action, tests the router, then uses only `contents: read` and `issues: write`. It never gives message text to a shell, writes source code, merges changes, modifies account settings or reads model secrets.

Runs share one concurrency group. Because queued runs can be superseded, **each run reconciles all issues (open and closed)** and replays full paginated command history, so a superseded close event cannot strand a stale claim. It preserves unrelated labels and updates one existing bot receipt only when state changes. Spoofed human comments containing the bot marker are not trusted. A failed permission/API read fails the run rather than silently accepting a partial history. GitHub outages, quotas and the five-minute job limit can delay processing; inspect failed runs and resync. Pagination exceeding 10,000 items fails explicitly. This is designed for the current small project, not an unbounded production queue.

Recover with **Actions → Agent message router → Run workflow**. Leave `issue_number` empty to replay all threads; a positive number optionally verifies a particular issue is included. There is no scheduled polling or model billing. GitHub-hosted Actions still count against applicable usage limits; routine event handling is not a promise of unlimited free execution.

An agent posting with the workflow's own `GITHUB_TOKEN` must not rely on its issue/comment write triggering a second workflow. Use manual/explicit dispatch from an authorized orchestration workflow, or reconcile in the current workflow; do not create recursive model-to-model reply loops. App/PAT-based writers may generate events, but no extra credential is provisioned here. If an AI worker is added later, it needs a separately authorized runtime/model configuration, budget bounds, sandboxed execution, and review gates. This version intentionally stops at persistent communication and deterministic routing.

## Validation and sources

Run `python3 -m unittest discover -s tests -p test_agent_router.py -v`. The existing foundation CI also discovers these tests. Test fixtures are synthetic coordination events, not actual agents or mining measurements. See [communication validation](validation/communication/README.md) for exact results and remote-run evidence.

Primary implementation references, checked 2026-10-08 UTC:
- [GitHub workflow triggering and token recursion behavior](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
- [Workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [Secure workflow use](https://docs.github.com/en/actions/reference/security/secure-use)
- [Repository collaborator permissions](https://docs.github.com/en/rest/collaborators/collaborators#get-repository-permissions-for-a-user)

The remote remains `jliu67/OpenRandomX`; OpenRX is the project name. Existing Phase 1 gates and benchmark evidence are unchanged.
