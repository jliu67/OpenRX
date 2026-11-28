"""Finite arithmetic/contract regressions; no native, HDL or physical workload."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.architecture import machine as M

FIXTURE = Path(__file__).resolve().parents[1] / "tools/architecture/fixtures/machine-baseline.json"


class MachineFeasibility(unittest.TestCase):
    def setUp(self):
        self.d = json.loads(FIXTURE.read_text())
        self.d["samples"] = self.d["samples"][:1]
        self.d["architectures"] = self.d["architectures"][1:2]
        self.d["scenarios"] = self.d["scenarios"][:1]

    def row(self):
        return M.evaluate(self.d)["rows"][0]

    def set_memory(self, which, key, value):
        m=self.d["physical"]["unknown"][which]
        m[key]=value
        m["parameter_sources"][key]="protocol_assumptions"
        if key=="response_latency_s":m["response_interpretation"]="fixed_service"

    def zero_energy_fixture(self):
        p=self.d["physical"]["unknown"]
        p["logic_source_id"]="protocol_assumptions"
        p["operation_energy_pJ"]={k:0 for k in M.OPS}
        for k in ("RF_metadata_J_per_hash","controller_J_per_hash","fabric_clock_J_per_hash",
                  "PHY_pJ_per_external_bit","setup_control_and_dataset_init_J_per_hash","AC_auxiliary_W"):
            p[k]=0
        p["psu_efficiency"]=1
        p["external_wire_to_payload_ratio"]=1
        p["static_dc_W"]={k:0 for k in M.envelope.STATIC_TERMS}
        for which in ("private_memory","external_memory"):
            self.set_memory(which,"read_energy_pJ",0)
            self.set_memory(which,"write_energy_pJ",0)
        return p

    def test_unknown_power_and_area_are_not_zero_or_pass(self):
        r=self.row()
        self.assertIsNone(r["cost"]["wall"]["wall_power_w"])
        self.assertIsNone(r["cost"]["area_mm2"])
        self.assertFalse(r["demonstrated_hardware_feasibility"])
        self.assertGreater(len(r["remaining_correctness"]),0)

    def test_full_lifecycle_and_receiver_accounting(self):
        s=self.d["samples"][0];a=self.d["architectures"][0];w=M.demand(s,a)
        self.assertEqual(w["SP_port_B"],31477376)
        self.assertEqual(w["SP_useful_B"],19932992)
        self.assertEqual(w["resource_work"]["AES128_round"],530696)
        self.assertEqual(w["resource_work"]["BLAKE2b_compression"],17)
        self.assertEqual(w["resource_work"]["receiver16_grant"],2*(1046784+262144)+8*16384)
        self.assertEqual(w["external_payload_B"],1048576)
        self.assertNotIn("nested_dataset_availability",w["resource_work"])

    def test_fetch_is_eight_bytes_and_phase_retirement_is_paid(self):
        r=self.row();s=self.d["samples"][0]
        self.assertEqual(r["resource_floors_cycles"]["instruction_fetch"],-(-s["instructions"]//4))
        self.assertEqual(r["resource_floors_cycles"]["ordered_retirement"],-(-(s["instructions"]+66*16384+6144)//4))
        self.assertIn("BLAKE2b_compression",r["resource_service_unknown"])

    def test_latency_is_not_initiation_interval(self):
        r=self.row()["resource_floors_cycles"]
        self.d["architectures"][0]["resources"]["DIVSQRT128"]["latency_cycles"]=80
        self.assertEqual(r,self.row()["resource_floors_cycles"])
        self.d["architectures"][0]["resources"]["DIVSQRT128"]["II_cycles"]=80
        self.assertGreater(self.row()["resource_floors_cycles"]["DIVSQRT128"],r["DIVSQRT128"])

    def test_private_credit_hold_is_charged(self):
        r=self.row()["resource_floors_cycles"]["finite_SP_credit"]
        self.d["architectures"][0]["SP_credits_per_engine"]=1
        self.assertGreaterEqual(self.row()["resource_floors_cycles"]["finite_SP_credit"],4*r-3)

    def test_pooling_does_not_give_free_context_capacity(self):
        one=self.row()
        self.d["architectures"][0]["contexts_per_engine"]=4
        four=self.row()
        self.assertEqual(one["engine_service_floor_cycles"],four["engine_service_floor_cycles"])
        self.assertEqual(four["private_data_B"],4*one["private_data_B"])

    def test_twenty_percent_is_only_a_research_screen(self):
        r=self.row();self.d["target"]["research_fraction"]=.01
        x=self.row()
        self.assertTrue(x["research_reserve_screen_exceeded"])
        self.assertEqual(r["rejections"],x["rejections"])

    def test_dataset_latency_credit_rejection_without_peak_inference(self):
        self.set_memory("external_memory","response_latency_s",.01)
        self.set_memory("external_memory","request_II_s",1e-9)
        r=self.row()
        self.assertIn("external_causal_credit_capacity",r["rejections"])
        self.assertIn("sustained_payload_Bps",r["external_service"]["unknown"])
        self.assertNotIn("request_II_s",r["external_service"]["unknown"])

    def test_physical_outstanding_limit_is_not_ignored(self):
        self.set_memory("external_memory","response_latency_s",1e-6)
        self.set_memory("external_memory","outstanding",1)
        r=self.row()
        self.assertEqual(r["external_service"]["credit_supply"],1)
        self.assertIn("external_causal_credit_capacity",r["rejections"])

    def test_upper_latency_is_not_mean_or_a_credit_rejection(self):
        self.set_memory("external_memory","response_latency_s",.01)
        self.d["physical"]["unknown"]["external_memory"]["response_interpretation"]="upper_bound"
        r=self.row()
        self.assertIsNone(r["external_service"]["necessary_outstanding_average"])
        self.assertNotIn("external_causal_credit_capacity",r["rejections"])

    def test_unknown_wire_overhead_prevents_complete_PHY_power(self):
        p=self.zero_energy_fixture();p["external_wire_to_payload_ratio"]=None
        r=self.row()
        self.assertIsNone(r["cost"]["wall"]["wall_power_w"])
        self.assertIn("external_wire_to_payload_ratio",r["cost"]["wall"]["missing_components"])

    def test_tiered_traffic_rmw_and_credits_are_separate(self):
        d=json.loads(FIXTURE.read_text());self.d["architectures"]=[d["architectures"][3]]
        r=self.row()
        self.assertEqual(r["traffic"]["external_payload_B"],14028736)
        self.assertIsNone(r["external_service"]["credit_supply"])
        self.assertIsNone(r["cost"]["wall"]["wall_power_w"])
        self.assertIn("local_cache_refill_writeback_and_tag_activity",r["private_service"]["unknown"])

    def tiered(self):
        self.d["architectures"]=[json.loads(FIXTURE.read_text())["architectures"][3]]

    def class_contract(self, latency, *, outstanding=None):
        m=copy.deepcopy(self.d["physical"]["unknown"]["external_memory"])
        m["response_latency_s"]=latency;m["response_interpretation"]="fixed_service"
        m["parameter_sources"]["response_latency_s"]="protocol_assumptions"
        if outstanding is not None:
            m["outstanding"]=outstanding;m["parameter_sources"]["outstanding"]="protocol_assumptions"
        return m

    def test_mixed_latency_is_not_dataset_latency(self):
        self.tiered();self.set_memory("external_memory","response_latency_s",.01)
        r=self.row()
        self.assertIsNone(r["external_service"]["dataset_only_necessary_outstanding"])
        self.assertIsNone(r["external_service"]["rejected"])
        self.assertFalse(any("credit_capacity"in x for x in r["rejections"]))

    def test_tiered_front_is_not_macro_rate_or_credit_demand(self):
        self.tiered()
        for k,v in [("response_latency_s",.01),("sustained_payload_Bps",1),("sustained_transactions_per_s",1),("outstanding",1)]:
            self.set_memory("private_memory",k,v)
        r=self.row()
        self.assertEqual(r["traffic"]["SP_port_B"],31477376)
        self.assertIsNone(r["private_service"]["required_payload_Bps"])
        self.assertIsNone(r["private_service"]["required_transactions_per_s"])
        self.assertIsNone(r["private_service"]["rejected"])
        self.assertNotIn("finite_SP_credit",r["resource_floors_cycles"])
        self.assertNotIn("bank_balanced_SP",r["resource_floors_cycles"])
        self.assertFalse(any(x.startswith("private_")for x in r["rejections"]))

    def test_dataset_and_backing_have_independent_credit_bounds(self):
        self.tiered();self.set_memory("external_memory","response_latency_s",.01)
        p=self.d["physical"]["unknown"]
        p["external_classes"]={"dataset":self.class_contract(1e-9),"scratchpad_backing":self.class_contract(.01,outstanding=1)}
        r=self.row();classes=r["external_service"]["classes"]
        self.assertEqual(classes["dataset"]["necessary_outstanding_average"],17)
        self.assertNotIn("causal_credit_capacity",classes["dataset"]["failures"])
        self.assertIn("causal_credit_capacity",classes["scratchpad_backing"]["failures"])
        self.assertIn("external_scratchpad_backing_causal_credit_capacity",r["rejections"])

    def test_residence_witness_reprovisions_engines_and_costs(self):
        a=self.d["architectures"][0];a["contexts_per_engine"]=4;a["full_hash_residence_cycles"]=40000000
        p=self.d["physical"]["unknown"];p["logic_source_id"]="protocol_assumptions"
        p["unit_leakage_W"]={k:0 for k in M.SERVICES}
        p["logic_base_leakage_W_per_engine"]=.001;p["aux_leakage_W_per_context"]=.0001
        r=self.row()
        self.assertEqual(r["target_engine_minimum_or_planning_count"],5000)
        self.assertEqual(r["provisioned_contexts"],20000)
        self.assertEqual(r["target_resource_instance_counts"]["integer64"],10000)
        self.assertEqual(r["external_service"]["dataset_only_credit_upper_limit"],40000)
        self.assertAlmostEqual(r["cost"]["wall"]["known_DC_contribution_W"],7)

    def bounded_profile(self):
        p=self.zero_energy_fixture();p["static_dc_W"]["auxiliary_dc"]=2500
        p["technology"]="synthetic-node";p["corner"]="synthetic-PVT";p["logic_source_id"]="synthetic_scope"
        self.d["sources"]["synthetic_scope"]={"kind":"assumed","technology":p["technology"],"corner":p["corner"]}
        p["applicability"]={"mode":"bounded","frequency_Hz":[1e9],"placements":["all_local"],
            "technology":p["technology"],"corner":p["corner"],"source_id":"synthetic_scope"}
        return p

    def test_frequency_profile_is_not_extrapolated(self):
        self.bounded_profile();r=self.row()
        self.assertFalse(r["physical_profile_application"]["matched"])
        self.assertIsNone(r["cost"]["wall"]["wall_power_w"])
        self.assertNotIn("strict_wall_limit",r["rejections"])
        self.d["scenarios"][0]["frequency_Hz"]=1e9;r=self.row()
        self.assertTrue(r["physical_profile_application"]["matched"])
        self.assertIn("strict_wall_limit",r["rejections"])

    def test_traffic_profile_is_not_extrapolated(self):
        self.bounded_profile();self.d["scenarios"][0]["frequency_Hz"]=1e9;self.tiered()
        r=self.row()
        self.assertFalse(r["physical_profile_application"]["matched"])
        self.assertIsNone(r["cost"]["wall"]["wall_power_w"])

    def test_baseline_is_explicitly_unqualified_sensitivity(self):
        r=self.row()
        self.assertEqual(r["physical_profile_application"]["mode"],"unqualified_sensitivity_only")
        self.assertFalse(r["physical_profile_application"]["physical_extrapolation_qualified"])

    def test_profile_PVT_fingerprint_must_match(self):
        p=self.bounded_profile();p["applicability"]["corner"]="different-PVT"
        with self.assertRaisesRegex(ValueError,"applicability PVT/source mismatch"):
            self.row()

    def test_class_energy_does_not_use_mixed_aggregate_coefficient(self):
        self.tiered();p=self.d["physical"]["unknown"]
        p["external_classes"]={"dataset":self.class_contract(1e-9),"scratchpad_backing":self.class_contract(1e-6)}
        for name,read,write in [("dataset",1,0),("scratchpad_backing",2,3)]:
            m=p["external_classes"][name]
            for key,val in [("read_energy_pJ",read),("write_energy_pJ",write)]:
                m[key]=val;m["parameter_sources"][key]="protocol_assumptions"
        self.set_memory("external_memory","read_energy_pJ",9999)
        self.set_memory("external_memory","write_energy_pJ",9999)
        r=self.row();s=self.d["samples"][0]
        self.assertAlmostEqual(r["cost"]["wall"]["known_DC_contribution_W"],
            (16384+2*s["tier_read64"]+3*s["tier_write64"])*1e-6)

    def test_memory_operating_points_cannot_be_silently_joined(self):
        m=self.d["physical"]["unknown"]["private_memory"]
        m.update(technology="7nm",corner="0.75V/125C",source_ids=["hot","cold"])
        self.d["sources"]["hot"]={"kind":"measured","technology":"7nm","corner":"0.75V/125C"}
        self.d["sources"]["cold"]={"kind":"measured","technology":"7nm","corner":"0.75V/25C"}
        m["parameter_sources"]={"transaction_B":"hot","read_energy_pJ":"cold"}
        m["read_energy_pJ"]=5.8
        with self.assertRaisesRegex(ValueError,"incompatible memory operating point"):
            self.row()

    def test_memory_width_energy_units_are_bound(self):
        self.d["physical"]["unknown"]["private_memory"]["transaction_B"]=64
        with self.assertRaisesRegex(ValueError,"transaction width"):
            self.row()

    def test_unbound_measured_corner_stays_a_separate_anchor(self):
        m=self.d["physical"]["unknown"]["private_memory"]
        self.d["sources"]["unbound"]={"kind":"measured","technology":None,"corner":None}
        m["source_ids"].append("unbound");m["read_energy_pJ"]=5.8
        m["parameter_sources"]["read_energy_pJ"]="unbound"
        with self.assertRaisesRegex(ValueError,"unbound physical corner"):
            self.row()

    def test_strict_wall_limit_and_conversion_applied_once(self):
        p=self.zero_energy_fixture();p["static_dc_W"]["auxiliary_dc"]=2250;p["psu_efficiency"]=.9
        r=self.row()
        self.assertEqual(r["cost"]["wall"]["wall_power_w"],2500)
        self.assertIn("strict_wall_limit",r["rejections"])
        self.assertFalse(r["demonstrated_hardware_feasibility"])

    def test_partial_known_power_can_reject_while_total_stays_unknown(self):
        p=self.d["physical"]["unknown"]
        p["static_dc_W"]["auxiliary_dc"]=2500
        r=self.row()
        self.assertIsNone(r["cost"]["wall"]["wall_power_w"])
        self.assertIn("known_DC_contribution_exceeds_strict_wall_limit",r["rejections"])

    def test_instance_and_context_leakage_are_charged_once(self):
        p=self.d["physical"]["unknown"];p["logic_source_id"]="protocol_assumptions"
        p["unit_leakage_W"]={k:0 for k in M.SERVICES}
        p["logic_base_leakage_W_per_engine"]=.001;p["aux_leakage_W_per_context"]=.0001
        one=self.row();self.d["architectures"][0]["contexts_per_engine"]=4;four=self.row()
        engines=one["target_engine_minimum_or_planning_count"]
        self.assertAlmostEqual(one["cost"]["wall"]["known_DC_contribution_W"],engines*.0011)
        self.assertAlmostEqual(four["cost"]["wall"]["known_DC_contribution_W"],engines*.0014)

    def test_zero_write_activity_does_not_require_invented_write_energy(self):
        p=self.zero_energy_fixture();p["external_memory"]["write_energy_pJ"]=None
        r=self.row()
        self.assertEqual(r["traffic"]["external_write64"],0)
        self.assertEqual(r["cost"]["wall"]["wall_power_w"],0)
        self.assertFalse(r["demonstrated_hardware_feasibility"])

    def test_area_anchor_does_not_supply_logic_or_multiport_aux_area(self):
        r=self.row()
        self.assertGreater(r["bare_capacity_area_anchors_mm2"]["Yokoyama7nm-area-only"],0)
        self.assertIsNone(r["cost"]["area_mm2"])
        self.assertIn("private_aux",r["cost"]["area_unknown"])
        self.assertIsNone(r["cost"]["chip_count_area_only_floor"])

    def test_digest_nonce_and_baseline_rejections(self):
        original=copy.deepcopy(self.d)
        for change in ("digest","nonce","v1"):
            self.d=copy.deepcopy(original)
            if change=="digest":self.d["samples"][0]["digest_hex"]="G"*64
            elif change=="nonce":self.d["samples"][0]["nonce"]=2
            else:self.d["baseline"]["v1_regression_scope"]=""
            with self.subTest(change=change),self.assertRaises(ValueError):self.row()

    def test_negative_boolean_and_nonfinite_inputs_rejected(self):
        for value in (-1,True,float("nan"),float("inf")):
            with self.subTest(value=value),self.assertRaises(ValueError):
                M.number(value,"directed")
        with self.assertRaisesRegex(ValueError,"duplicate"):
            M.strict_json('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            M.strict_json('{"a":NaN}')

    def test_cli_complete_output_bound_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"input.json";out=Path(tmp)/"result.json"
            src.write_text(json.dumps(self.d))
            with patch.object(M,"OUTPUT_CAP",1),self.assertRaisesRegex(ValueError,"output exceeds cap"):
                M.main(["--input",str(src),"--output",str(out)])
            self.assertFalse(out.exists())
            with contextlib.redirect_stdout(io.StringIO()):
                M.main(["--input",str(src),"--output",str(out)])
            content=out.read_bytes()
            with self.assertRaises(FileExistsError):M.main(["--input",str(src),"--output",str(out)])
            self.assertEqual(out.read_bytes(),content)

    def test_cli_bad_source_pin_fails_before_output(self):
        self.d["sources"]["native"]["sha256"]="0"*64
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"input.json";out=Path(tmp)/"result.json";src.write_text(json.dumps(self.d))
            with self.assertRaisesRegex(ValueError,"source binding mismatch"):
                M.main(["--input",str(src),"--output",str(out),"--verify-sources"])
            self.assertFalse(out.exists())

    def test_workload_projection_cannot_change_under_unchanged_source_pins(self):
        self.d["samples"][0]["work"]["mul64"]+=1
        with self.assertRaisesRegex(ValueError,"primitive-work projection"):
            M.verify_sources(self.d)


if __name__=="__main__":
    unittest.main()
