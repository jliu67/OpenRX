"""Whole-machine conditional accounting, not a scheduler or silicon predictor.

Run: python3 -m tools.architecture.machine --input FILE --output NEW_FILE
Memory investigators can supply openrx.memory-service-contract.v1 objects.
Unknown physical costs stay unknown; unrelated operating points are not joined.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

from . import envelope

SCHEMA = "openrx.machine-feasibility.v1"
MEMORY_SCHEMA = "openrx.memory-service-contract.v1"
INPUT_CAP = 131072
OUTPUT_CAP = 262144
SP = 2097152
N = 16384
DATASET = 2181038016  # pinned native base + extra, not the 256MiB light cache
OPS = ("integer64", "mul64", "FP128", "DIVSQRT128", "bitwise128",
       "convert128", "AES128_round", "BLAKE2b_compression")
SERVICES = OPS + ("SP16_front", "receiver16_grant", "return_grant", "dataset_request")
MEMORY_FIELDS = {
    "schema", "id", "technology", "corner", "source_ids", "parameter_sources",
    "capacity_B", "transaction_B", "response_latency_s", "request_II_s",
    "sustained_payload_Bps", "sustained_transactions_per_s", "outstanding",
    "read_energy_pJ", "write_energy_pJ", "area_mm2_per_bit", "leakage_W_per_bit",
    "qualification", "scope", "exclusions", "response_interpretation",
}
MEMORY_NUMBERS = MEMORY_FIELDS - {
    "schema", "id", "technology", "corner", "source_ids", "parameter_sources",
    "qualification", "scope", "exclusions", "response_interpretation",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def number(x, name, *, positive=False, integer=False, unknown=False):
    if x is None and unknown:
        return None
    require(type(x) in (int, float) and math.isfinite(x), name + ": finite number required")
    require(x > 0 if positive else x >= 0, name + ": invalid sign")
    require(not integer or type(x) is int, name + ": integer required")
    return x


def strict_json(raw):
    def pairs(items):
        d = {}
        for k, v in items:
            require(k not in d, "duplicate JSON key: " + k)
            d[k] = v
        return d
    def constant(x):
        raise ValueError("nonfinite JSON constant: " + x)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def memory_contract(m, sources):
    require(set(m) == MEMORY_FIELDS and m["schema"] == MEMORY_SCHEMA, "memory schema/fields")
    require(m["qualification"] in ("unknown", "assumed", "characterized"), "memory qualification")
    require(m["response_interpretation"] in ("unknown", "fixed_service", "mean_at_declared_traffic",
                                            "lower_bound", "upper_bound"), "memory latency interpretation")
    require(bool(m["id"]) and bool(m["scope"]), "memory identity/scope")
    require(set(m["source_ids"]) <= set(sources), "unknown memory source")
    require(set(m["parameter_sources"]) <= MEMORY_NUMBERS, "memory provenance field")
    for k in MEMORY_NUMBERS:
        number(m[k], "memory." + k, unknown=True,
               positive=k in ("transaction_B", "response_latency_s", "request_II_s"),
               integer=k in ("capacity_B", "transaction_B", "outstanding"))
        if m[k] is None:
            continue
        source = m["parameter_sources"].get(k)
        require(source in m["source_ids"], "memory parameter lacks explicit provenance: " + k)
        p = sources[source]
        require(p.get("technology") == m["technology"] and p.get("corner") == m["corner"],
                "incompatible memory operating point: " + k + "; use separate contracts")
        if k not in ("capacity_B","transaction_B","outstanding") and p["kind"]!="assumed":
            require(m["technology"] and m["corner"],"unbound physical corner: keep separate anchor or explicit assumption")
        if m["qualification"] == "characterized":
            require(p["kind"] == "measured" and m["technology"] and m["corner"],
                    "characterized memory requires bound measured corner")
    require(m["transaction_B"] in (None, 16, 64), "only explicit 16B/64B service contracts supported")


def validate(d):
    require(set(d) == {"schema", "target", "sources", "baseline", "samples", "architectures",
                       "scenarios", "physical", "anchors", "retained_comparators"}, "top-level schema")
    require(d["schema"] == SCHEMA, "model schema")
    t = d["target"]
    require(set(t) == {"hashes_per_s", "wall_limit_W", "research_fraction", "private_capacity_B"}, "target fields")
    for k in t:
        number(t[k], "target." + k, positive=True)
    require(t["research_fraction"] <= 1, "research fraction")
    require(d["baseline"]["v2_canonical_hashes"] == 4, "four-input canonical baseline required")
    require(d["baseline"]["v1_regression_scope"] and d["baseline"]["v1_source_id"] in d["sources"],
            "explicit v1 regression baseline required")
    require(1 <= len(d["samples"]) <= 16 and 1 <= len(d["architectures"]) <= 8
            and 1 <= len(d["scenarios"]) <= 8, "finite model dimensions")
    for group, key in ((d["samples"], "nonce"), (d["architectures"], "id"), (d["scenarios"], "id")):
        require(len({x[key] for x in group}) == len(group), "duplicate " + key)
    for s in d["samples"]:
        number(s["nonce"], "nonce", integer=True)
        require(type(s["canonical_digest_equal"]) is bool and s["canonical_digest_equal"], "canonical digest")
        for k in ("input_sha256", "digest_hex"):
            require(isinstance(s[k], str) and len(s[k]) == 64
                    and all(c in "0123456789abcdef" for c in s[k]), k)
        require(isinstance(s["input_hex"], str) and len(s["input_hex"]) == 120
                and all(c in "0123456789abcdef" for c in s["input_hex"]), "immutable60B input")
        raw=bytes.fromhex(s["input_hex"])
        require(hashlib.sha256(raw).hexdigest()==s["input_sha256"]
                and int.from_bytes(raw[-8:],"little")==s["nonce"], "nonce/input fingerprint mismatch")
        require(set(s["work"]) == set(OPS), "exclusive primitive work classes")
        for k, v in s["work"].items():
            number(v, k, integer=True)
        for k in ("instructions", "read8", "write8", "dataset_requests", "tier_read64", "tier_write64"):
            number(s[k], k, integer=True)
        require(s["dataset_requests"] == N, "dataset request count")
        require(s["work"]["AES128_round"] == 530696 and s["work"]["BLAKE2b_compression"] == 17,
                "complete lifecycle AES/BLAKE work required")
    for a in d["architectures"]:
        require(a["placement"] in ("all_local", "static256K_cache16K_sector"), "supported placement")
        require(a["physical_id"] in d["physical"], "physical profile")
        for k in ("contexts_per_engine", "native_dispatch", "native_retire", "fetch_B_per_cycle",
                  "internal_issue", "phase_events_per_iteration", "SP_banks", "SP_bank_II",
                  "SP_credits_per_engine", "SP_read_credit_cycles", "SP_write_credit_cycles"):
            number(a[k], a["id"] + "." + k, positive=True, integer=True)
        number(a["aux_B_per_context"], "aux capacity", unknown=True, integer=True)
        number(a["predecode_events_per_hash"],"predecode events",integer=True)
        require(a["dataset_credits_per_context"] in (1, 2), "only source-supported 1/2 DS credits")
        require(set(a["resources"]) == set(SERVICES), "resource classes")
        for name, r in a["resources"].items():
            require(set(r) == {"count", "latency_cycles", "II_cycles"}, "FU/service fields")
            number(r["count"], name + " count", positive=True, integer=True)
            number(r["latency_cycles"], name + " latency", positive=True, unknown=True)
            number(r["II_cycles"], name + " II", positive=True, unknown=True)
        for k in ("full_hash_residence_cycles", "complete_engine_service_cycles_per_hash"):
            number(a[k], k, unknown=True, positive=True)
        for k in ("v2_equivalent", "v1_equivalent", "finite_schedule_checked"):
            require(a[k] is None or type(a[k]) is bool, k)
    for s in d["scenarios"]:
        number(s["frequency_Hz"], "frequency", positive=True)
        number(s["utilization"], "utilization", positive=True)
        require(s["utilization"] <= 1 and s["qualification"] == "illustrative_unqualified", "scenario scope")
    for p in d["physical"].values():
        app=p.get("applicability",{"mode":"unqualified_sensitivity_only"})
        require(app["mode"] in ("unqualified_sensitivity_only","bounded"),"profile applicability mode")
        if app["mode"]=="bounded":
            require(set(app)=={"mode","frequency_Hz","placements","technology","corner","source_id"},"bounded profile applicability fields")
            require(app["frequency_Hz"] and app["placements"],"bounded profile frequency/traffic required")
            require(app["technology"] and app["corner"],"bounded profile requires explicit PVT")
            for f in app["frequency_Hz"]:number(f,"profile frequency",positive=True)
            require(set(app["placements"]) <= {"all_local","static256K_cache16K_sector"},"profile traffic scope")
            source=d["sources"].get(app["source_id"])
            require(source is not None and app["technology"]==p["technology"]==source.get("technology")
                    and app["corner"]==p["corner"]==source.get("corner"),"profile applicability PVT/source mismatch")
        require(set(p["operation_energy_pJ"]) == set(OPS), "operation energy classes")
        require(set(p["unit_area_mm2"]) == set(SERVICES), "area resource classes")
        require(set(p["unit_leakage_W"]) == set(SERVICES), "leakage resource classes")
        for section in ("operation_energy_pJ", "unit_area_mm2", "unit_leakage_W", "static_dc_W"):
            for k, v in p[section].items():
                number(v, section + "." + k, unknown=True)
        require(set(p["static_dc_W"]) == set(envelope.STATIC_TERMS), "static wall accounting")
        for k in ("logic_base_area_mm2_per_engine", "aux_area_mm2_per_context", "RF_metadata_J_per_hash",
                  "controller_J_per_hash", "fabric_clock_J_per_hash", "PHY_pJ_per_external_bit",
                  "setup_control_and_dataset_init_J_per_hash", "AC_auxiliary_W", "psu_efficiency",
                  "usable_area_mm2_per_die", "packaged_die_cost_USD", "fixed_board_cost_USD",
                  "logic_base_leakage_W_per_engine", "aux_leakage_W_per_context",
                  "controller_PHY_interconnect_area_mm2", "external_wire_to_payload_ratio"):
            number(p[k], k, unknown=True)
        require(p["external_wire_to_payload_ratio"] is None or p["external_wire_to_payload_ratio"]>=1,
                "external wire/payload overhead cannot be less than1")
        logic_values = list(p["operation_energy_pJ"].values()) + list(p["unit_area_mm2"].values()) + list(p["unit_leakage_W"].values())
        if any(v is not None for v in logic_values):
            source = d["sources"].get(p["logic_source_id"])
            require(source is not None and source.get("technology") == p["technology"]
                    and source.get("corner") == p["corner"], "logic operating-point provenance")
            if source["kind"]=="measured":require(p["technology"] and p["corner"],"measured logic needs a bound corner")
        require(p["psu_efficiency"] is None or 0 < p["psu_efficiency"] <= 1, "conversion efficiency")
        for k, width in (("private_memory",16), ("external_memory",64)):
            memory_contract(p[k], d["sources"])
            require(p[k]["transaction_B"]==width, "memory energy/service transaction width")
        require(set(p.get("external_classes",{})) <= {"dataset","scratchpad_backing"},"external traffic classes")
        for m in p.get("external_classes",{}).values():
            memory_contract(m,d["sources"])
            require(m["transaction_B"]==64,"external class transaction width")


def demand(sample, architecture):
    """Full-path requests; 8B useful accesses still occupy a 16B logical port."""
    reads = sample["read8"] + 2 * SP // 16  # entry + final scan
    writes = sample["write8"] + 2 * SP // 16  # tail + initial fill
    ops = dict(sample["work"])
    ops.update(SP16_front=reads + writes,
               receiver16_grant=2 * reads + 8 * sample["dataset_requests"],
               return_grant=reads + writes + 4 * sample["dataset_requests"],
               dataset_request=sample["dataset_requests"])
    tiered = architecture["placement"] != "all_local"
    external_read64 = sample["dataset_requests"] + (sample["tier_read64"] if tiered else 0)
    external_write64 = sample["tier_write64"] if tiered else 0
    return {"resource_work": ops, "SP_front_read16": reads, "SP_front_write16": writes,
            "SP_useful_B": 8 * (sample["read8"] + sample["write8"]) + 4 * SP,
            "SP_port_B": 16 * (reads + writes), "dataset_payload_B": 64 * N,
            "external_read64": external_read64, "external_write64": external_write64,
            "external_payload_B": 64 * (external_read64 + external_write64),
            "external_classes":{"dataset":{"read64":sample["dataset_requests"],"write64":0},
                "scratchpad_backing":{"read64":sample["tier_read64"] if tiered else 0,
                                       "write64":sample["tier_write64"] if tiered else 0}},
            "private_macro_read16":None if tiered else reads,
            "private_macro_write16":None if tiered else writes,
            "local_macro_access_counts_complete": not tiered,
            "micro_events_floor": sum(sample["work"].values()) + reads + writes + N + 4 * N}


def sum_known(terms):
    return sum(v for v in terms.values() if v is not None)


def complete_sum(terms):
    return sum(terms.values()) if all(v is not None for v in terms.values()) else None


def memory_screen(m, rate_Bps, rate_tx, required_B, credits, *, check_credits=True):
    missing, failures = [], []
    for key, required in (("capacity_B", required_B), ("sustained_payload_Bps", rate_Bps),
                          ("sustained_transactions_per_s", rate_tx)):
        if required is None:
            missing.append(key+"_demand")
        elif m[key] is None:
            missing.append(key)
        elif m[key] < required:
            failures.append(key)
    latency = credit_latency(m) if check_credits else None
    outstanding = math.ceil(rate_tx * latency) if latency is not None and rate_tx is not None else None
    if check_credits and m["outstanding"] is not None:
        credits = m["outstanding"] if credits is None else min(credits, m["outstanding"])
    if outstanding is None:
        missing.append("mean_or_lower_bound_response_for_credit_accounting")
    elif credits is None:
        missing.append("class_credit_upper_bound")
    elif outstanding > credits:
        failures.append("causal_credit_capacity")
    if m["request_II_s"] is None:
        missing.append("request_II_s")
    # A bank's II is not aggregate service: sustained rates must be supplied independently.
    return {"necessary_outstanding_average": outstanding, "credit_supply": credits if check_credits else None,
            "required_capacity_B":required_B,"required_payload_Bps":rate_Bps,"required_transactions_per_s":rate_tx,
            "failures": failures, "unknown": missing,
            "rejected":True if failures else None if missing else False,
            "qualification": m["qualification"], "not_a_bank_schedule": True}


def credit_latency(m):
    """A maximum/tail/access-time quote is not the mean credit residence."""
    return m["response_latency_s"] if m["response_interpretation"] in (
        "fixed_service", "mean_at_declared_traffic", "lower_bound") else None


def applicable_profile(p, architecture, scenario):
    """Do not reuse a bounded cost/service point outside its frequency/traffic/PVT."""
    app=p.get("applicability",{"mode":"unqualified_sensitivity_only"})
    if app["mode"]=="unqualified_sensitivity_only":
        return p,{"mode":app["mode"],"matched":None,"physical_extrapolation_qualified":False}
    matched=scenario["frequency_Hz"] in app["frequency_Hz"] and architecture["placement"] in app["placements"]
    result={"mode":"bounded","matched":matched,"source_id":app["source_id"],
            "frequency_Hz":app["frequency_Hz"],"placements":app["placements"],
            "technology":app["technology"],"corner":app["corner"],"physical_extrapolation_qualified":False}
    if matched:return p,result
    masked=copy.deepcopy(p)
    for k,v in list(masked.items()):
        if type(v) in (int,float):masked[k]=None
    for section in ("operation_energy_pJ","unit_area_mm2","unit_leakage_W","static_dc_W"):
        masked[section]=dict.fromkeys(masked[section],None)
    for m in [masked["private_memory"],masked["external_memory"],*masked.get("external_classes",{}).values()]:
        for key in MEMORY_NUMBERS-{"transaction_B"}:m[key]=None
    result["disposition"]="outside supplied scope: physical costs and service unknown, not extrapolated"
    return masked,result


def access_energy(m, reads, writes):
    if (reads and m["read_energy_pJ"] is None) or (writes and m["write_energy_pJ"] is None):return None
    return (reads*(m["read_energy_pJ"] or 0)+writes*(m["write_energy_pJ"] or 0))*1e-12


def cost(p, a, work, engines, states, hot_B, hps, wall_limit):
    q = p["operation_energy_pJ"]
    operation = {k: 0 if work["resource_work"][k]==0 else None if q[k] is None else work["resource_work"][k] * q[k] * 1e-12 for k in OPS}
    compute = complete_sum(operation)
    compute = None if compute is None or p["RF_metadata_J_per_hash"] is None else compute + p["RF_metadata_J_per_hash"]
    private, external = p["private_memory"], p["external_memory"]
    sp = None
    if work["local_macro_access_counts_complete"] and private["read_energy_pJ"] is not None and private["write_energy_pJ"] is not None:
        sp = (work["SP_front_read16"] * private["read_energy_pJ"] + work["SP_front_write16"] * private["write_energy_pJ"]) * 1e-12
    if p.get("external_classes"):
        ext=complete_sum({name:0 if not counts["read64"]+counts["write64"] else
            access_energy(p["external_classes"][name],counts["read64"],counts["write64"])
            if name in p["external_classes"] else None for name,counts in work["external_classes"].items()})
    else:ext=access_energy(external,work["external_read64"],work["external_write64"])
    io_floor = None if p["PHY_pJ_per_external_bit"] is None else work["external_payload_B"] * 8 * p["PHY_pJ_per_external_bit"] * 1e-12
    io = None if io_floor is None or p["external_wire_to_payload_ratio"] is None else io_floor*p["external_wire_to_payload_ratio"]
    dynamic = dict(compute=compute, scratchpad_dynamic=sp, dataset_dynamic=ext,
                   controllers_phy=complete_sum({"PHY": io, "controller": p["controller_J_per_hash"]}),
                   fabric_clock=p["fabric_clock_J_per_hash"],
                   input_hash_fill_program_dataset_generation=p["setup_control_and_dataset_init_J_per_hash"])
    static = dict(p["static_dc_W"])
    leak_parts = {k: None if p["unit_leakage_W"][k] is None else engines*r["count"]*p["unit_leakage_W"][k]
                  for k,r in a["resources"].items()}
    leak_parts["base"] = None if p["logic_base_leakage_W_per_engine"] is None else engines*p["logic_base_leakage_W_per_engine"]
    leak_parts["aux"] = None if p["aux_leakage_W_per_context"] is None else states*p["aux_leakage_W_per_context"]
    if static["logic_leakage"] is None:
        static["logic_leakage"] = complete_sum(leak_parts)
    if static["sram_leakage"] is None and private["leakage_W_per_bit"] is not None:
        static["sram_leakage"] = states*hot_B*8*private["leakage_W_per_bit"]
    wall = envelope.full_wall_power(hps, dynamic, static, p["psu_efficiency"], p["AC_auxiliary_W"])
    if wall["wall_power_w"] is not None:
        wall["status"]="conditional_under_limit" if wall["wall_power_w"]<wall_limit else "rejected"
    # Partial sums are nonnegative lower contributions, never a complete power estimate.
    partial = dict(operation, RF_metadata=p["RF_metadata_J_per_hash"], SP=sp, external=ext,
                   PHY=io_floor if io is None else io, controller=p["controller_J_per_hash"], fabric=p["fabric_clock_J_per_hash"],
                   setup=p["setup_control_and_dataset_init_J_per_hash"])
    wall["known_DC_contribution_W"] = hps*sum_known(partial)+sum_known(static)
    if static["logic_leakage"] is None:wall["known_DC_contribution_W"]+=sum_known(leak_parts)
    wall["missing_components"] = [k for k,v in partial.items() if v is None]
    if p["external_wire_to_payload_ratio"] is None:wall["missing_components"].append("external_wire_to_payload_ratio")
    parts = {k: None if p["unit_area_mm2"][k] is None else engines * r["count"] * p["unit_area_mm2"][k]
             for k,r in a["resources"].items()}
    parts["logic_control"] = None if p["logic_base_area_mm2_per_engine"] is None else engines * p["logic_base_area_mm2_per_engine"]
    parts["private_aux"] = None if p["aux_area_mm2_per_context"] is None else states * p["aux_area_mm2_per_context"]
    parts["private_data"] = None if private["area_mm2_per_bit"] is None else states * hot_B * 8 * private["area_mm2_per_bit"]
    parts["global_controller_PHY_interconnect"] = p["controller_PHY_interconnect_area_mm2"]
    # Off-chip dataset capacity is not added to logic die area.
    area = complete_sum(parts)
    dies = math.ceil(area / p["usable_area_mm2_per_die"]) if area is not None and p["usable_area_mm2_per_die"] else None
    usd = None if dies is None or p["packaged_die_cost_USD"] is None or p["fixed_board_cost_USD"] is None else dies * p["packaged_die_cost_USD"] + p["fixed_board_cost_USD"]
    return {"wall": wall, "area_mm2": area, "known_partial_area_mm2": sum_known(parts),
            "area_unknown": [k for k,v in parts.items() if v is None],
            "chip_count_area_only_floor": dies, "partial_die_board_cost_USD": usd,
            "cost_excludes": ["memory packages", "yield/NRE unless included in packaged price", "cooling/PSU/interconnect"]}


def evaluate(d):
    validate(d)
    t, rows = d["target"], []
    for a in d["architectures"]:
        for scenario in d["scenarios"]:
            f, u = scenario["frequency_Hz"], scenario["utilization"]
            for s in d["samples"]:
                w = demand(s, a)
                floors = {k: w["resource_work"][k] * r["II_cycles"] / r["count"]
                          for k,r in a["resources"].items() if r["II_cycles"] is not None}
                floors.update(native_dispatch=s["instructions"] / a["native_dispatch"],
                              instruction_fetch=8 * s["instructions"] / a["fetch_B_per_cycle"],
                              ordered_retirement=(s["instructions"] + N * a["phase_events_per_iteration"] + a["predecode_events_per_hash"]) / a["native_retire"],
                              shared_internal_issue=(w["micro_events_floor"]+a["predecode_events_per_hash"])/a["internal_issue"])
                if w["local_macro_access_counts_complete"]:
                    floors.update(bank_balanced_SP=(w["private_macro_read16"]+w["private_macro_write16"])*a["SP_bank_II"]/a["SP_banks"],
                        finite_SP_credit=(w["private_macro_read16"]*a["SP_read_credit_cycles"]+
                            w["private_macro_write16"]*a["SP_write_credit_cycles"])/a["SP_credits_per_engine"])
                floor = max(floors.values())
                witness = a["complete_engine_service_cycles_per_hash"]
                require(witness is None or witness >= floor, "service witness contradicts resource floor")
                service = floor if witness is None else witness
                engines = math.ceil(t["hashes_per_s"] * service / (f * u))
                residence = a["full_hash_residence_cycles"]
                if residence is not None:
                    require(residence >= floor, "residence witness contradicts resource floor")
                    engines=max(engines,math.ceil(t["hashes_per_s"]*residence/(f*a["contexts_per_engine"])))
                states = engines * a["contexts_per_engine"]
                hot = SP if a["placement"] == "all_local" else 278528
                private_B = states * hot
                p,application=applicable_profile(d["physical"][a["physical_id"]],a,scenario)
                external_tx = t["hashes_per_s"] * (w["external_read64"] + w["external_write64"])
                credits = states * a["dataset_credits_per_context"]
                mixed=bool(w["external_classes"]["scratchpad_backing"]["read64"]+w["external_classes"]["scratchpad_backing"]["write64"])
                # Aggregate mixed latency cannot be assigned to either causal class.
                mem = memory_screen(p["external_memory"], t["hashes_per_s"] * w["external_payload_B"],
                    external_tx, DATASET+(states*SP if hot!=SP else 0),credits if not mixed else None,check_credits=not mixed)
                classes={}
                for name,counts in w["external_classes"].items():
                    rate=t["hashes_per_s"]*(counts["read64"]+counts["write64"])
                    if not rate:continue
                    cm=p.get("external_classes",{}).get(name)
                    if cm is None and not mixed and name=="dataset":cm=p["external_memory"]
                    if cm is None:
                        cm=copy.deepcopy(p["external_memory"])
                        for key in MEMORY_NUMBERS-{"transaction_B"}:cm[key]=None
                        cm["qualification"]="unknown"
                    cc=credits if name=="dataset" else None
                    if p["external_memory"]["outstanding"] is not None:
                        cap=p["external_memory"]["outstanding"];cc=cap if cc is None else min(cc,cap)
                    classes[name]=memory_screen(cm,64*rate,rate,DATASET if name=="dataset" else states*SP,cc)
                    if mixed or cm is not p["external_memory"]:
                        mem["failures"].extend(name+"_"+x for x in classes[name]["failures"])
                mem["classes"]={name:{k:value for k,value in entry.items()if k in (
                    "required_transactions_per_s","necessary_outstanding_average","credit_supply","rejected","failures")}
                    for name,entry in classes.items()}
                if hot != SP:
                    mem["unknown"].append("separate_tiered_SP_queues_credits_and_refill_service")
                mem["dataset_only_necessary_outstanding"]=classes["dataset"]["necessary_outstanding_average"]
                mem["dataset_only_credit_upper_limit"]=classes["dataset"]["credit_supply"]
                mem["unknown"].append("native_source_order_is_not_hardware_ready_timing")
                mem["rejected"]=True if mem["failures"] else None
                macro_ops=None if not w["local_macro_access_counts_complete"] else w["private_macro_read16"]+w["private_macro_write16"]
                private = memory_screen(p["private_memory"],None if macro_ops is None else 16*t["hashes_per_s"]*macro_ops,
                    None if macro_ops is None else t["hashes_per_s"]*macro_ops,private_B,
                    engines*a["SP_credits_per_engine"] if macro_ops is not None else None)
                if hot != SP:
                    private["unknown"].append("local_cache_refill_writeback_and_tag_activity")
                capacity_rejected = private_B > t["private_capacity_B"]
                nominal = t["private_capacity_B"] / hot * f / t["hashes_per_s"]
                costs=cost(p,a,w,engines,states,hot,t["hashes_per_s"],t["wall_limit_W"])
                reasons=[]
                if capacity_rejected: reasons.append("fixed_pool_private_capacity")
                if costs["wall"]["known_DC_contribution_W"]>=t["wall_limit_W"]:reasons.append("known_DC_contribution_exceeds_strict_wall_limit")
                if costs["wall"]["wall_power_w"] is not None and costs["wall"]["wall_power_w"]>=t["wall_limit_W"]:reasons.append("strict_wall_limit")
                reasons += ["external_"+x for x in mem["failures"]]+["private_"+x for x in private["failures"]]
                if a["v2_equivalent"] is False or a["v1_equivalent"] is False:reasons.append("candidate_correctness_failed")
                rows.append({"architecture":a["id"], "scenario":scenario["id"], "nonce":s["nonce"],
                    "frequency_Hz_assumed":f, "utilization_assumed":u,
                    "engine_service_floor_cycles":math.ceil(floor), "floor_bottleneck":max(floors,key=floors.get),
                    "target_engine_minimum_or_planning_count":engines, "provisioned_contexts":states,
                    "private_data_B":private_B, "private_aux_B":None if a["aux_B_per_context"] is None else states*a["aux_B_per_context"],
                    "external_dataset_B":DATASET, "external_backing_B":states * SP if hot != SP else 0,
                    "optimistic_private_context_floor":math.ceil(t["hashes_per_s"] * floor / f),
                    "full_hash_residence_cycles":residence,
                    "nominal_capacity_cycle_budget":nominal,
                    "research_reserve_screen_exceeded":floor > nominal*t["research_fraction"],
                    "fixed_pool_capacity_rejected":capacity_rejected,
                    "resource_floors_cycles":{k:math.ceil(v) for k,v in floors.items()},
                    "resource_service_unknown":[k for k,v in a["resources"].items()if v["II_cycles"] is None]+([] if macro_ops is not None else ["private_macro_traffic_and_credit_bounds"]),
                    "target_resource_instance_counts":{k:engines*r["count"] for k,r in a["resources"].items()},
                    "traffic":{k:v for k,v in w.items() if k != "resource_work"},
                    "external_service":mem,
                    "private_service":private,
                    "physical_profile_application":application,
                    "cost":costs,
                    "bare_capacity_area_anchors_mm2":{x["id"]:math.ceil(private_B/x["macro_B"])*x["macro_area_mm2"]
                        for x in d["anchors"] if x["role"]=="capacity_area_only"},
                    "whole_wall_exclusive_W_per_engine_ceiling":t["wall_limit_W"]/engines,
                    "whole_wall_exclusive_pJ_per_native_instruction_ceiling":t["wall_limit_W"]/t["hashes_per_s"]*1e12/s["instructions"],
                    "remaining_correctness": [k for k in ("v2_equivalent","v1_equivalent","finite_schedule_checked") if a[k] is not True],
                    "status":"conditional_rejection" if reasons else "unresolved", "rejections":reasons,
                    "demonstrated_hardware_feasibility":False})
    sensitivity={
        "W_per_pJ_per_primitive_event":{k:{"min":min(s["work"][k] for s in d["samples"])*t["hashes_per_s"]*1e-12,
            "max":max(s["work"][k] for s in d["samples"])*t["hashes_per_s"]*1e-12} for k in OPS},
        "all_local_W_per_pJ_per_external_bit":N*64*8*t["hashes_per_s"]*1e-12,
        "dataset_only_latency_credit_sensitivity":[{"assumed_response_ns":ns,
            "necessary_outstanding_average":math.ceil(t["hashes_per_s"]*N*ns*1e-9),
            "not_hardware_readiness":True}for ns in (30,100,300)],
        "all_local_capacity_cycle_budgets":[{"frequency_Hz_assumed":f,"private_SP_GiB":g,
            "nominal_cycles":g*1024**3/SP*f/t["hashes_per_s"]}
            for f in (.5e9,1e9,2e9,3e9) for g in (1,4,8,16)],
        "scope":"Factorized arithmetic slopes/budgets, not compatible physical points or independent uniform arrivals."}
    return {"schema":SCHEMA+".report", "target":t, "baseline":d["baseline"], "rows":rows,"sensitivity":sensitivity,
            "scenarios":d["scenarios"], "sources":d["sources"], "anchors_separate_not_combined":d["anchors"],
            "retained_comparators_not_recalibration":d["retained_comparators"],
            "limits":["Work/service floors are not achievable schedules; latency and II are different.",
                      "Sample maxima are four-input maxima, not worst-case workload guarantees.",
                      "Planning utilization and the20% reserve are assumptions, not owner acceptance criteria.",
                      "Fullhash residence, compatible physical costs and new-candidate v1/v2 correctness remain unknown.",
                      "Private data and auxiliary state are separate from shared external dataset/backing."]}


def verify_sources(inputs):
    """Hash retained files AND check the small projected workload, without replay."""
    sources=inputs["sources"]
    for source in sources.values():
        if "path" not in source:
            continue
        data=Path(source["path"]).read_bytes()
        require(len(data)==source["bytes"] and hashlib.sha256(data).hexdigest()==source["sha256"],
                "source binding mismatch: "+source["path"])
    native={x["nonce"]:x for x in map(json.loads,Path(sources["native"]["path"]).read_text().splitlines())}
    census=json.loads(Path(sources["census"]["path"]).read_text())
    counts={x["nonce"]:x for x in census["cases"]}
    locality={x["nonce"]:x for x in json.loads(Path(sources["locality"]["path"]).read_text())["input_rows"]}
    require(len(native)==len(counts)==len(locality)==4,"four-input retained source set")
    for s in inputs["samples"]:
        n=s["nonce"];r=native[n];c=counts[n];l=locality[n]
        require(r["canonical_digest_equal"] and c["canonical_digest_equal"],"retained canonical check")
        require(s["digest_hex"]==r["digest_hex"]==c["digest_hex"]==l["digest"]
                and s["input_hex"]==r["input_hex"]==l["input_hex"]
                and s["input_sha256"]==c["input_sha256"],"retained input/digest projection")
        require(s["instructions"]==r["instruction_steps"]==c["instruction_steps"]
                and s["read8"]==c["bytecode_read8"] and s["write8"]==c["bytecode_write8"],
                "retained workload count projection")
        expected=dict(r["dependency_certificate"]["policies"][1]["work"])
        expected["AES128_round"]=census["source_derived_fixed_work"]["AES128_block_round_calls"]
        expected["BLAKE2b_compression"]=census["source_derived_fixed_work"]["BLAKE2b_compressions"]
        require(s["work"]=={k:expected[k]for k in OPS},"retained primitive-work projection")
        policy=next(x for x in l["policies"]if x["name"]=="static256K_cache16K_sector")
        require(s["tier_read64"]==policy["64B_demand_read_fills"]+policy["64B_RFO_reads"]+policy["partial64B_writebacks"]
                and s["tier_write64"]==policy["64B_writebacks"],"retained locality projection")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--verify-sources",action="store_true",help="Verify retained local source bytes; never execute them")
    args=parser.parse_args(argv)
    raw=args.input.read_bytes()
    require(len(raw)<=INPUT_CAP,"input cap exceeded")
    inputs=strict_json(raw)
    if args.verify_sources:
        verify_sources(inputs)
    report=evaluate(inputs)
    report["source_validation"]="retained_hashes_and_exact_projection" if args.verify_sources else "not_requested_fixture_only"
    report["input_sha256"]=hashlib.sha256(raw).hexdigest()
    report["model_code_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["reused_envelope_sha256"]=hashlib.sha256(Path(envelope.__file__).read_bytes()).hexdigest()
    report["python_runtime"]=sys.version
    data=(json.dumps(report,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
    require(len(data)<=OUTPUT_CAP,"complete output exceeds cap; no truncation")
    with args.output.open("xb") as f:
        f.write(data)
    print(json.dumps({"output":str(args.output),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
                      "rows":len(report["rows"]),"physical_feasibility":False}))


if __name__ == "__main__":
    main()
