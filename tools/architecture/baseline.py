"""Exact scalar protocol accounting on the accepted detailed bytecode windows."""


def calibrate(trace):
    references = {(r["program"], r["iteration"]): r for r in trace["iterations"]}
    rows = []
    for window in trace["windows"]:
        ops = window["operations"]
        reference = references[(window["program"], window["iteration"])]
        reads = sum(op["memory"] is not None and not op["memory"]["write"] for op in ops)
        stores = sum(op["memory"] is not None and op["memory"]["write"] for op in ops)
        service = sum(op["latency"] for op in ops)
        # FETCH_REQ/FETCH_RSP each one ideal clock; load request/reply each
        # one clock; accepted store one clock. Measured FU service is explicit.
        expected_commit = 2 * len(ops) + service + 2 * reads + stores
        observed_commit = ops[-1]["commit_cycle"] - reference["first_cycle"]
        phases = {phase: sum(op["observed_phase_cycles"].get(phase, 0) for op in ops)
                  for phase in (1, 2, 4, 5, 6)}
        if phases != {1: len(ops), 2: len(ops), 4: reads, 5: reads, 6: stores}:
            raise ValueError("scalar ideal protocol phase counts do not match source equations")
        if observed_commit != expected_commit:
            raise ValueError("unexplained scalar bytecode timing residual")
        rows.append({"program": window["program"], "iteration": window["iteration"],
                     "instructions": len(ops), "reads": reads, "stores": stores,
                     "measured_nonmemory_service_cycles": service,
                     "source_expected_first_fetch_to_final_commit_cycles": expected_commit,
                     "observed_first_fetch_to_final_commit_cycles": observed_commit,
                     "source_return_cycles": 1,
                     "source_expected_executor_wait_cycles_including_return": expected_commit + 1,
                     "residual_cycles": observed_commit - expected_commit})
    return {"schema": "openrx.architecture.scalar-calibration.v1", "windows": rows,
            "formula": "to_final_commit = 2*instructions + measured_nonmemory_service + 2*loads + stores; executor wait includes one RETURN clock",
            "classification": "source_protocol_accounting_with_measured_operand_dependent_FU_service",
            "independent_full_hash_prediction": False, "unexplained_fitted_cycles": 0,
            "limitations": ["Eight disjoint accepted bounded windows only.",
                            "FU service spans are measured inputs; their operand-dependent latencies are not predicted.",
                            "Architectural comparison windows intentionally omit fetch and accepted RTL memory protocol overhead; they are separate changed-interface scenarios."]}
