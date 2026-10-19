"""Synthetic full-size accounting and prepared-input substitution checks only.

No HDL compilation, native/reference workload or accepted fixture generation.
The repeated placeholder addresses/data intentionally are not RandomX gold.
"""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import test_dataset_fullhash as full


def accounting():
    n = full.ITEMS
    native = {'bytecode_events': 1, 'static_active_reciprocals': 1}
    dataset_cycles = n * 53400
    execution = dataset_cycles + n
    stage = {'execution': execution, 'finalization': 2, 'input_hash': 3,
        'program_generation': 4, 'initialization_hardware_fill': 5}
    ledger = {'hardware_fill_enabled': True, 'hardware_program_enabled': True,
        'hardware_input_hash_enabled': True, 'cycles': sum(stage.values()), 'stage_cycles': stage,
        'nested_iteration_phases': [execution] + [0] * 11,
        'nested_finalization_phases': [2], 'nested_input_hash_phases': [3],
        'nested_program_generation_phases': [4], 'nested_executor_phases': [0],
        'nested_initialization': {'provider_wait': 0, 'fill_phases': [5]},
        'scratchpad_bytes': 2097152, 'dataset_logical_bytes': n * 64,
        'logical_entry_bytes': n * 128, 'logical_tail_bytes': n * 128,
        'program_image_load_bytes': 8 * 384 * 8, 'logical_bytecode_memory_bytes': 8,
        'preparation_reciprocals': 1, 'runtime_reciprocals': 0, 'untimed_provider_device_cycles': None,
        'nested_reply_waits': {'dataset': execution}}
    provider = {key: 0 for key in ('input_hash_calls', 'software_fill_provider_calls', 'program_generations',
        'dataset_requests', 'assertion_only_dataset_requests', 'argon_initializations',
        'native_cache_program_generations', 'cache_image_export_bytes', 'cache_initialization_host_seconds')}
    provider.update({'cache_key_hex': '74657374206b657920303030', 'assertion_only_input_hash_calls': 1,
        'assertion_only_program_generations': 8, 'cache_bytes': 268435456, 'materialized_dataset_bytes': 0,
        'logical_dataset_bytes': 2181038016, 'provider_device_cycles': None})
    dataset = {'schema': 'openrx.dataset-capacity.nested-ledger.v1', 'hardware_dataset': 1,
        'outer_cycles': ledger['cycles'], 'dataset_costs_are_nested_not_added_to_outer_total': True,
        'all_descriptors_captured': True, 'full_native_digest_registers_scratchpad': True,
        'physical_cache_service': None, 'session_namespace_bits': 32, 'external_tag_bits': 64,
        'captured_asset_epoch': 0x4ca3, 'live_native_dataset_calls': 0,
        'ideal_executor_clocks_each': 53325, 'item_availability_clocks': dataset_cycles,
        'core_item_availability_clocks': n * 53399, 'executor_clocks': n * 53325,
        'session_launch_extra_clocks': n, 'service_phase_cycles': [execution, 0, 0],
        'session_phase_cycles': [execution - n, n, 0], 'item_phase_cycles': [0] * 9}
    for key in ('demands', 'responses', 'items', 'item_returns', 'sessions_used'): dataset[key] = n
    for key in ('stages', 'cache_requests', 'cache_responses'): dataset[key] = n * 8
    for key in ('retirements', 'instruction_requests', 'instruction_responses'): dataset[key] = n * 3563
    for key in ('program_service_extra_clocks', 'cache_service_extra_clocks', 'stale_packets_drained',
        'cache_request_stalls', 'instruction_request_stalls'): dataset[key] = 0
    rows = [{'tag': f'{0x10000 + i:x}', 'item_namespace': f'{i:x}', 'image_epoch': '4ca3', 'address': '0',
        'stages': '8', 'retired': '3563', 'muls': '1254', 'executor_cycles': '53325',
        'instruction_service_extra': '0', 'core_cycles': '53399', 'cache_service_extra': '0',
        'session_launch_extra': '1', 'item_cycles': '53400', 'request_to_first_response': '53400'}
        for i in range(1, n + 1)]
    items = [['0000000000000000', '0' * 128] for _ in range(n)]
    return ledger, dataset, provider, native, rows, items


