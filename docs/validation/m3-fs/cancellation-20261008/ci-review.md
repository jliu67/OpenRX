# Hosted CI review for PR 25

Independent review by the state_review agent, separate from the cancellation patch author. All five hosted runs passed for head `9d108c4041e0fa440a676f8a3ee1a2db1d736192`. All four uploaded artifacts passed download integrity checks and replay of their recorded outputs. The actual hosted gem5 guest job was skipped.

## Source identity

The push jobs checked out the exact head. The PR jobs checked out synthetic merge `1528112ccca6b256ff5cb5dbf4fe5ad6a527de99`, whose parents are base `50ba83166a9df0fca243af57a7c889ec752a59fc` and the reviewed head. The merge and head share tree `9dc721651244beff3475be7b6df2fbde9098f6ce`; independently fetched runner and test contents match the locally accepted bytes at both refs.

| File | Git blob | SHA256 |
| --- | --- | --- |
| simulator/gem5/run.py | `987ee06d05e7501348589a7c12acb973be29f8b1` | `e0bd968231f5d4d6a3f99d45fa630013ed9894d9b4b4f7e74917095cf4fb7a17` |
| tests/test_gem5_fs.py | `f7dabbfafca165ed5aa537df70a4d6e83cf00e7b` | `97b9a9a26e832d6a4d624482b191f323b2a20b837bd0e87e68e08f78f05cca4f` |

## Hosted jobs

All runs below are attempt 1, completed on 2026-10-08. Repository identity is `jliu67/OpenRX`, ID `1409576804`.

