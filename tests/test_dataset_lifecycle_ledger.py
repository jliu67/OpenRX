"""Small synthetic ledger checks; no native generation, simulation or source writes.

Addresses and native item words below are test inputs, not an execution result.
The fixed cache0 program counts exercise the real validator's modeled-clock
identity while each fixture contains only two in-memory per-return rows.
"""
import copy
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from test_dataset_hash_lifecycle import compare_ideal_profiles, validate_dataset


NATIVE_INSTRUCTIONS = 3563
NATIVE_MULTIPLIES = 1254
IDEAL_EXECUTOR = 3 * NATIVE_INSTRUCTIONS + 34 * NATIVE_MULTIPLIES
IDEAL_ITEM = IDEAL_EXECUTOR + 74


def dataset_fixture(hardware=True, stalled=False):
    """Keep observed rows separate from their independent native addresses."""
    native_items = [('0000000001000040', '11' * 64),
                    ('000000007fffffc0', '22' * 64)]
    rows = []
    for index, (address, _) in enumerate(native_items):
        instruction_extra = (13, 7)[index] if stalled else 0
        cache_extra = (5, 11)[index] if stalled else 0
        executor = IDEAL_EXECUTOR + instruction_extra
        item = executor + 74 + cache_extra
        rows.append({'tag': f'{0x00010000 + index:08x}', 'address': address,
                     'image_epoch': '002a', 'item_cycles': str(item),
                     'executor_cycles': str(executor), 'stages': '8',
                     'retired': str(NATIVE_INSTRUCTIONS), 'muls': str(NATIVE_MULTIPLIES),
                     'instruction_service_extra': str(instruction_extra),
                     'cache_service_extra': str(cache_extra),
                     'request_to_first_response': str(item)})
    item_clocks = sum(int(row['item_cycles']) for row in rows)
    executor_clocks = sum(int(row['executor_cycles']) for row in rows)
    execution = item_clocks + 102
    ledger = {'cycles': execution + 100,
              'stage_cycles': {'execution': execution, 'other': 100}}
    dataset = {'schema': 'openrx.dataset-lifecycle.nested-ledger.v1',
        'hardware_dataset': hardware, 'outer_cycles': ledger['cycles'],
        'dataset_costs_are_nested_not_added_to_outer_total': True,
        'all_descriptors_captured': True, 'full_native_digest_registers_scratchpad': True,
        'physical_cache_service': None, 'demands': 2, 'responses': 2,
        'live_native_dataset_calls': 0 if hardware else 2,
        'items': 2, 'item_returns': 2, 'stages': 16,
        'retirements': 2 * NATIVE_INSTRUCTIONS,
        'item_availability_clocks': item_clocks, 'executor_clocks': executor_clocks,
        'ideal_executor_clocks_each': IDEAL_EXECUTOR,
        'program_service_extra_clocks': 20 if stalled else 0,
        'cache_service_extra_clocks': 16 if stalled else 0,
        'cache_requests': 16, 'cache_responses': 16,
        'instruction_requests': 2 * NATIVE_INSTRUCTIONS,
        'instruction_responses': 2 * NATIVE_INSTRUCTIONS,
        'stale_packets_drained': 1 if stalled else 0,
        'cache_request_stalls': 3 if stalled else 0,
        'instruction_request_stalls': 2 if stalled else 0,
        'service_phase_cycles': [2, 100, item_clocks],
        'item_phase_cycles': [0, 0, 0, 0, item_clocks, 0, 0, 0, 0],
        'captured_asset_epoch': 42}
    if not hardware:
        for name in ('items', 'item_returns', 'stages', 'retirements',
                     'item_availability_clocks', 'executor_clocks',
                     'program_service_extra_clocks', 'cache_service_extra_clocks',
                     'cache_requests', 'cache_responses', 'instruction_requests',
                     'instruction_responses', 'stale_packets_drained',
                     'cache_request_stalls', 'instruction_request_stalls'):
            dataset[name] = 0
        dataset['service_phase_cycles'] = [0] * 3
        dataset['item_phase_cycles'] = [0] * 9
        rows = []
    return dataset, ledger, rows, native_items


