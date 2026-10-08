# Independent acceptance — 2026-10-08

Reviewer: separate agent `/root/state_review`; implementation author:
`/root/runner_review`. Root persisted this review from the reviewer's report.
The reviewer inspected and tested without editing production files.

**Accepted:** final cancellation implementation, regression controls and narrow
current-guidance changes in REUSE.md, the M3-FS README, PROJECT and HANDOFF.
No remaining blocker before a monitored real gem5 launch. This acceptance
does not establish a guest hash result.

Exact accepted source SHA-256:

| File | SHA-256 |
|---|---|
| `simulator/gem5/run.py` | `e0bd968231f5d4d6a3f99d45fa630013ed9894d9b4b4f7e74917095cf4fb7a17` |
| `tests/test_gem5_fs.py` | `97b9a9a26e832d6a4d624482b191f323b2a20b837bd0e87e68e08f78f05cca4f` |

Independent commands and outcomes:

```bash
python3 -m unittest discover -s tests -p 'test_gem5*.py' -v
# 34 passed in 4.735 seconds
python3 -m unittest discover -s tests
# 253 passed in 8.416 seconds
```

The first draft had two independently reproduced signal races. SIGTERM inside
the timeout handler escaped the exception catch, and a signal at cleanup entry
could skip termination. The final exception-free record-and-kill handler
passes both deterministic injections, returns interrupted/timed-out metadata,
and restores original handlers.

Independent lifecycle checks established that the leader and a same-group
descendant ignoring SIGTERM were alive before cancellation. The direct leader
was reaped. A test-only subreaper adopted the descendant; `waitpid` reported
SIGKILL and subsequent `kill(pid, 0)` reported ESRCH. The revised committed
tests use the same namespace-correct checks and restore subreaper settings.

Production reaps its direct child and stops same-group descendants; descendants
are reaped by their adopting host init. The default wall timeout remains
disabled. Opt-in timeout behavior, strict completion, partial runtime evidence,
the tick guard and immutable input checks remain intact. Synthetic lifecycle
tests are explicitly distinct from actual gem5/Linux execution.
