# Preserved recovery and finite validation sequence

These are exact host-script/spec exports with the sole literal root-prefix redaction recorded in `export-index.json`. They are review evidence; the literal placeholder is not automatically expanded by Python and the host originals retain their separate hashes.

Attempt03 builds one worker in a separate full copy of the preserved failed partial tree, retaining the pinned scientific configuration. This is incremental compilation, not simulator checkpoint resume. Normal experiment budget remains6GiB/1GiBswap/200%; the reviewed migration-build recovery exception is8GiB/2GiBswap/100%.

The v2 sequence is independently reviewed and host-managed. It waits without a wall cutoff, verifies successful build/source/config/toolchain/guest/actual pinned loader closure and durable assets, binds `LOCAL_VALIDATING` in both journals, then submits only the fixed nine-control runtime request. It captures output integrity without independently declaring scientific acceptance or activation. See [pipeline review](../pipeline-independent-review-v2.json) and [runner durability review](../runner-durability-independent-review.json). The running sequence must not be edited. Failed v1 remains in [preserved failure evidence](../build-failure-02/README.md).