def paired_fixture():
    """An outer ledger pair with dataset work charged exactly once."""
    software = {'cycles': 1355,
        'stage_cycles': {'control': 5, 'input_hash': 30,
                         'initialization_hardware_fill': 100,
                         'program_generation': 20, 'execution': 1000,
                         'finalization': 200},
        'nested_reply_waits': {'dataset': 2},
        'nested_executor_phases': [0, 3, 4],
        'nested_initialization': {'provider_wait': 0, 'fill_phases': [0, 1, 2]},
        'nested_input_hash_phases': [0, 28, 2],
        'nested_program_generation_phases': [0, 18, 2],
        'nested_finalization_phases': [0, 199, 1]}
    hardware = copy.deepcopy(software)
    delta = 2 * IDEAL_ITEM
    hardware['cycles'] += delta
    hardware['stage_cycles']['execution'] += delta
    hardware['nested_reply_waits']['dataset'] += delta
    return {'software-dataset-ideal': {'ledger': software, 'actual_digest_sha256': 'ab' * 32},
            'hardware-dataset-ideal': {'ledger': hardware, 'dataset': {'item_availability_clocks': delta},
                                       'actual_digest_sha256': 'ab' * 32}}


class DatasetLedger(unittest.TestCase):
    def check(self, fixture, hardware=True, stalled=False):
        return validate_dataset(*fixture, hardware=hardware, stalled=stalled)

    def test_valid_ideal_uses_exact_native_program_counts(self):
        self.assertEqual((IDEAL_EXECUTOR, IDEAL_ITEM), (53325, 53399))
        self.assertIsNone(self.check(dataset_fixture()))

    def test_valid_stalled_separates_program_and_cache_extra_clocks(self):
        self.assertIsNone(self.check(dataset_fixture(stalled=True), stalled=True))

    def test_valid_software_has_no_hardware_item_rows(self):
        self.assertIsNone(self.check(dataset_fixture(hardware=False), hardware=False))

    def test_rejects_mutated_per_return_timing(self):
        for field in ('executor_cycles', 'item_cycles', 'request_to_first_response',
                      'instruction_service_extra', 'cache_service_extra'):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[2][0][field] = str(int(fixture[2][0][field]) + 1)
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_mutated_per_return_instruction_counts(self):
        for field in ('stages', 'retired', 'muls'):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[2][1][field] = str(int(fixture[2][1][field]) - 1)
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_mutated_aggregate_counts_and_clocks(self):
        for field in ('demands', 'responses', 'items', 'item_returns', 'stages',
                      'retirements', 'cache_requests', 'cache_responses',
                      'instruction_requests', 'instruction_responses',
                      'ideal_executor_clocks_each', 'item_availability_clocks',
                      'executor_clocks', 'program_service_extra_clocks',
                      'cache_service_extra_clocks'):
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[0][field] += 1
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_invalid_nested_phase_counts(self):
        mutations = [('service_phase_cycles', [2, 101, 2 * IDEAL_ITEM]),
                     ('item_phase_cycles', [2 * IDEAL_ITEM + 103] + [0] * 8),
                     ('service_phase_cycles', [-1, 103, 2 * IDEAL_ITEM]),
                     ('item_phase_cycles', [0] * 8)]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                fixture = dataset_fixture()
                fixture[0][field] = value
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_outer_or_double_added_nesting_claims(self):
        for field, value in [('outer_cycles', 0),
                             ('dataset_costs_are_nested_not_added_to_outer_total', False)]:
            with self.subTest(field=field):
                fixture = dataset_fixture()
                fixture[0][field] = value
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_wrong_measured_or_native_address(self):
        fixture = dataset_fixture()
        fixture[2][0]['address'] = '0000000001000080'
        with self.assertRaises(AssertionError):
            self.check(fixture)
        fixture = dataset_fixture()
        fixture[3][1] = ('000000007fffff80', fixture[3][1][1])
        with self.assertRaises(AssertionError):
            self.check(fixture)

    def test_rejects_duplicate_or_missing_generation_tag(self):
        for value in ('00010000', '00000001'):
            with self.subTest(tag=value):
                fixture = dataset_fixture()
                fixture[2][1]['tag'] = value
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_wrong_captured_asset_epoch(self):
        fixture = dataset_fixture()
        fixture[2][0]['image_epoch'] = '002b'
        with self.assertRaises(AssertionError):
            self.check(fixture)

    def test_rejects_extra_measured_or_native_gold_rows(self):
        for index in (2, 3):
            with self.subTest(extra='measured' if index == 2 else 'native'):
                fixture = dataset_fixture()
                fixture[index].append(copy.deepcopy(fixture[index][0]))
                with self.assertRaises(AssertionError):
                    self.check(fixture)

    def test_rejects_stalled_profile_without_measured_stalls(self):
        for field in ('program_service_extra_clocks', 'cache_service_extra_clocks',
                      'stale_packets_drained', 'cache_request_stalls',
                      'instruction_request_stalls'):
            with self.subTest(field=field):
                fixture = dataset_fixture(stalled=True)
                fixture[0][field] = 0
                with self.assertRaises(AssertionError):
                    self.check(fixture, stalled=True)

    def test_rejects_live_native_provider_in_hardware_profile(self):
        fixture = dataset_fixture()
        fixture[0]['live_native_dataset_calls'] = 2
        with self.assertRaises(AssertionError):
            self.check(fixture)


