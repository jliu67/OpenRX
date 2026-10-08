# Bounded gem5 CI build attempts — 2026-10-08

**Both actual hosted build attempts reached the 45-minute simulator-build
limit and exited 124. No guest boot or runtime test ran.** This is a host
build-budget result, not a Linux guest or RandomX correctness failure.
Reviewer `/root/runtime_review` independently inspected complete job logs,
downloaded both failure artifacts and verified their ZIP digests.

| Event / run | Job | Actual checkout | Terminating stage / result |
|---|---|---|---|
| [PR run 37805009018](https://github.com/jliu67/OpenRandomX/actions/runs/37805009018) | `113406877620` | PR merge `4fe386da4ad72111556635a9f618abf46998408f` | Simulator build timeout; exit 124 at `16:43:34Z` |
| [Push run 37805005108](https://github.com/jliu67/OpenRandomX/actions/runs/37805005108) | `113406864380` | `47c8caa0b9b0c34f8b96efed11819a94a099caf4` | Simulator build timeout; exit 124 at `16:43:44Z` |

Both ran the gem5 workflow at branch head
`47c8caa0b9b0c34f8b96efed11819a94a099caf4`. The PR merge also included base
`87309b203865d16076e17818b516b6399caddc6a`. These runs do not execute later
source changes. The exact workflow snapshot is retained below.

Before building, each job verified all 171 vendor files, passed seven offline
gem5 evidence-control tests and installed/recorded its build environment.
The gem5 clone was pinned to v25.1.0.1 commit
`c8222cc67a399bfc01e8658dd14b30d5bfd634f9`, with an empty prebuild source
status. Observed host compiler was GCC 13.3.0, SCons 4.5.2, and installed
guest cross GCC 14.2.0. The command was:

```bash
timeout --signal=TERM --kill-after=30s 45m \
  scons build/RISCV/gem5.opt -j2
```

The build logs show compilation progressing until interruption. PR ended
while compiling LupIO device objects; push ended while compiling AddrMap
and MemInterface objects. The shell reported exit 124 in both cases. No
completed simulator binary digest or postbuild source-diff record was
produced by the remaining build-step commands.

Guest runtime cross compilation, exact guest resource preparation and the
bounded Linux boot/runtime step were all **skipped**. The optional unchanged
light-hash build was also skipped; neither run requested that opt-in input.
Artifact preservation ran successfully despite the build failure.

| Artifact | ZIP SHA-256 | Independently verified |
|---|---|---|
| PR `11564847796`, 18,173 bytes | `40f0b6f3f8cb31cf1d2e65568637cf97928461a7c7814f810ffef20884624e2f` | Downloaded digest matches GitHub |
| Push `11564613127`, 20,149 bytes | `89399c0ee6e718812f7c99405d21571f2591e220aa7e150f1ec0c5eda2cbefb0` | Downloaded digest matches GitHub |

Each archive contains only `build.log`, `environment.txt`,
`source-commit.txt` and `source-status-before.txt` under `gem5-validation`.
Safe extraction and member inspection confirmed there is no guest execution
report or boot log. The archives expire on 2027-01-06; complete downloaded
build logs and full decoded Actions job logs are retained durably:

- [PR build log](ci-build-20261008/pr/build.log) and [job log](ci-build-20261008/pr/job.log)
- [Push build log](ci-build-20261008/push/build.log) and [job log](ci-build-20261008/push/job.log)
- [Executed workflow snapshot](ci-build-20261008/workflow-at-ci-head.yml)
- [Compact audit ledger with file digests and exact stages](CI-BUILD.json)

Next attempt needs a larger bounded cold-build budget or a separately
verified cache tied to source, compiler and build configuration before
attempting the retained guest controls. These results leave #16 and M3 open;
they establish no guest runtime compatibility, calibrated timing or power.