| Workflow | Event | Run | Job | Name | Result |
| --- | --- | --- | --- | --- | --- |
| Foundation and Phase 1 checks | PR | [37857787697](https://github.com/jliu67/OpenRX/actions/runs/37857787697) | [113586047235](https://github.com/jliu67/OpenRX/actions/runs/37857787697/job/113586047235) | correctness | success |
| Foundation and Phase 1 checks | push | [37857783755](https://github.com/jliu67/OpenRX/actions/runs/37857783755) | [113586033827](https://github.com/jliu67/OpenRX/actions/runs/37857783755/job/113586033827) | correctness | success |
| RISC-V functional preflight | PR | [37857787730](https://github.com/jliu67/OpenRX/actions/runs/37857787730) | [113586047060](https://github.com/jliu67/OpenRX/actions/runs/37857787730/job/113586047060) | scalar-correctness | success |
| RISC-V functional preflight | push | [37857783793](https://github.com/jliu67/OpenRX/actions/runs/37857783793) | [113586034103](https://github.com/jliu67/OpenRX/actions/runs/37857783793/job/113586034103) | scalar-correctness | success |
| gem5 full-system Linux functional gate | PR | [37857787784](https://github.com/jliu67/OpenRX/actions/runs/37857787784) | [113586047536](https://github.com/jliu67/OpenRX/actions/runs/37857787784/job/113586047536) | offline-controls | success |
| gem5 full-system Linux functional gate | PR | [37857787784](https://github.com/jliu67/OpenRX/actions/runs/37857787784) | [113586120254](https://github.com/jliu67/OpenRX/actions/runs/37857787784/job/113586120254) | atomic-linux-runtime | skipped |

Each foundation job passed 253 Python tests, 107 upstream tests and six native steady tests, and verified all 171 pinned vendor files. The pinned profile, both algorithm smoke runs and v1/v2 full-dataset 1000-nonce reference controls also passed.

Each RISC-V job passed 39 required hash and semantic checks and nine runtime checks in both native and QEMU environments. Each hash probe reported one optional hardware-AES skip; all required checks passed. QEMU used scalar `rv64,v=false` and the explicit Linux RISC-V instruction-cache flush path. The scalar main compile flags include `-march=rv64gc -mabi=lp64d -frounding-math -fno-fast-math -ffp-contract=off`.

The gem5 offline job passed 34 tests in 4.664 seconds, including real host SIGINT/SIGTERM, timeout and transition-race cancellation, handler restoration, direct-child reaping and adopted-descendant SIGKILL checks. These tests use synthetic simulators and namespace-correct host process assertions. Job `113586120254` (`atomic-linux-runtime`) was skipped because the workflow condition requires a `workflow_dispatch` event. These hosted runs did not build or execute gem5.

## Artifact replay

All archives matched the SHA256 and byte length recorded by GitHub, passed ZIP CRC validation and contained unique safe relative members. The foundation archives each contain 36 members; the RISC-V archives each contain 26. Each artifact expires on 2027-01-06.

| Artifact | ID | Bytes | SHA256 |
| --- | --- | --- | --- |
| PR correctness-logs | 11584129552 | 69510 | `5e732dd1e3c599d37c01c9e74be48441b22c2b5838fc643eef3c73d38185ff7c` |
| push correctness-logs | 11584548717 | 69500 | `97914efc12c8d692be5971a19a3aa392744a0c84303ae320b7a7bacd58ee32f3` |
| PR riscv-functional-preflight | 11584598469 | 462343 | `de061f9c2bf8f146a5ce87dec9f19247e1f5de252aa78f9df98d8ef94a4fe8db` |
| push riscv-functional-preflight | 11584553495 | 462339 | `4fb9d6958799a90f52bc37910a7abf5add53038cc232a8f9ac5963d5da20020e` |

Replay used the trusted project validators without executing downloaded workload binaries. In each foundation archive, it reproduced the pinned profile, both v1/v2 reference results, four steady streams comprising 36 intervals and eight controls, four intentional duration rejections, 16 invalid-option rejections and two upstream differential matches. Adapter raw output and source SHA256 bindings, return codes, stderr and summaries matched. The expected duration rejection is an exercised gate, not a failed test.

All eight native/QEMU streams across the two RISC-V archives reproduced the exact recorded validation objects. Uploaded RISC-V ELF headers and hashes matched their reports. The runtime ELF SHA256 is `8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac`. The newly hosted hash ELF SHA256 is `0e310b9c39a24685cc10d907e6db7056b8bff3e4bb43ddf23e524acd593367fc`; it differs from the retained `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657` hash ELF used as a separate local guest input. Each run must retain its own digest binding. Native ELF bytes are absent from these archives, so their binaries were not independently rehashed.

The separately monitored local gem5 light-mode guest run is outside this review. These hosted checks establish functional controls; they do not establish calibrated RISC-V hardware timing, BOOM validation, power, hashes/J or full-dataset gem5 acceptance.

## Preserved evidence

[ci-review.json](ci-review.json) records source identities, run and job metadata, step conclusions, artifact identities, detailed replay outcomes, skips and limits. Raw decoded GitHub job logs are preserved byte-for-byte, including the initial UTF-8 BOM:

| Log | Bytes | SHA256 |
| --- | --- | --- |
| [offline-pr-job-113586047536.log](offline-pr-job-113586047536.log) | 18375 | `aefab11174d5cba8e7d21d6972dcc0aac5d792055aeba466a133c93754d48988` |
| [riscv-pr-job-113586047060.log](riscv-pr-job-113586047060.log) | 56801 | `dbf8cd1ae3f9282259560b6edea26f97dfd11d5d4bd5c4575232ec987e5051f0` |
| [riscv-push-job-113586034103.log](riscv-push-job-113586034103.log) | 55902 | `6c67aaecd52b0d71ae58714b3c3fa5ad31ddb3a4b2e122534cb16a61379c8dab` |
| [foundation-pr-job-113586047235.log](foundation-pr-job-113586047235.log) | 72470 | `ae36b9b861d4917aa6956d757199a0117e0c7a46778942ed9346ac2f34cf77c1` |
| [foundation-push-job-113586033827.log](foundation-push-job-113586033827.log) | 71571 | `d6e8ae8961eac91bd7fa488f44ef8d5cf3462e81f5b235d4a0f4605c9d6916f4` |
