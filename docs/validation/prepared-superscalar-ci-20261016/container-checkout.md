# Container checkout metadata correction

At feature head `fb6843a0cc7f7361009c6b840ed7b8372fb5f248`, hosted run
`38983447478` passed the pinned package and tool identity check. Independent
inspection verified all three retained official packages, their 200 regular
payload files, five executable/alias identities, 98 Yosys support files and
37 Icarus helpers. This establishes toolchain identity only.

The run then failed at the driver's first `git rev-parse HEAD`, before native
generation, RTL simulation or synthesis: the container user and checkout owner
differ, so Git rejected the checkout. The run remains failed; no scientific
work ran, and absent fixtures are not mismatches. The
[retained log and identity export](container-checkout-fb6843/export-index.json)
bind the exact failure and distinguish unchanged raw bytes from the three
path-only substitutions in the portable independent report. The original full
toolchain archive, including its package bytes, remains retained separately.

The successor prefixes only the validation-driver process with Git's command
configuration environment: one `safe.directory` value equal to the physical
current checkout path. Its child Git commands inherit that exact-path exception.
It writes no global, system or repository configuration and uses no wildcard.
[Git documents this runtime configuration scope](https://git-scm.com/docs/git-config#Documentation/git-config.txt-GITCONFIGCOUNT).

A focused forced-owner fixture on the same Jammy Git package rejects the
unscoped and wrong-path cases, accepts the exact-path case including a Python
child, and rejects an unscoped follow-up. Configuration file hashes remain
unchanged. The forced-owner test variable is confined to that fixture and is
not used in production CI.

The scientific driver, all 178 original inputs, raw four-state gate tests,
assertions, coverage, workers and timeouts remain unchanged. Successor hosted
results remain pending until actually observed. Earlier failed runs and partial
probes retain their original status. PR #79 remains draft; do not merge.
