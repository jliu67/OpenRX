"""Guards against misleading paired-stage/per-hash performance accounting."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('cycle_model', Path(__file__).resolve().parents[1] /
                                             'scripts/reciprocal_cycle_model.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def pair(static=2, dynamic=8):
    base = {k: 0 for k in (*model.PHASES, *model.COMMON, *model.WAIT_OBSERVERS)}
    base.update(prepared=0, stall=0, control=1, admissions=2, iterations=8, reloads=2,
                program_reads=512, retirements=2048, dynamic_rcp=dynamic + 2,
                dynamic_active_rcp=dynamic, dynamic_nop_rcp=2,
                static_rcp=static + 2, static_active_rcp=static,
                preparation_rcp_requests=0, runtime_rcp_requests=dynamic,
                preparation_clocks=20, preparation_response_clocks=12,
                kernel_clocks=100 + 66 * dynamic, entry_clocks=80, dataset_clocks=16,
                tail_clocks=96, return_clocks=32, control_clocks=11, outside_clocks=3,
                full_hash_measured=0)
    base.update({f'prep_s{i}': 20 if i == 2 else 0 for i in range(6)})
    base.update({f'ex_s{i}': (100 if i == 3 else dynamic if i == 12 else
                             65 * dynamic if i == 13 else 0) for i in range(18)})
    new = copy.deepcopy(base)
    new.update(prepared=1, preparation_rcp_requests=static, runtime_rcp_requests=0,
               preparation_clocks=20 + 66 * static, kernel_clocks=100,
               prep_s3=static, prep_s4=65 * static, ex_s12=0, ex_s13=0)
    for row in (base, new):
        row['execution_clocks'] = sum(row[k] for k in model.PHASES)
        row['elapsed_cycles'] = row['preparation_clocks'] + row['execution_clocks'] + 14
    return base, new


class CycleModelTests(unittest.TestCase):
    def test_charges_preparation_and_calibrates_actual_occupancy(self):
        result = model.compare(*pair(), 2)
        self.assertEqual(result['preparation_added_clocks'], 132)
        self.assertEqual(result['kernel_saved_clocks'], 528)
        self.assertEqual(result['net_stage_saved_clocks'], 396)
        self.assertEqual(result['measured_active_rcp_clocks_each'], 66)
        self.assertFalse(result['full_hash_performance_accepted'])

    def test_no_amortization_can_cost_more(self):
        result = model.compare(*pair(static=8, dynamic=2), 8)
        self.assertEqual(result['net_stage_saved_clocks'], -396)

    def test_rejects_unequal_workload_or_memory_profile(self):
        for key in ('retirements', 'program_reads', 'stall', 'dynamic_active_rcp'):
            baseline, prepared = pair()
            prepared[key] += 1
            with self.assertRaises(ValueError):
                model.compare(baseline, prepared, 2)

    def test_rejects_nonclosing_outer_or_nested_ledger(self):
        for key in ('elapsed_cycles', 'execution_clocks', 'prep_s2', 'ex_s3'):
            baseline, prepared = pair()
            baseline[key] += 1
            with self.assertRaises(ValueError):
                model.compare(baseline, prepared, 2)

    def test_rejects_runtime_recalculation_and_missing_admission_charge(self):
        for key in ('runtime_rcp_requests', 'reloads', 'preparation_rcp_requests'):
            baseline, prepared = pair()
            prepared[key] += 1
            with self.assertRaises(ValueError):
                model.compare(baseline, prepared, 2)

    def test_wait_observers_are_never_added_again(self):
        baseline, prepared = pair()
        baseline['sp_reply_wait'] = prepared['sp_reply_wait'] = 70
        result = model.compare(baseline, prepared, 2)
        self.assertEqual(result['net_stage_saved_clocks'], 396)

    def test_missing_pipeline_stage_cost_remains_unknown(self):
        components = {'connected_complete_pipeline_measured': False,
                      'missing_stages_or_calibration': [{'stage': 'initial hash', 'clocks': None}],
                      'draft_component_evidence': []}
        self.assertIsNone(model.pipeline_context(components)['complete_pipeline_clocks'])
        self.assertIsNone(model.pipeline_context(components)['full_hash_speedup'])
        for invalid in (0, 56):
            components['missing_stages_or_calibration'][0]['clocks'] = invalid
            with self.assertRaises(ValueError):
                model.pipeline_context(components)

    def test_component_measurement_cannot_certify_a_pipeline(self):
        with self.assertRaises(ValueError):
            model.pipeline_context({'connected_complete_pipeline_measured': True})


if __name__ == '__main__':
    unittest.main()
