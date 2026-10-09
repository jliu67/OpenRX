# Actual guest runtime review

Independent read-only replay by `matrix_review` at 2026-10-08T23:24:04Z accepts the completed nine-control runtime subsection of `/tmp/openrx-gem5-light-20261008-attempt2`. The overall light attempt was subsequently stopped as incomplete after its tick allowance was proven insufficient; see [REVIEW.md](REVIEW.md). No complete hash output, hypercall 3 or successful simulator exit is asserted by this review.

The actual serial contained exactly one runtime begin/end frame, guest exit status 0 and exactly one empty runtime stderr frame. The saved executing validator `tests/native_runtime_probe.py` independently accepted all nine controls with architecture `riscv64` and flush path `linux-riscv-flush-icache`. The normalized runtime JSONL SHA256 is `7dd1fdcbaa7b283a326924f15f430397c536ff02d36a853303d6dd7e65cbdeb7`.

All eight live source and executing-source snapshot bindings matched `preflight.json`, including runner SHA256 `e0bd968231f5d4d6a3f99d45fa630013ed9894d9b4b4f7e74917095cf4fb7a17`. Execution is bound to commit `9d108c4041e0fa440a676f8a3ee1a2db1d736192` (PR #25). At review, the serial was 18,215 bytes with SHA256 `287a40cdb260d0c4e24ad20085fabb5d1c48487dc9470c7f9f86bb09cadc7e52`; these values describe the reviewed prefix, since the active serial will grow.

The running simulation checkpoint recorded kernel-booted hypercall 1 at tick `379381390000` and after-boot-started hypercall 2 at tick `674367239000`. This attempt used the `10000000000000` per-simulate-call tick allowance and no wall timeout. Runtime acceptance is functional evidence and does not establish complete light hashing, a full dataset, calibrated timing or measured power.
