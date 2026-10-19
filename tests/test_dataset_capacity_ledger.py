"""Tiny synthetic capacity ledgers; no native generation, HDL tools or writes.

The two rows are in-memory test inputs, not new execution evidence. Independent
constants pin the accepted cache0 work and the public software baseline, so a
coherently altered pair cannot redefine the expected cost.
"""
import copy
import hashlib
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from test_dataset_capacity import compare_ideal_profiles, validate_dataset


NATIVE_INSTRUCTIONS = 3563
NATIVE_MULTIPLIES = 1254
IDEAL_EXECUTOR = 3 * NATIVE_INSTRUCTIONS + 34 * NATIVE_MULTIPLIES
IDEAL_CORE = IDEAL_EXECUTOR + 74
IDEAL_SESSION = IDEAL_CORE + 1
BASELINE_PATH = 'docs/validation/dataset-lifecycle-20261018/bounded-results.json'
SOFTWARE_STAGES = {
    'control_and_metadata': 8, 'execution': 4995, 'finalization': 393286,
    'held_return': 1, 'initialization_hardware_fill': 131074, 'input_hash': 30,
    'interprogram_seed': 60, 'program_generation': 1606, 'program_preparation': 3322,
}
SOFTWARE_NESTED = {
    'executor': 4935, 'finalization': 393286, 'initial_fill': 131074,
    'input_hash': 30, 'iteration': 4995, 'program_generation': 1606,
}
NATIVE_DIGEST = 'ffbc66a37af9b4f986492b464e92ec15e24157b29cf8e470e44d03eab7d3c8c1'


def outer_ledger(availability):
    stages = dict(SOFTWARE_STAGES)
    stages['execution'] += availability
    return {
        'cycles': sum(stages.values()), 'stage_cycles': stages,
        'nested_reply_waits': {'dataset': 2 + availability},
        'nested_executor_phases': [0, 3, 4932],
        'nested_initialization': {'provider_wait': 0, 'fill_phases': [1, 131072, 1]},
        'nested_input_hash_phases': [1, 28, 1],
        'nested_program_generation_phases': [4, 1600, 2],
        'nested_finalization_phases': [1, 393284, 1],
        'nested_iteration_phases': [2, stages['execution'] - 4, 2],
    }


def dataset_fixture(stalled=False):
    """Native address inputs stay independent of the measured CSV rows."""
    native_items = [('0000000038a2aa80', '11' * 64),
                    ('000000000f7cf3c0', '22' * 64)]
    rows = []
    for index, (address, _) in enumerate(native_items):
        instruction_extra = (13, 7)[index] if stalled else 0
        cache_extra = (5, 11)[index] if stalled else 0
        executor = IDEAL_EXECUTOR + instruction_extra
        core = executor + 74 + cache_extra
        session = core + 1
        rows.append({
            'tag': f'{0x10001 + index:08x}', 'address': address,
            'image_epoch': '4ca3', 'item_namespace': f'{index + 1:08x}',
            'item_cycles': str(session), 'core_cycles': str(core),
            'executor_cycles': str(executor), 'session_launch_extra': '1',
            'stages': '8', 'retired': str(NATIVE_INSTRUCTIONS),
            'muls': str(NATIVE_MULTIPLIES),
            'instruction_service_extra': str(instruction_extra),
            'cache_service_extra': str(cache_extra),
            'request_to_first_response': str(session),
        })
    availability = sum(int(row['item_cycles']) for row in rows)
    core = sum(int(row['core_cycles']) for row in rows)
    executor = sum(int(row['executor_cycles']) for row in rows)
    program_extra = sum(int(row['instruction_service_extra']) for row in rows)
    cache_extra = sum(int(row['cache_service_extra']) for row in rows)
    ledger = outer_ledger(availability)
    dataset = {
        'schema': 'openrx.dataset-capacity.nested-ledger.v1',
        'hardware_dataset': 1, 'outer_cycles': ledger['cycles'],
        'dataset_costs_are_nested_not_added_to_outer_total': True,
        'all_descriptors_captured': True,
        'full_native_digest_registers_scratchpad': True,
        'physical_cache_service': None,
        'demands': 2, 'responses': 2, 'live_native_dataset_calls': 0,
        'items': 2, 'item_returns': 2, 'stages': 16,
        'retirements': 2 * NATIVE_INSTRUCTIONS,
        'item_availability_clocks': availability,
        'core_item_availability_clocks': core, 'session_launch_extra_clocks': 2,
        'executor_clocks': executor, 'ideal_executor_clocks_each': IDEAL_EXECUTOR,
        'program_service_extra_clocks': program_extra,
        'cache_service_extra_clocks': cache_extra,
        'cache_requests': 16, 'cache_responses': 16,
        'instruction_requests': 2 * NATIVE_INSTRUCTIONS,
        'instruction_responses': 2 * NATIVE_INSTRUCTIONS,
        'stale_packets_drained': 1 if stalled else 0,
        'cache_request_stalls': 3 if stalled else 0,
        'instruction_request_stalls': 2 if stalled else 0,
        'service_phase_cycles': [4993, availability + 2, 0],
        'session_phase_cycles': [4993, 2, availability],
        'item_phase_cycles': [0, 2, 66, 16, 106666 + program_extra,
                              16 + cache_extra, 16, 16, 2],
        'captured_asset_epoch': 0x4ca3,
        'session_namespace_bits': 32, 'external_tag_bits': 64, 'sessions_used': 2,
    }
    return dataset, ledger, rows, native_items