class PairedIdealProfiles(unittest.TestCase):
    def test_valid_pair_charges_dataset_delta_once(self):
        self.assertEqual(compare_ideal_profiles(paired_fixture()), {
            'outer_cycle_delta': 106798, 'execution_cycle_delta': 106798,
            'dataset_reply_wait_delta': 106798, 'other_stage_clocks_equal': True,
            'native_digest_equal': True, 'nested_costs_added_twice': False})

    def test_rejects_corrupt_outer_execution_or_reply_delta(self):
        for mutation in ('outer', 'execution', 'reply', 'double-added', 'coherent-double-added'):
            with self.subTest(mutation=mutation):
                profiles = paired_fixture()
                hardware = profiles['hardware-dataset-ideal']['ledger']
                if mutation == 'outer':
                    hardware['cycles'] += 1
                elif mutation == 'execution':
                    hardware['stage_cycles']['execution'] += 1
                elif mutation == 'reply':
                    hardware['nested_reply_waits']['dataset'] += 1
                else:
                    hardware['cycles'] += 2 * IDEAL_ITEM
                    hardware['stage_cycles']['execution'] += 2 * IDEAL_ITEM
                    if mutation == 'coherent-double-added':
                        hardware['nested_reply_waits']['dataset'] += 2 * IDEAL_ITEM
                with self.assertRaises(AssertionError):
                    compare_ideal_profiles(profiles)

    def test_rejects_mutated_measured_availability(self):
        profiles = paired_fixture()
        profiles['hardware-dataset-ideal']['dataset']['item_availability_clocks'] += 1
        with self.assertRaises(AssertionError):
            compare_ideal_profiles(profiles)

    def test_rejects_nonexecution_stage_shift_even_with_equal_total(self):
        profiles = paired_fixture()
        hardware = profiles['hardware-dataset-ideal']['ledger']
        hardware['stage_cycles']['finalization'] += 1
        hardware['stage_cycles']['execution'] -= 1
        with self.assertRaises(AssertionError):
            compare_ideal_profiles(profiles)

    def test_rejects_changes_to_unchanged_nested_work(self):
        for key in ('nested_executor_phases', 'nested_initialization',
                    'nested_input_hash_phases', 'nested_program_generation_phases',
                    'nested_finalization_phases'):
            with self.subTest(key=key):
                profiles = paired_fixture()
                value = profiles['hardware-dataset-ideal']['ledger'][key]
                if isinstance(value, list):
                    value[0] += 1
                else:
                    value['provider_wait'] += 1
                with self.assertRaises(AssertionError):
                    compare_ideal_profiles(profiles)

    def test_rejects_different_actual_digest(self):
        profiles = paired_fixture()
        profiles['hardware-dataset-ideal']['actual_digest_sha256'] = 'cd' * 32
        with self.assertRaises(AssertionError):
            compare_ideal_profiles(profiles)

    def test_rejects_nonpositive_delta(self):
        profiles = paired_fixture()
        profiles['hardware-dataset-ideal']['ledger'] = copy.deepcopy(
            profiles['software-dataset-ideal']['ledger'])
        with self.assertRaises(AssertionError):
            compare_ideal_profiles(profiles)


if __name__ == '__main__':
    unittest.main()
