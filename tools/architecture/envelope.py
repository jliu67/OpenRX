"""Necessary resource and energy conditions, never demonstrated ASIC performance.

Adapted from the preserved scratchpad-handoff-20261016/bounds.py. All byte
counts are algorithmic or explicitly named placement scenarios; no cache hit
rate, physical frequency, SRAM macro or memory technology is inferred.
"""
import math

SCRATCHPAD_BYTES = 2 * 1024**2
TARGET_HPS = 1_000_000
WALL_LIMIT_W = 2500
ENERGY_TERMS = (
    "compute", "scratchpad_dynamic", "dataset_dynamic", "controllers_phy",
    "fabric_clock", "input_hash_fill_program_dataset_generation",
)
STATIC_TERMS = ("logic_leakage", "sram_leakage", "memory_refresh_static", "vrm_losses", "fans", "auxiliary_dc")


def nonnegative(value, name="value"):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return value


def positive(value, name="value"):
    if nonnegative(value, name) == 0:
        raise ValueError(f"{name} must be positive")
    return value


def integer(value, name="value", minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def capacity(contexts, hot_bytes):
    integer(contexts, "contexts")
    integer(hot_bytes, "hot_bytes", 0)
    if hot_bytes > SCRATCHPAD_BYTES or hot_bytes % 64:
        raise ValueError("hot prefix must be a 64-byte multiple within the 2 MiB image")
    return {
        "logical_state_bytes": contexts * SCRATCHPAD_BYTES,
        "on_chip_image_bytes": contexts * hot_bytes,
        "external_backing_bytes": contexts * (SCRATCHPAD_BYTES - hot_bytes),
        "metadata_ecc_queues_registers_program_bytes": None,
        "shared_pool_saves_active_image_bits": False,
    }


def external_prefix(cold, hot_bytes, granule_bytes=64, store_rmw=False):
    """No combining/reuse/cache; masked transfers or explicit partial-store RMW.

    Fill and final scan are cold-range transfers. These source-derived bytes
    do not include the unknown work to *generate* the initial fill.
    """
    capacity(1, hot_bytes)
    if granule_bytes not in (8, 16, 32, 64):
        raise ValueError("granule must be 8/16/32/64 bytes")
    if type(store_rmw) is not bool:
        raise ValueError("store_rmw must be boolean")
    for key in ("bytecode_read8", "bytecode_write8", "outer_read64", "outer_write64"):
        integer(cold[key], key, 0)
    reads, writes = cold["bytecode_read8"], cold["bytecode_write8"]
    outer = cold["outer_read64"] + cold["outer_write64"]
    stream_bytes = 2 * (SCRATCHPAD_BYTES - hot_bytes)
    transactions = reads + writes + outer * (64 // granule_bytes) + stream_bytes // granule_bytes
    wire = (reads + writes) * granule_bytes + 64 * outer + stream_bytes
    if store_rmw:
        transactions += writes
        wire += granule_bytes * writes
    return {
        "algorithmic_cold_bytes_per_hash": 8 * (reads + writes) + 64 * outer + stream_bytes,
        "external_transfer_bytes_per_hash": wire,
        "external_transactions_per_hash": transactions,
        "cold_execution_reads_per_hash": reads + cold["outer_read64"],
        "granule_bytes": granule_bytes,
        "partial_store_read_modify_write": store_rmw,
        "cache_or_combining_model": "none",
    }


def port_operations(counts, width_bytes):
    if width_bytes not in (8, 16, 32, 64):
        raise ValueError("port width must divide a 64-byte line")
    return (counts["bytecode_read8"] + counts["bytecode_write8"]
            + (counts["outer_read64"] + counts["outer_write64"]) * (64 // width_bytes)
            + 2 * SCRATCHPAD_BYTES // width_bytes)


def latency_requirement(hps, requests_per_hash, service_latency_s, ready_per_context):
    positive(hps, "hps")
    integer(requests_per_hash, "requests_per_hash", 0)
    positive(service_latency_s, "service_latency_s")
    integer(ready_per_context, "ready_per_context")
    outstanding = math.ceil(hps * requests_per_hash * service_latency_s)
    return {"necessary_outstanding_requests": outstanding,
            "necessary_contexts_if_ready_limit_is_valid": math.ceil(outstanding / ready_per_context),
            "ready_per_context": ready_per_context,
            "scope": "Little's law necessary average bound; excludes scan, dataset and latency tails"}


def full_wall_power(hps, dynamic_j_per_hash, static_dc_w, psu_efficiency, ac_auxiliary_w):
    """A complete conditional input set is required. Missing means unknown.

    controllers_phy is exclusive of memory figures: callers must avoid double
    counting PHY energy. vrm_losses covers regulator conversion losses at the
    requested operating point. PSU loss is applied once to the DC subtotal.
    """
    positive(hps, "hps")
    if set(dynamic_j_per_hash) - set(ENERGY_TERMS) or set(static_dc_w) - set(STATIC_TERMS):
        raise ValueError("unexpected energy/power term; use the explicit complete accounting schema")
    missing = ["dynamic." + k for k in ENERGY_TERMS if dynamic_j_per_hash.get(k) is None]
    missing += ["static." + k for k in STATIC_TERMS if static_dc_w.get(k) is None]
    if psu_efficiency is None:
        missing.append("psu_efficiency")
    elif not 0 < positive(psu_efficiency, "psu_efficiency") <= 1:
        raise ValueError("PSU efficiency must be <= 1")
    if ac_auxiliary_w is None:
        missing.append("ac_auxiliary_w")
    else:
        nonnegative(ac_auxiliary_w)
    for value in list(dynamic_j_per_hash.values()) + list(static_dc_w.values()):
        if value is not None:
            nonnegative(value, "energy/power term")
    if missing:
        return {"wall_power_w": None, "wall_j_per_hash": None,
                "status": "unresolved", "missing": missing}
    dc = hps * sum(dynamic_j_per_hash[k] for k in ENERGY_TERMS) + sum(static_dc_w[k] for k in STATIC_TERMS)
    wall = dc / psu_efficiency + ac_auxiliary_w
    return {"wall_power_w": wall, "wall_j_per_hash": wall / hps,
            "dc_power_w": dc, "status": "conditional_under_limit" if wall < WALL_LIMIT_W else "rejected",
            "missing": [], "input_classification": "assumed_unless_independently_characterized"}


def rejection_gate(hps=None, wall_w=None, required_bandwidth=None, available_bandwidth=None,
                   required_capacity=None, available_capacity=None, required_outstanding=None,
                   supported_outstanding=None, correctness=None):
    reasons, unknown = [], []
    if correctness is not None and type(correctness) is not bool:
        raise ValueError("correctness must be boolean or unknown")
    if correctness is False:
        reasons.append("correctness_or_ordering_failure")
    elif correctness is None:
        unknown.append("correctness_for_proposed_hardware")
    if hps is None:
        unknown.append("complete_path_throughput")
    elif nonnegative(hps) < TARGET_HPS:
        reasons.append("throughput_below_1MHps")
    if wall_w is None:
        unknown.append("whole_machine_wall_power")
    elif nonnegative(wall_w) >= WALL_LIMIT_W:
        reasons.append("wall_power_not_below_2500W")
    for name, demand, supply in (
        ("sustainable_bandwidth", required_bandwidth, available_bandwidth),
        ("live_state_capacity", required_capacity, available_capacity),
        ("independent_outstanding_requests", required_outstanding, supported_outstanding),
    ):
        if demand is None or supply is None:
            unknown.append(name)
        elif nonnegative(demand) > nonnegative(supply):
            reasons.append(name + "_exceeded")
    return {"status": "rejected" if reasons else "unresolved" if unknown else "conditional_inputs_pass",
            "rejections": reasons, "unknown": unknown, "demonstrated_asic_feasibility": False}


def sensitivity(evidence, target_hps=TARGET_HPS):
    """Small factorized sweeps; no multiplied headline from unrelated minima."""
    positive(target_hps)
    counts = evidence["counts"]
    prefixes = evidence["prefixes"]
    dataset_bytes = evidence.get("dataset_bytes_per_hash", 16384 * 64)
    capacity_rows, placement_rows, latency_rows = [], [], []
    for row in prefixes:
        hot = row["hot_prefix_bytes"]
        cold = row["cold_counts"]
        for contexts in (1, 2, 4, 8, 16, 64, 256, 1024, 4096, 16384):
            capacity_rows.append(dict(contexts=contexts, hot_prefix_bytes=hot,
                                      residence_budget_s=contexts / target_hps, **capacity(contexts, hot)))
        for granule in (8, 16, 32, 64):
            for rmw in (False, True):
                traffic = external_prefix(cold, hot, granule, rmw)
                combined_bytes = traffic["external_transfer_bytes_per_hash"] + dataset_bytes
                placement_rows.append(dict(hot_prefix_bytes=hot, **traffic,
                    required_scratchpad_Bps=target_hps * traffic["external_transfer_bytes_per_hash"],
                    required_scratchpad_transactions_per_s=target_hps * traffic["external_transactions_per_hash"],
                    required_dataset_Bps=target_hps * dataset_bytes,
                    all_wall_energy_ceiling_j_per_transferred_bit=WALL_LIMIT_W / (target_hps * 8 * combined_bytes),
                    ceiling_scope="optimistic rejection ceiling assigns ALL wall energy to scratchpad+dataset transfers"))
        for latency_ns in (30, 100, 300):
            for ready in (1, 2, 4):
                latency_rows.append(dict(hot_prefix_bytes=hot, service_latency_ns=latency_ns,
                    **latency_requirement(target_hps, cold["bytecode_read8"] + cold["outer_read64"], latency_ns * 1e-9, ready)))
    return {
        "schema": "openrx.architecture.envelope.v1",
        "classification": "necessary_bounds_and_explicit_scenarios",
        "target_hps": target_hps,
        "strict_wall_limit_w": WALL_LIMIT_W,
        "strict_wall_energy_ceiling_j_per_hash": WALL_LIMIT_W / target_hps,
        "capacity_sweep": capacity_rows,
        "placement_sweep": placement_rows,
        "latency_sweep": latency_rows,
        "port_sweep": [{"width_bytes": width, "service_operations_per_hash": port_operations(counts, width),
            "banks": banks, "ports_per_bank": ports,
            "necessary_aggregate_bank_port_clocks_per_s": target_hps * port_operations(counts, width),
            "necessary_clock_hz_if_perfectly_balanced": target_hps * port_operations(counts, width) / (banks * ports),
            "actual_bank_conflicts_and_ready_time": "scheduler_required"}
            for width in (8, 16, 32, 64) for banks in (1, 2, 4, 8, 16, 32) for ports in (1, 2)],
        "dataset": {"logical_bytes_per_hash": dataset_bytes, "required_payload_Bps": target_hps * dataset_bytes,
            "requests_per_hash": dataset_bytes // 64,
            "internal_generation_or_cache_physical_traffic": None,
            "source": "accepted native light values from 256 MiB cache; no whole dataset materialized"},
        "dataset_latency_sweep": [dict(service_latency_ns=latency_ns,
            **latency_requirement(target_hps, dataset_bytes // 64, latency_ns * 1e-9, ready))
            for latency_ns in (30, 100, 300) for ready in (1, 2, 4)],
        "random_service_sweep": [
            {"hot_prefix_bytes": row["hot_prefix_bytes"], "assumed_random_to_peak_efficiency": eta,
             "necessary_peak_Bps_for_scratchpad_and_dataset":
                 target_hps * (external_prefix(row["cold_counts"], row["hot_prefix_bytes"])["external_transfer_bytes_per_hash"] + dataset_bytes) / eta,
             "measured_efficiency": None,
             "controller_bank_tRC_tFAW_refresh_turnaround_transaction_capacity": None}
            for row in prefixes for eta in (.1, .25, .5, .8)],
        "time_multiplex": {"full_image_save_restore_bytes_per_switch": 2 * SCRATCHPAD_BYTES,
            "Bps_per_switch_per_hash_at_target": 2 * SCRATCHPAD_BYTES * target_hps,
            "switches_per_hash": None, "resident_backing_required": True},
        "physical_inputs": {"clock_hz": None, "process": None, "sram_macro_area_mm2": None,
            "sram_leakage_w": None, "controller_sustainable_random_Bps": None,
            "dataset_energy_j_per_hash": None, "complete_wall_power_w": None,
            "engine_count_selected": None},
        "power": full_wall_power(target_hps, {}, {}, None, None),
        "gate": rejection_gate(),
    }
