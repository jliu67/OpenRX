# Progress publication and retained local sources

Owner direction recorded in [task #31](https://github.com/jliu67/OpenRX/issues/31): GitHub is the sole place where project progress is published and coordinated. There is no standing editable local progress mirror and no automatic Git synchronization. This policy does not claim zero local source copies.

## Publication and authoring

Publish progress, decisions, evidence indices and handoffs through the existing GitHub task issues, repository documentation and reviewed feature PRs. Existing claims, dependency gates, independent review and hub announcements remain authoritative procedures; no coordination architecture is replaced.

Prefer connected GitHub tools/API or bounded temporary authoring. A temporary editing checkout may be created only when separately needed and authorized, on a dedicated feature branch, and retired after its reviewed work is handed off. Do not create a permanent replacement mirror merely to update documentation. Do not auto-commit unfinished files, force-push, push directly to protected main, or merge without the applicable authorization and reviews.

## Retained local reproducibility assets

Keep the original evidence-bound checkout and shared Git metadata, pinned execution source snapshots, installed immutable runner releases, simulator source/builds/binaries, toolchains, guest resources, disks, scientific data, results, caches, checkpoints, logs, configuration, request mappings and acceptance receipts. These sources/assets support reproducibility and local computation; they are not progress publication workspaces.

The designated standing editable authoring worktree is the cleanup target, not the original preservation source or execution inputs. Recoverable system Trash is permitted only after current dependency and preservation checks; preserve linked-worktree metadata required for restoration and other execution worktrees. Never prune, reset, rewrite or move evidence-bound originals to make cleanup appear complete. The local pointer/cleanup receipt states actual retained and retired paths; do not assume a historical authoring path is still active.

## Cancelled synchronization and runtime behavior

The owner cancelled the ten-minute Git sync setup. Its timer and service are disabled/inactive; no scheduled pushes or unattended working-tree updates are authorized. Retain its bounded implementation/review/status evidence as historical records, without re-enabling it. Any later sync request needs fresh explicit authorization.

The accepted local migration remains LOCAL_ACTIVE under its existing explicit release. This publication policy does not change the scientific acceptance criteria, one-payload resource gate, pinned runtime/source bindings, stop/recovery behavior or remote-execution availability. No scientific run is authorized by publishing progress. Full-scale research and #16/M1–M5 remain separate gates; do not treat retained source copies, a task claim, or this policy as scientific acceptance.
