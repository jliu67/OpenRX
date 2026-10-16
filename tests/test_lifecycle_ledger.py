"""Reject nonclosing/ambiguous device clocks and invented provider costs."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('lifecycle_driver', ROOT / 'scripts/test_prepared_hash_lifecycle.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.ledger = {'cycles': 100, 'stage_cycles': {'initialization_transport': 20,
            'control_and_metadata': 2, 'program_preparation': 10, 'execution': 30,
            'interprogram_seed': 10, 'finalization': 28, 'held_return': 0},
            'nested_iteration_phases': [30] + [0] * 11,
            'nested_finalization_phases': [28] + [0] * 5,
            'nested_executor_phases': [0] * 18,
            'preparation_reciprocals': 0, 'runtime_reciprocals': 0,
            'scratchpad_bytes': 2097152, 'dataset_logical_bytes': 64,
            'program_image_load_bytes': 3072, 'untimed_provider_device_cycles': None,
            'physical_port_read_bytes': 2097280, 'physical_port_write_bus_bytes': 2097280,
            'strobed_write_bytes': 2097280, 'logical_bytecode_memory_bytes': 16,
            'logical_entry_bytes': 128, 'logical_tail_bytes': 128}
        self.provider = {'provider_device_cycles': None, 'dataset_requests': 1,
            'program_generations': 1, 'cache_bytes': 268435456,
            'logical_dataset_bytes': 2181038016, 'materialized_dataset_bytes': 0}
        self.native = {'static_active_reciprocals': 0, 'dynamic_active_reciprocals': 0, 'bytecode_events': 2}

    def check(self):
        driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1)

    def test_closing_partition(self):
        self.check()

    def hardware_fill(self):
        self.ledger['stage_cycles']['initialization_hardware_fill'] = self.ledger['stage_cycles'].pop('initialization_transport')
        self.ledger['hardware_fill_enabled'] = True
        self.ledger['nested_initialization'] = {'provider_wait': 2, 'fill_phases': [1, 16, 1]}
        self.provider.update(input_hash_calls=1, software_fill_provider_calls=0, initialization_host_seconds=0)

    def test_hardware_fill_replaces_existing_initialization_stage(self):
        self.hardware_fill()
        driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True)

    def test_hardware_fill_cannot_double_count_old_transport(self):
        self.hardware_fill()
        self.ledger['stage_cycles']['initialization_transport'] = 20
        self.ledger['cycles'] += 20
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True)

    def test_hardware_fill_cannot_use_host_fill_as_live_provider(self):
        self.hardware_fill()
        self.provider['software_fill_provider_calls'] = 1
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True)

    def test_hardware_fill_nested_cycles_must_close(self):
        self.hardware_fill()
        self.ledger['nested_initialization']['fill_phases'][1] += 1
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True)

    def hardware_program(self):
        self.ledger['cycles'] += 802
        self.ledger['stage_cycles']['program_generation'] = 802
        self.ledger.update(hardware_program_enabled=True,
            nested_program_generation_phases=[2, 799, 1], program_generation_output_bytes=3200,
            program_image_storage_bytes=3200, program_image_transport='internal_generated_buffer')
        self.provider.update(program_generations=0, program_generation_host_seconds=0,
                             assertion_only_program_generations=1)

    def test_hardware_program_partition_and_assertion_only_oracle(self):
        self.hardware_program()
        driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, False, True)

    def test_hardware_program_cannot_hide_live_host_generation(self):
        self.hardware_program()
        self.provider['program_generations'] = 1
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, False, True)

    def test_hardware_program_nested_generation_must_close(self):
        self.hardware_program()
        self.ledger['nested_program_generation_phases'][1] += 1
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, False, True)

    def test_hardware_program_requires_full_entropy_and_instructions(self):
        self.hardware_program()
        self.ledger['program_generation_output_bytes'] = 3072
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, False, True)

    def test_hardware_program_cache_load_is_internal_transport(self):
        self.hardware_program()
        self.ledger['program_image_transport'] = 'external_provider'
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, False, True)

    def test_hardware_program_and_initial_fill_have_distinct_partitions(self):
        self.hardware_fill()
        self.hardware_program()
        driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True, True)

    def hardware_input_hash(self):
        self.hardware_fill()
        self.ledger['stage_cycles']['initialization_hardware_fill'] -= 2
        self.ledger['nested_initialization']['provider_wait'] = 0
        self.ledger['cycles'] += 28
        self.ledger['stage_cycles']['input_hash'] = 30
        self.ledger.update(hardware_input_hash_enabled=True, nested_input_hash_phases=[1, 28, 1],
            input_hash_bytes=80, removed_initialization_replies_drained=0, removed_initialization_writes_drained=0)
        self.provider.update(input_hash_calls=0, input_hash_host_seconds=0, assertion_only_input_hash_calls=1)

    def test_hardware_input_hash_has_disjoint_device_partition(self):
        self.hardware_input_hash()
        driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True, False, True, 80)

    def test_hardware_input_hash_cannot_use_live_host_hash(self):
        self.hardware_input_hash()
        self.provider['input_hash_calls'] = 1
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True, False, True, 80)

    def test_hardware_input_hash_requires_independent_oracle(self):
        self.hardware_input_hash()
        self.provider['assertion_only_input_hash_calls'] = 0
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True, False, True, 80)

    def test_hardware_input_hash_cycles_must_close(self):
        self.hardware_input_hash()
        self.ledger['nested_input_hash_phases'][1] += 1
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True, False, True, 80)

    def test_hardware_input_hash_length_must_match_request(self):
        self.hardware_input_hash()
        self.ledger['input_hash_bytes'] = 79
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True, False, True, 80)

    def test_hardware_input_hash_does_not_double_count_provider_wait(self):
        self.hardware_input_hash()
        self.ledger['nested_initialization']['provider_wait'] = 2
        self.ledger['stage_cycles']['initialization_hardware_fill'] += 2
        self.ledger['cycles'] += 2
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True, False, True, 80)

    def test_all_three_hardware_stages_have_distinct_partitions(self):
        self.hardware_input_hash()
        self.hardware_program()
        driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 1, True, True, True, 80)

    def test_stalls_cannot_be_added_as_an_outer_stage(self):
        self.ledger['stage_cycles']['memory_stall'] = 4
        self.ledger['cycles'] += 4
        with self.assertRaises(AssertionError):
            self.check()

    def test_nonclosing_outer_partition(self):
        self.ledger['cycles'] += 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_nonclosing_nested_partition(self):
        self.ledger['nested_iteration_phases'][0] += 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_negative_or_fractional_cycles_rejected(self):
        for value in (-1, 0.5, True):
            with self.subTest(value=value):
                saved = copy.deepcopy(self.ledger)
                self.ledger['stage_cycles']['held_return'] = value
                with self.assertRaises(AssertionError):
                    self.check()
                self.ledger = saved

    def test_provider_seconds_cannot_become_device_cycles(self):
        self.provider['provider_device_cycles'] = 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_logical_dataset_size_is_not_materialized_bytes(self):
        self.provider['materialized_dataset_bytes'] = self.provider['logical_dataset_bytes']
        with self.assertRaises(AssertionError):
            self.check()

    def test_useful_bytes_cannot_exceed_bus_traffic(self):
        self.ledger['strobed_write_bytes'] += 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_native_work_counts_must_match(self):
        self.provider['dataset_requests'] += 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_partial_beat_traffic_rejected(self):
        self.ledger['physical_port_read_bytes'] += 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_nonclosing_executor_partition(self):
        self.ledger['nested_executor_phases'][0] = 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_missing_positive_preparation_work(self):
        self.native['static_active_reciprocals'] = 2
        with self.assertRaises(AssertionError):
            self.check()

    def test_missing_positive_runtime_work(self):
        self.native['dynamic_active_reciprocals'] = 2
        with self.assertRaises(AssertionError):
            driver.validate_ledger(self.ledger, self.provider, 1, 1, self.native, 0)

    def test_logical_bytecode_bytes_require_native_events(self):
        self.ledger['logical_bytecode_memory_bytes'] += 8
        with self.assertRaises(AssertionError):
            self.check()


class PairedCycleTest(unittest.TestCase):
    def setUp(self):
        fixture = LedgerTest()
        fixture.setUp()
        self.baseline = fixture.ledger
        self.baseline['nested_iteration_phases'] = [0] * 7 + [30] + [0] * 4
        self.baseline['nested_executor_phases'] = [0] * 18
        self.baseline['nested_executor_phases'][3] = 18
        self.baseline['nested_executor_phases'][12:14] = [3, 9]
        self.baseline['runtime_reciprocals'] = 3
        self.prepared = copy.deepcopy(self.baseline)
        self.prepared['cycles'] -= 8
        self.prepared['stage_cycles']['program_preparation'] += 4
        self.prepared['stage_cycles']['execution'] -= 12
        self.prepared['nested_iteration_phases'][7] -= 12
        self.prepared['nested_executor_phases'][12:14] = [0, 0]
        self.prepared['preparation_reciprocals'] = 1
        self.prepared['runtime_reciprocals'] = 0
        self.native = {'static_active_reciprocals': 1, 'dynamic_active_reciprocals': 3}

    def check(self):
        return driver.compare_variants(self.baseline, self.prepared, self.native)

    def test_observed_reciprocal_cycle_equations(self):
        result = self.check()
        self.assertEqual(result['measured_reciprocal_cycles_each'], 4)
        self.assertEqual(result['net_saved_cycles'], 8)

    def test_hidden_common_stage_change_rejected(self):
        self.prepared['stage_cycles']['finalization'] += 1
        self.prepared['cycles'] += 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_unrelated_executor_saving_rejected(self):
        self.prepared['nested_executor_phases'][3] -= 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_uncharged_preparation_rejected(self):
        self.prepared['stage_cycles']['program_preparation'] -= 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_fractional_reciprocal_latency_rejected(self):
        self.baseline['nested_executor_phases'][13] += 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_wrong_positive_count_rejected(self):
        self.prepared['preparation_reciprocals'] = 2
        with self.assertRaises(AssertionError):
            self.check()


if __name__ == '__main__':
    unittest.main()