def baseline_fixture():
    """Only public baseline fields consumed by the comparison are needed."""
    return {
        'schema': 'openrx.dataset-lifecycle.bounded-results.v1',
        'normal_profiles': {'software-dataset-ideal': {
            'stage_cycles': dict(SOFTWARE_STAGES),
            'nested_phase_sums': dict(SOFTWARE_NESTED),
            'total_modeled_clocks': 534382, 'stage_sum': 534382,
            'dataset_reply_wait_clocks': 2,
            'full_native_registers_2MiB_scratchpad_digest_equal': True,
        }},
        'native_reference': {'digest32_hex': NATIVE_DIGEST},
    }


def ideal_profile():
    dataset, ledger, _, _ = dataset_fixture()
    return {'ledger': ledger, 'dataset': dataset,
            'actual_digest_sha256': hashlib.sha256((NATIVE_DIGEST + '\n').encode()).hexdigest()}


class DatasetCapacityLedger(unittest.TestCase):
    def check(self, fixture, stalled=False):
        return validate_dataset(*fixture, stalled=stalled)

    def test_valid_ideal_separates_private_core_and_session_launch(self):
        self.assertEqual((IDEAL_EXECUTOR, IDEAL_CORE, IDEAL_SESSION), (53325, 53399, 53400))
        fixture = dataset_fixture()
        self.assertEqual(fixture[0]['core_item_availability_clocks'], 106798)
        self.assertEqual(fixture[0]['item_availability_clocks'], 106800)
        self.assertEqual(fixture[1]['cycles'], 641182)
        self.assertIsNone(self.check(fixture))

    def test_valid_stalled_keeps_launch_extra_distinct_from_service_extras(self):
        fixture = dataset_fixture(stalled=True)
        self.assertEqual(fixture[0]['program_service_extra_clocks'], 20)
        self.assertEqual(fixture[0]['cache_service_extra_clocks'], 16)
        self.assertEqual(fixture[0]['session_launch_extra_clocks'], 2)
        self.assertIsNone(self.check(fixture, stalled=True))

    def test_rejects_stale_pre_capacity_schema(self):
        fixture = dataset_fixture()
        fixture[0]['schema'] = 'openrx.dataset-lifecycle.nested-ledger.v1'
        with self.assertRaises(AssertionError):
            self.check(fixture)

    def test_rejects_coherently_reused_private_core_timing_as_session_timing(self):
        fixture = dataset_fixture()
        dataset, _, rows, _ = fixture
        for row in rows:
            row['item_cycles'] = row['request_to_first_response'] = row['core_cycles']
            row['session_launch_extra'] = '0'
        dataset['item_availability_clocks'] = 106798
        dataset['session_launch_extra_clocks'] = 0
        ledger = outer_ledger(106798)
        dataset['outer_cycles'] = ledger['cycles']
        dataset['service_phase_cycles'] = [4993, 106800, 0]
        dataset['session_phase_cycles'] = [4993, 2, 106798]
        with self.assertRaises(AssertionError):
            self.check((dataset, ledger, rows, fixture[3]))

    def test_rejects_each_mutated_per_return_timing_field(self):
        for field in ('item_cycles', 'core_cycles', 'executor_cycles',
                      'session_launch_extra', 'instruction_service_extra',
                      'cache_service_extra', 'request_to_first_response'):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[2][0][field] = str(int(fixture[2][0][field]) + 1)
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_each_mutated_per_return_work_count(self):
        for field in ('stages', 'retired', 'muls'):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[2][1][field] = str(int(fixture[2][1][field]) - 1)
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_mutated_aggregate_counts_and_clocks(self):
        for field in ('demands', 'responses', 'items', 'item_returns', 'stages',
                      'retirements', 'cache_requests', 'cache_responses',
                      'instruction_requests', 'instruction_responses', 'sessions_used',
                      'ideal_executor_clocks_each', 'item_availability_clocks',
                      'core_item_availability_clocks', 'session_launch_extra_clocks',
                      'executor_clocks', 'program_service_extra_clocks', 'cache_service_extra_clocks'):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[0][field] += 1
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_negative_boolean_or_float_counters(self):
        for field in ('item_availability_clocks', 'core_item_availability_clocks',
                      'session_launch_extra_clocks', 'executor_clocks', 'sessions_used'):
            for kind in ('negative', 'boolean', 'float'):
                with self.subTest(field=field, kind=kind):
                    fixture = dataset_fixture()
                    old = fixture[0][field]
                    fixture[0][field] = -1 if kind == 'negative' else True if kind == 'boolean' else float(old)
                    with self.assertRaises(AssertionError):
                        self.check(fixture)

    def test_rejects_phase_shape_type_and_nesting_mutations(self):
        for field, size in (('service_phase_cycles', 3), ('session_phase_cycles', 3),
                            ('item_phase_cycles', 9)):
            for kind in ('short', 'long', 'negative', 'boolean', 'float', 'outside-execution'):
                with self.subTest(field=field, kind=kind):
                    fixture = dataset_fixture()
                    values = fixture[0][field]
                    if kind == 'short':
                        values.pop()
                    elif kind == 'long':
                        values.append(0)
                    elif kind == 'negative':
                        values[0] = -1
                    elif kind == 'boolean':
                        values[0] = False
                    elif kind == 'float':
                        values[0] = float(values[0])
                    else:
                        fixture[0][field] = [fixture[1]['stage_cycles']['execution'] + 1] + [0] * (size - 1)
                    with self.assertRaises(AssertionError):
                        self.check(fixture)

    def test_rejects_wrong_launch_phase_even_when_session_phase_sum_still_closes(self):
        fixture = dataset_fixture()
        fixture[0]['session_phase_cycles'][0] -= 1
        fixture[0]['session_phase_cycles'][1] += 1
        with self.assertRaises(AssertionError):
            self.check(fixture)

    def test_rejects_outer_cycle_or_nesting_claim_mutations(self):
        for field, value in (('outer_cycles', 0),
                             ('dataset_costs_are_nested_not_added_to_outer_total', False),
                             ('all_descriptors_captured', False),
                             ('full_native_digest_registers_scratchpad', False),
                             ('physical_cache_service', 0)):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[0][field] = value
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_software_or_live_native_provider_claims(self):
        for field, value in (('hardware_dataset', 0), ('live_native_dataset_calls', 2)):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[0][field] = value
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_wrong_address_in_measured_or_independent_native_row(self):
        for native in (False, True):
            with self.subTest(native=native):
                fixture = dataset_fixture()
                if native:
                    fixture[3][1] = ('000000000f7cf400', fixture[3][1][1])
                else:
                    fixture[2][0]['address'] = '0000000038a2aac0'
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_missing_or_extra_measured_or_native_rows(self):
        for index in (2, 3):
            for extra in (False, True):
                with self.subTest(index=index, extra=extra):
                    fixture = dataset_fixture()
                    if extra:
                        fixture[index].append(copy.deepcopy(fixture[index][0]))
                    else:
                        fixture[index].pop()
                    with self.assertRaises(AssertionError):
                        self.check(fixture)

    def test_rejects_wrong_duplicate_or_wide_caller_tags(self):
        for value in ('00010001', '00000002', '00010003', '00020002', '100000002'):
            with self.subTest(tag=value):
                fixture = dataset_fixture()
                fixture[2][1]['tag'] = value
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_zero_duplicate_skipped_reordered_or_wide_namespaces(self):
        for namespaces in (('0', '2'), ('1', '1'), ('1', '3'), ('2', '1'), ('1', '100000002')):
            with self.subTest(namespaces=namespaces):
                fixture = dataset_fixture()
                for row, namespace in zip(fixture[2], namespaces):
                    row['item_namespace'] = namespace
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_skipped_namespace_with_coherently_rebound_session_count(self):
        fixture = dataset_fixture()
        fixture[2][1]['item_namespace'] = '3'
        fixture[0]['sessions_used'] = 3
        with self.assertRaises(AssertionError):
            self.check(fixture)

    def test_rejects_stale_or_short_namespace_and_external_tag_widths(self):
        for field, value in (('session_namespace_bits', 16), ('external_tag_bits', 32)):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[0][field] = value
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_row_epoch_or_coherently_rebound_stale_epoch(self):
        for coherent in (False, True):
            with self.subTest(coherent=coherent):
                fixture = dataset_fixture()
                fixture[2][0]['image_epoch'] = '4ca4'
                if coherent:
                    fixture[0]['captured_asset_epoch'] = 0x4ca4
                    fixture[2][1]['image_epoch'] = '4ca4'
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_negative_row_counters(self):
        for field in ('core_cycles', 'session_launch_extra', 'instruction_service_extra', 'cache_service_extra'):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[2][0][field] = '-1'
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_malformed_csv_numeric_or_hex_fields(self):
        for field, value in (('core_cycles', 'not-a-number'), ('item_cycles', '53400.0'),
                             ('tag', 'not-hex'), ('item_namespace', 'not-hex'),
                             ('image_epoch', 'not-hex'), ('address', 'not-hex')):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[2][0][field] = value
                with self.assertRaises(ValueError):
                    self.check(fixture)

    def test_rejects_stalled_profile_without_each_observed_stall_witness(self):
        for field in ('program_service_extra_clocks', 'cache_service_extra_clocks',
                      'stale_packets_drained', 'cache_request_stalls', 'instruction_request_stalls'):
            with self.subTest(field=field):
                fixture = dataset_fixture(stalled=True)
                fixture[0][field] = 0
                with self.assertRaises(AssertionError):
                    self.check(fixture, stalled=True)


