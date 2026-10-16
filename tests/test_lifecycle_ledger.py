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
            'scratchpad_bytes': 2097152, 'dataset_logical_bytes': 64,
            'program_image_load_bytes': 3072, 'untimed_provider_device_cycles': None,
            'physical_port_read_bytes': 2097280, 'physical_port_write_bus_bytes': 2097280,
            'strobed_write_bytes': 2097280, 'logical_bytecode_memory_bytes': 16,
            'logical_entry_bytes': 128, 'logical_tail_bytes': 128}
        self.provider = {'provider_device_cycles': None, 'dataset_requests': 1,
            'program_generations': 1, 'cache_bytes': 268435456,
            'logical_dataset_bytes': 2181038016, 'materialized_dataset_bytes': 0}

    def check(self):
        driver.validate_ledger(self.ledger, self.provider, 1, 1)

    def test_closing_partition(self):
        self.check()

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


if __name__ == '__main__':
    unittest.main()