class FullAccounting(unittest.TestCase):
    def setUp(self): self.values = accounting()

    def test_full_counts_and_disjoint_clocks_close(self):
        result = full.validate_full_ledgers(*self.values)
        self.assertEqual(result['dataset_item_availability_clocks'], 874905600)
        self.assertFalse(result['physical_service_or_PPA_validated'])

    def test_protocol_capacity_counts_are_insufficient(self):
        self.values[1]['retirements'] = 32768
        with self.assertRaises(AssertionError): full.validate_full_ledgers(*self.values)

    def test_missing_last_item_rejects(self):
        self.values[4].pop()
        with self.assertRaises(AssertionError): full.validate_full_ledgers(*self.values)

    def test_mutated_native_address_rejects(self):
        self.values[5][-1][0] = '0000000000000040'
        with self.assertRaises(AssertionError): full.validate_full_ledgers(*self.values)

    def test_recycled_session_rejects(self):
        self.values[4][-1]['item_namespace'] = '1'
        with self.assertRaises(AssertionError): full.validate_full_ledgers(*self.values)

    def test_mutated_item_clock_rejects(self):
        self.values[4][-1]['item_cycles'] = '53401'
        with self.assertRaises(AssertionError): full.validate_full_ledgers(*self.values)

    def test_double_added_dataset_clocks_rejects(self):
        self.values[0]['cycles'] += 874905600
        self.values[1]['outer_cycles'] += 874905600
        with self.assertRaises(AssertionError): full.validate_full_ledgers(*self.values)

    def test_live_software_dataset_rejects(self):
        self.values[2]['dataset_requests'] = 16384
        with self.assertRaises(AssertionError): full.validate_full_ledgers(*self.values)

    def test_missing_program_assertion_rejects(self):
        self.values[2]['assertion_only_program_generations'] = 7
        with self.assertRaises(AssertionError): full.validate_full_ledgers(*self.values)

    def test_physical_service_claim_rejects(self):
        self.values[1]['physical_cache_service'] = 'validated'
        with self.assertRaises(AssertionError): full.validate_full_ledgers(*self.values)


class PreparedInputIdentity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fullhash-prepared-identity-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'obj-fullhash').mkdir(); (self.root / 'native-reference').mkdir()
        (self.root / 'obj-fullhash/sim').write_bytes(b'not a simulator\n')
        (self.root / 'native-reference/synthetic.hex').write_bytes(b'not reference gold\n')
        self.sources = {'synthetic-source': {'bytes': 1, 'sha256': '0' * 64}}
        self.message = b'input'
        commands = [{'label': label, 'returncode': 0, 'wall_timeout': False,
            'group_empty_after_cleanup': True, 'argv': []} for label in
            ('fullhash-unit', 'compile-full-reference', 'native-full-reference', 'compile-fullhash')]
        commands[2]['argv'] = [str(self.root / 'reference'), str(self.root / 'native-reference'), '8', '2048', '1', self.message.hex()]
        full.save(self.root / 'commands.json', commands)
        self.manifest = {'schema': full.PREPARED_SCHEMA, 'status': 'prepared_not_executed',
            'source_inputs': self.sources, 'source_tree': '1' * 40, 'input_hex': self.message.hex(),
            'programs': 8, 'iterations': 2048, 'parameters': full.parameters(),
            'files': {name: full.identity(self.root / name) for name in
                ('obj-fullhash/sim', 'native-reference/synthetic.hex')},
            'commands_identity': full.identity(self.root / 'commands.json'), 'commands': commands}
        self.write_manifest()
        self.gold_check = patch.object(full, 'validate_reference', return_value=None)
        self.gold_check.start(); self.addCleanup(self.gold_check.stop)
        self.git_check = patch.object(full.subprocess, 'check_output', return_value='1' * 40 + '\n')
        self.git_check.start(); self.addCleanup(self.git_check.stop)

    def write_manifest(self):
        full.save(self.root / 'prepared-manifest.json', self.manifest)
        self.pin = full.sha(self.root / 'prepared-manifest.json')

    def verify(self): return full.verify_prepared(self.root, self.pin, self.sources, self.message)

    def test_exact_pinned_inputs(self): self.verify()

    def test_rebound_embedded_claim_without_external_pin_rejects(self):
        self.manifest['source_tree'] = '2' * 40
        full.save(self.root / 'prepared-manifest.json', self.manifest)
        with self.assertRaises(AssertionError): self.verify()

    def test_mutated_binary_rejects_stale_hash(self):
        (self.root / 'obj-fullhash/sim').write_bytes(b'changed\n')
        with self.assertRaises(AssertionError): self.verify()

    def test_mutated_gold_rejects_stale_hash(self):
        (self.root / 'native-reference/synthetic.hex').write_bytes(b'changed\n')
        with self.assertRaises(AssertionError): self.verify()

    def test_changed_current_source_rejects(self):
        self.sources = copy.deepcopy(self.sources); self.sources['synthetic-source']['bytes'] += 1
        with self.assertRaises(AssertionError): self.verify()

    def test_symlink_binary_rejects(self):
        path = self.root / 'obj-fullhash/sim'; path.rename(path.with_suffix('.original'))
        path.symlink_to(path.with_suffix('.original'))
        with self.assertRaises(AssertionError): self.verify()

    def test_unrecorded_gold_rejects(self):
        (self.root / 'native-reference/extra').write_text('extra')
        with self.assertRaises(AssertionError): self.verify()

    def test_mutated_command_ledger_rejects(self):
        full.save(self.root / 'commands.json', [])
        with self.assertRaises(AssertionError): self.verify()

    def test_rebound_failed_command_rejects(self):
        self.manifest['commands'][-1]['wall_timeout'] = True
        full.save(self.root / 'commands.json', self.manifest['commands'])
        self.manifest['commands_identity'] = full.identity(self.root / 'commands.json'); self.write_manifest()
        with self.assertRaises(AssertionError): self.verify()