class PublicBaselineClockClosure(unittest.TestCase):
    def test_valid_default_public_baseline_has_exact_execution_only_delta(self):
        profile = ideal_profile()
        self.assertEqual(len(profile['ledger']['stage_cycles']), 9)
        self.assertEqual(profile['ledger']['cycles'], 641182)
        self.assertEqual(compare_ideal_profiles(profile), {
            'public_baseline': BASELINE_PATH,
            'outer_cycle_delta': 106800, 'execution_cycle_delta': 106800,
            'dataset_reply_wait_delta': 106800,
            'other_stage_clocks_equal': True, 'non_dataset_nested_sums_equal': True,
            'native_digest_equal': True, 'nested_costs_added_twice': False,
        })

    def test_valid_explicit_public_baseline(self):
        self.assertEqual(compare_ideal_profiles(ideal_profile(), baseline_fixture())['outer_cycle_delta'], 106800)

    def test_rejects_independently_corrupted_cycle_execution_reply_or_availability(self):
        for field in ('cycles', 'execution', 'reply', 'availability'):
            with self.subTest(field=field):
                profile = ideal_profile()
                if field == 'cycles':
                    profile['ledger']['cycles'] += 1
                elif field == 'execution':
                    profile['ledger']['stage_cycles']['execution'] += 1
                elif field == 'reply':
                    profile['ledger']['nested_reply_waits']['dataset'] += 1
                else:
                    profile['dataset']['item_availability_clocks'] += 1
                with self.assertRaises(AssertionError):
                    compare_ideal_profiles(profile, baseline_fixture())

    def test_rejects_coherent_dataset_inflation_and_double_addition(self):
        for extra in (1, 106800):
            with self.subTest(extra=extra):
                profile = ideal_profile()
                ledger, dataset = profile['ledger'], profile['dataset']
                ledger['cycles'] += extra
                ledger['stage_cycles']['execution'] += extra
                ledger['nested_reply_waits']['dataset'] += extra
                ledger['nested_iteration_phases'][1] += extra
                for field in ('item_availability_clocks', 'core_item_availability_clocks',
                              'executor_clocks', 'program_service_extra_clocks'):
                    dataset[field] += extra
                with self.assertRaises(AssertionError):
                    compare_ideal_profiles(profile, baseline_fixture())

    def test_rejects_each_nonexecution_partition_shift_with_unchanged_total(self):
        for stage in SOFTWARE_STAGES:
            if stage == 'execution':
                continue
            with self.subTest(stage=stage):
                profile = ideal_profile()
                profile['ledger']['stage_cycles'][stage] += 1
                profile['ledger']['stage_cycles']['execution'] -= 1
                with self.assertRaises(AssertionError):
                    compare_ideal_profiles(profile, baseline_fixture())

    def test_rejects_missing_or_extra_hardware_partition_even_with_same_sum(self):
        for extra in (False, True):
            with self.subTest(extra=extra):
                profile = ideal_profile()
                stages = profile['ledger']['stage_cycles']
                if extra:
                    stages['unaccounted_fabric'] = 0
                else:
                    stages['execution'] += stages.pop('control_and_metadata')
                with self.assertRaises(AssertionError):
                    compare_ideal_profiles(profile, baseline_fixture())

    def test_rejects_each_changed_non_dataset_nested_sum(self):
        for key in ('nested_executor_phases', 'nested_finalization_phases',
                    'nested_input_hash_phases', 'nested_program_generation_phases',
                    'nested_iteration_phases', 'nested_initialization'):
            with self.subTest(key=key):
                profile = ideal_profile()
                value = profile['ledger'][key]
                if key == 'nested_initialization':
                    value['fill_phases'][0] += 1
                else:
                    value[0] += 1
                with self.assertRaises(AssertionError):
                    compare_ideal_profiles(profile, baseline_fixture())

    def test_rejects_hidden_native_initialization_wait(self):
        profile = ideal_profile()
        profile['ledger']['nested_initialization']['provider_wait'] = 1
        with self.assertRaises(AssertionError):
            compare_ideal_profiles(profile, baseline_fixture())

    def test_rejects_different_actual_digest(self):
        profile = ideal_profile()
        profile['actual_digest_sha256'] = 'cd' * 32
        with self.assertRaises(AssertionError):
            compare_ideal_profiles(profile, baseline_fixture())

    def test_rejects_coherently_inflated_software_baseline_and_hardware_pair(self):
        baseline = baseline_fixture()
        software = baseline['normal_profiles']['software-dataset-ideal']
        profile = ideal_profile()
        software['stage_cycles']['finalization'] += 1
        software['nested_phase_sums']['finalization'] += 1
        software['total_modeled_clocks'] += 1
        software['stage_sum'] += 1
        profile['ledger']['stage_cycles']['finalization'] += 1
        profile['ledger']['nested_finalization_phases'][1] += 1
        profile['ledger']['cycles'] += 1
        with self.assertRaises(AssertionError):
            compare_ideal_profiles(profile, baseline)

    def test_rejects_coherent_baseline_partition_redistribution_with_fixed_total(self):
        baseline = baseline_fixture()
        stages = baseline['normal_profiles']['software-dataset-ideal']['stage_cycles']
        profile = ideal_profile()
        for target in (stages, profile['ledger']['stage_cycles']):
            target['control_and_metadata'] += 1
            target['finalization'] -= 1
        with self.assertRaises(AssertionError):
            compare_ideal_profiles(profile, baseline)

    def test_rejects_coherently_changed_baseline_and_hardware_nested_work(self):
        baseline = baseline_fixture()
        baseline['normal_profiles']['software-dataset-ideal']['nested_phase_sums']['executor'] += 1
        profile = ideal_profile()
        profile['ledger']['nested_executor_phases'][0] += 1
        with self.assertRaises(AssertionError):
            compare_ideal_profiles(profile, baseline)

    def test_rejects_missing_or_extra_public_baseline_partition(self):
        for extra in (False, True):
            with self.subTest(extra=extra):
                baseline = baseline_fixture()
                stages = baseline['normal_profiles']['software-dataset-ideal']['stage_cycles']
                if extra:
                    stages['unaccounted_fabric'] = 0
                else:
                    stages['execution'] += stages.pop('held_return')
                with self.assertRaises(AssertionError):
                    compare_ideal_profiles(ideal_profile(), baseline)

    def test_rejects_stale_baseline_schema_total_wait_or_native_claim(self):
        for field in ('schema', 'total', 'wait', 'native'):
            with self.subTest(field=field):
                baseline = baseline_fixture()
                software = baseline['normal_profiles']['software-dataset-ideal']
                if field == 'schema':
                    baseline['schema'] = 'openrx.dataset-capacity.nested-ledger.v1'
                elif field == 'total':
                    software['total_modeled_clocks'] = software['stage_sum'] = 534383
                elif field == 'wait':
                    software['dataset_reply_wait_clocks'] = 3
                else:
                    software['full_native_registers_2MiB_scratchpad_digest_equal'] = False
                with self.assertRaises(AssertionError):
                    compare_ideal_profiles(ideal_profile(), baseline)


if __name__ == '__main__':
    unittest.main()
