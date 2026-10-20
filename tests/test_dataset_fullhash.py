"""Synthetic full-size accounting and prepared-input substitution checks only.

No HDL compilation, native/reference workload or accepted fixture generation.
The repeated placeholder addresses/data intentionally are not RandomX gold.
"""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
# unittest discovery already owns the name "test_dataset_fullhash" for this
# file. Load the driver by its exact path under a distinct module identity.
_driver_spec = importlib.util.spec_from_file_location(
    'openrx_dataset_fullhash_driver_under_test',
    Path(__file__).resolve().parents[1] / 'scripts/test_dataset_fullhash.py')
assert _driver_spec is not None and _driver_spec.loader is not None
full = importlib.util.module_from_spec(_driver_spec)
sys.modules[_driver_spec.name] = full
_driver_spec.loader.exec_module(full)


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

    def test_missing_dataset_phase_ledger_rejects(self):
        del self.values[1]['item_phase_cycles']
        with self.assertRaises(KeyError): full.validate_full_ledgers(*self.values)


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


class RetainedReferenceAndRebuiltIdentity(unittest.TestCase):
    """Tiny synthetic provenance files; never compile or generate native gold.

    Reference semantics have their own validator. Here it is mocked so every
    rejection exercises actual file, source, command, receipt or copy binding.
    """
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fullhash-rebuilt-identity-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.old = self.base / 'original-execution' / 'output'
        self.new = self.base / 'rebuilt-execution' / 'output'
        self.message = b'synthetic input'
        for root in (self.old, self.new):
            (root / 'obj-fullhash').mkdir(parents=True)
            (root / 'native-reference').mkdir()
        self.gold_names = [
            'accesses.hex', 'dataset-items.hex', 'dataset-native-host-time.json', 'events.mem',
            *[f'final-{i}.hex' for i in range(8)], 'final-a.hex', 'final-digest32.hex',
            'final-rf.hex', 'full-reference.json', 'initial.hex', 'iterations.hex',
            'iterations.mem', 'metadata.hex', 'metadata.mem', 'oracle-summary.json',
            *[f'program-{i}.mem' for i in range(8)], 'program-registers.hex', 'sequence_sizes.vh']
        for name in self.gold_names:
            value = ('synthetic reference placeholder: ' + name + '\n').encode()
            for root in (self.old, self.new):
                (root / 'native-reference' / name).write_bytes(value)
        (self.old / 'obj-fullhash/sim').write_bytes(b'original synthetic model\n')
        (self.new / 'obj-fullhash/sim').write_bytes(b'corrected synthetic model\n')
        self.provenance_names = ['reference', 'extraction.json', 'program-extraction.json',
            'pinned_iteration.inc', 'pinned_dataset_read.inc', 'pinned_destructor.inc',
            'pinned_bytecode_loop.inc', 'pinned_scratchpad_address.inc', 'pinned_float_masks.inc',
            'pinned_program_initialize.inc', 'pinned_program_float_helpers.inc']
        for name in self.provenance_names:
            (self.old / name).write_text('synthetic native provenance: ' + name + '\n')
        self.old_sources = {name: {'bytes': 1, 'sha256': '0' * 64} for name in
            [full.BENCH, 'scripts/test_dataset_fullhash.py', 'tests/test_dataset_fullhash.py',
             'native-generation-dependency.hpp']}
        self.sources = copy.deepcopy(self.old_sources)
        for name in full.REFERENCE_REUSE_CHANGES:
            self.sources[name] = {'bytes': 2, 'sha256': '1' * 64}
        old_commands = self.commands(
            'fullhash-unit', 'compile-full-reference', 'native-full-reference', 'compile-fullhash')
        old_commands[2]['argv'] = [str(self.old / 'reference'), str(self.old / 'native-reference'),
            '8', '2048', '1', self.message.hex()]
        self.original = {'schema': full.PREPARED_SCHEMA, 'status': 'prepared_not_executed',
            'source_head': 'a' * 40, 'source_tree': '1' * 40,
            'source_inputs': self.old_sources, 'input_hex': self.message.hex(),
            'programs': 8, 'iterations': 2048, 'parameters': full.parameters(),
            'files': self.file_map(self.old), 'commands': old_commands,
            'native_archive_sha256': 'a' * 64, 'prepared_assets': {'synthetic-cache': {'bytes': 1}},
            'verilator_files': {'synthetic-tool': {'bytes': 1}}}
        self.receipt = {'schema': 'openrx.local.receipt.v1', 'execution_id': self.old.parent.name,
            'status': 'PROCESS_EXITED', 'scientific_acceptance': 'unverified',
            'process': {'returncode': 0}, 'artifacts': []}
        self.write_original()
        self.root_verify = self.base / 'original-root-verify.json'
        self.verified = {'execution_id': self.old.parent.name, 'status': 'PROCESS_EXITED',
            'integrity_verified': True, 'scientific_acceptance': 'unverified'}
        self.write_root_verify()
        self.rebuilt = copy.deepcopy(self.original)
        self.rebuilt.update({'schema': full.REBUILT_SCHEMA, 'source_head': 'b' * 40,
            'source_tree': '2' * 40, 'source_inputs': copy.deepcopy(self.sources),
            'files': self.file_map(self.new),
            'commands': self.commands('fullhash-unit', 'compile-fullhash'),
            'reused_reference': {'path': str(self.old), 'manifest_sha256': self.original_pin,
                'receipt_sha256': self.receipt_pin, 'root_verify': str(self.root_verify),
                'root_verify_sha256': self.root_pin}})
        self.write_rebuilt()
        self.reference_check = patch.object(full, 'validate_reference', return_value=None)
        self.reference_check.start(); self.addCleanup(self.reference_check.stop)
        self.git_check = patch.object(full.subprocess, 'check_output', return_value='2' * 40 + '\n')
        self.git_check.start(); self.addCleanup(self.git_check.stop)

    @staticmethod
    def commands(*labels):
        return [{'label': label, 'argv': [], 'returncode': 0, 'wall_timeout': False,
            'group_empty_after_cleanup': True} for label in labels]

    def file_map(self, root):
        names = ['obj-fullhash/sim', *['native-reference/' + name for name in self.gold_names]]
        return {name: full.identity(root / name) for name in names}

    def write_original(self):
        full.save(self.old / 'commands.json', self.original['commands'])
        self.original['commands_identity'] = full.identity(self.old / 'commands.json')
        full.save(self.old / 'prepared-manifest.json', self.original)
        self.original_pin = full.sha(self.old / 'prepared-manifest.json')
        self.write_receipt()

    def write_receipt(self):
        names = ['prepared-manifest.json', 'commands.json', *self.provenance_names,
                 *self.original['files']]
        self.receipt['artifacts'] = [{'path': str(self.old / name), **full.identity(self.old / name)}
            for name in names]
        full.save(self.old.parent / 'receipt.json', self.receipt)
        self.receipt_pin = full.sha(self.old.parent / 'receipt.json')

    def write_root_verify(self):
        full.save(self.root_verify, self.verified)
        self.root_pin = full.sha(self.root_verify)

    def write_rebuilt(self):
        full.save(self.new / 'commands.json', self.rebuilt['commands'])
        self.rebuilt['commands_identity'] = full.identity(self.new / 'commands.json')
        full.save(self.new / 'prepared-manifest.json', self.rebuilt)
        self.rebuilt_pin = full.sha(self.new / 'prepared-manifest.json')

    def verify_origin(self, sources=None):
        return full.verify_reference_preparation(self.old, self.original_pin, self.receipt_pin,
            self.root_verify, self.root_pin, self.sources if sources is None else sources, self.message)

    def verify_new(self):
        return full.verify_rebuilt(self.new, self.rebuilt_pin, self.sources, self.message)

    def test_exact_gold_origin_and_rebuilt_model_pass(self):
        self.assertEqual(len(self.gold_names), 32)
        self.assertEqual(self.verify_origin()['source_tree'], '1' * 40)
        self.assertEqual(self.verify_new()['source_tree'], '2' * 40)
        self.assertNotEqual(self.original['files']['obj-fullhash/sim'],
                            self.rebuilt['files']['obj-fullhash/sim'])

    def test_each_reviewed_source_change_is_allowed_for_gold_only(self):
        for name in sorted(full.REFERENCE_REUSE_CHANGES):
            with self.subTest(name=name):
                current = copy.deepcopy(self.old_sources)
                current[name]['bytes'] += 1
                self.verify_origin(current)

    def test_new_eof_regression_source_is_allowed_and_bound_to_rebuilt_model(self):
        self.sources['scripts/test_dataset_gold_eof.py'] = {'bytes': 3, 'sha256': '2' * 64}
        self.verify_origin()
        self.rebuilt['source_inputs'] = copy.deepcopy(self.sources)
        self.write_rebuilt()
        self.verify_new()
        self.sources['scripts/test_dataset_gold_eof.py']['bytes'] += 1
        with self.assertRaises(AssertionError): self.verify_new()

    def test_original_execution_verifier_stays_strict(self):
        with patch.object(full.subprocess, 'check_output', return_value='1' * 40 + '\n'):
            with self.assertRaises(AssertionError):
                full.verify_prepared(self.old, self.original_pin, self.sources, self.message)

    def test_changed_native_dependency_rejects(self):
        self.sources['native-generation-dependency.hpp']['bytes'] += 1
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_added_native_dependency_rejects(self):
        self.sources['new-dependency.hpp'] = {'bytes': 1, 'sha256': '0' * 64}
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_deleted_native_dependency_rejects(self):
        del self.sources['native-generation-dependency.hpp']
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_rebuilt_origin_cannot_be_used_as_original_generation(self):
        self.original['schema'] = full.REBUILT_SCHEMA
        self.write_original()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_original_manifest_external_pin_rejects_rebound_claim(self):
        self.original['source_tree'] = '3' * 40
        full.save(self.old / 'prepared-manifest.json', self.original)
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_wrong_receipt_pin_rejects(self):
        self.receipt_pin = '0' * 64
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_failed_receipt_rejects_even_with_fresh_pin(self):
        self.receipt['status'] = 'PROCESS_FAILED'
        self.write_receipt()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_nonzero_receipt_rejects_even_with_fresh_pin(self):
        self.receipt['process']['returncode'] = 1
        self.write_receipt()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_missing_receipt_rejects(self):
        (self.old.parent / 'receipt.json').unlink()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_receipt_must_bind_original_gold(self):
        self.receipt['artifacts'] = [row for row in self.receipt['artifacts']
            if row['path'] != str(self.old / 'native-reference/final-digest32.hex')]
        full.save(self.old.parent / 'receipt.json', self.receipt)
        self.receipt_pin = full.sha(self.old.parent / 'receipt.json')
        with self.assertRaises(KeyError): self.verify_origin()

    def test_wrong_root_verification_pin_rejects(self):
        self.root_pin = '0' * 64
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_failed_root_verification_rejects_even_with_fresh_pin(self):
        self.verified['integrity_verified'] = False
        self.write_root_verify()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_root_verification_execution_mismatch_rejects(self):
        self.verified['execution_id'] = 'different-execution'
        self.write_root_verify()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_missing_root_verification_rejects(self):
        self.root_verify.unlink()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_missing_original_gold_rejects(self):
        (self.old / 'native-reference/dataset-items.hex').unlink()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_missing_original_digest_rejects(self):
        (self.old / 'native-reference/final-digest32.hex').unlink()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_missing_original_command_ledger_rejects(self):
        (self.old / 'commands.json').unlink()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_missing_original_native_provenance_rejects(self):
        (self.old / 'pinned_iteration.inc').unlink()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_mutated_original_model_rejects(self):
        (self.old / 'obj-fullhash/sim').write_bytes(b'changed original model\n')
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_rebound_original_failed_command_rejects(self):
        self.original['commands'][-1]['wall_timeout'] = True
        self.write_original()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_original_native_generation_argv_is_exact(self):
        self.original['commands'][2]['argv'][3] = '2'
        self.write_original()
        with self.assertRaises(AssertionError): self.verify_origin()

    def test_rebuilt_verifier_requires_its_own_schema(self):
        self.rebuilt['schema'] = full.PREPARED_SCHEMA
        self.write_rebuilt()
        with self.assertRaises(AssertionError): self.verify_new()

    def test_rebuilt_source_map_is_exact_after_freeze(self):
        self.sources[full.BENCH]['bytes'] += 1
        with self.assertRaises(AssertionError): self.verify_new()

    def test_rebuilt_tree_is_exact_after_freeze(self):
        self.rebuilt['source_tree'] = '3' * 40
        self.write_rebuilt()
        with self.assertRaises(AssertionError): self.verify_new()

    def test_rebuilt_origin_pin_mismatch_rejects(self):
        self.rebuilt['reused_reference']['manifest_sha256'] = '0' * 64
        self.write_rebuilt()
        with self.assertRaises(AssertionError): self.verify_new()

    def test_rebound_copy_cannot_replace_origin_gold(self):
        path = self.new / 'native-reference/dataset-items.hex'
        path.write_bytes(b'different copied assertions\n')
        self.rebuilt['files']['native-reference/dataset-items.hex'] = full.identity(path)
        self.write_rebuilt()
        with self.assertRaises(AssertionError): self.verify_new()

    def test_missing_copied_digest_rejects(self):
        (self.new / 'native-reference/final-digest32.hex').unlink()
        with self.assertRaises(AssertionError): self.verify_new()

    def test_old_model_cannot_be_relabelled_with_fresh_rebuilt_pin(self):
        (self.new / 'obj-fullhash/sim').write_bytes((self.old / 'obj-fullhash/sim').read_bytes())
        self.rebuilt['files']['obj-fullhash/sim'] = full.identity(self.new / 'obj-fullhash/sim')
        self.write_rebuilt()
        with self.assertRaises(AssertionError): self.verify_new()

    def test_mutated_rebuilt_model_rejects(self):
        (self.new / 'obj-fullhash/sim').write_bytes(b'mutated new model\n')
        with self.assertRaises(AssertionError): self.verify_new()

    def test_rebound_model_claim_without_external_pin_rejects(self):
        path = self.new / 'obj-fullhash/sim'
        path.write_bytes(b'rebound new model\n')
        self.rebuilt['files']['obj-fullhash/sim'] = full.identity(path)
        full.save(self.new / 'prepared-manifest.json', self.rebuilt)
        with self.assertRaises(AssertionError): self.verify_new()

    def test_unrecorded_copied_gold_rejects(self):
        (self.new / 'native-reference/unrecorded.hex').write_text('extra\n')
        with self.assertRaises(AssertionError): self.verify_new()

    def test_missing_rebuilt_command_ledger_rejects(self):
        (self.new / 'commands.json').unlink()
        with self.assertRaises(AssertionError): self.verify_new()

    def test_rebound_failed_rebuilt_command_rejects(self):
        self.rebuilt['commands'][-1]['returncode'] = 1
        self.write_rebuilt()
        with self.assertRaises(AssertionError): self.verify_new()

    def test_rebuilt_commands_cannot_claim_new_native_generation(self):
        self.rebuilt['commands'].insert(1, self.commands('native-full-reference')[0])
        self.write_rebuilt()
        with self.assertRaises(AssertionError): self.verify_new()

    def test_mutated_rebuilt_command_ledger_rejects(self):
        full.save(self.new / 'commands.json', [])
        with self.assertRaises(AssertionError): self.verify_new()

    def test_rebuilt_archive_assets_and_tools_must_match_origin(self):
        for name in ('native_archive_sha256', 'prepared_assets', 'verilator_files'):
            with self.subTest(name=name):
                saved = copy.deepcopy(self.rebuilt[name])
                self.rebuilt[name] = 'changed origin binding'
                self.write_rebuilt()
                with self.assertRaises(AssertionError): self.verify_new()
                self.rebuilt[name] = saved


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
