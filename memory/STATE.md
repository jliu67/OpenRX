# Current state

Stage: M0 repository foundation / M1 workload baseline.

## Completed
- RandomX v2.0.1 downloaded from official upstream at aaafe71322df6602c21a5c72937ac284724ae561.
- Source inspected: benchmark defaults to v1; `--v2` selects v2; tests contain v1/v2 interpreter and JIT cases.
- Vendored source, integrity manifest, build/test scripts, benchmark runner and CI authored.
- Persistent memory, evidence rules, issue templates and initial experiment authored.

## Pending validation
- Remote CI has not run. Local validation passed: 107 upstream tests, zero skips; v1/v2 smoke and full-dataset reference hashes passed. See docs/VALIDATION.md.
- GitHub repository creation completed through authorized browser fallback; connected account jliu67. Private repository https://github.com/jliu67/OpenRandomX created and verified; foundation upload in progress.

## Next actions
1. Local baseline tooling validation complete; retain logs in docs/validation/foundation/.
2. Complete foundation upload, inspect branch contents and CI in jliu67/OpenRandomX.
3. Reproduce full-dataset benchmarks on a known local CPU with wall-power measurements.
4. Verify X5 board evidence and SG2042 ISA/cache details from primary sources.
5. Evaluate simulator/core feasibility before selecting RTL.