class Bounds(unittest.TestCase):
    def test_combined_prepare_and_full_run_rejects(self):
        with self.assertRaises(AssertionError): full.validate_mode(False, None, None, 100)

    def test_prepare_only_is_separate(self): full.validate_mode(True, None, None, None)

    def test_full_reuse_needs_external_manifest_pin(self):
        with self.assertRaises(AssertionError): full.validate_mode(False, Path('/tmp/prepared'), None, 100)

    def test_preparation_cannot_be_reused_as_prepare_only(self):
        with self.assertRaises(AssertionError): full.validate_mode(True, Path('/tmp/prepared'), 'a' * 64, None)

    def test_full_run_needs_positive_wall_budget(self):
        with self.assertRaises(AssertionError): full.validate_mode(False, Path('/tmp/prepared'), 'a' * 64, 0)

    def test_watchdog_over_signed_counter_budget_rejects(self):
        with self.assertRaises(AssertionError): full.parameters(2147483648)

    def test_trace_and_progress_are_bounded(self):
        values = full.parameters()
        self.assertEqual(values['EVENT_TRACE'], 1)
        self.assertGreater(values['WATCHDOG_CYCLES'], 874905600)
        self.assertLess(values['WATCHDOG_CYCLES'], 2147483647)
        self.assertEqual(full.ITEMS % values['PROGRESS_ITEMS'], 0)

    def test_traversal_into_source_rejects(self):
        with tempfile.TemporaryDirectory(prefix='fullhash-output-guard-') as value:
            base = Path(value); source = base / 'source'; sibling = base / 'sibling'
            source.mkdir(); sibling.mkdir()
            with self.assertRaises(AssertionError):
                full.fresh_output(sibling / '..' / 'source' / 'new-output', source)

    def test_symlink_ancestor_into_source_rejects(self):
        with tempfile.TemporaryDirectory(prefix='fullhash-output-guard-') as value:
            base = Path(value); source = base / 'source'; source.mkdir()
            alias = base / 'source-alias'; alias.symlink_to(source, target_is_directory=True)
            with self.assertRaises(AssertionError): full.fresh_output(alias / 'new-output', source)

    def test_existing_original_output_rejects(self):
        with tempfile.TemporaryDirectory(prefix='fullhash-output-guard-') as value:
            base = Path(value); source = base / 'source'; output = base / 'output'
            source.mkdir(); output.mkdir()
            with self.assertRaises(AssertionError): full.fresh_output(output, source)

    def test_fresh_sibling_output_is_allowed(self):
        with tempfile.TemporaryDirectory(prefix='fullhash-output-guard-') as value:
            base = Path(value); source = base / 'source'; source.mkdir()
            self.assertEqual(full.fresh_output(base / 'output', source), base / 'output')


if __name__ == '__main__': unittest.main()
