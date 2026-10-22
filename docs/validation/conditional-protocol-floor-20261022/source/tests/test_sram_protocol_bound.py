"""Prepared UNRUN focused analytical checks; never launch a model or simulator."""
import copy
from decimal import Decimal
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('prepared_sram_protocol_bound',
                                             SOURCE / 'adapter/sram_protocol_bound.py')
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


class ProtocolBoundTests(unittest.TestCase):
    def bound_inputs(self):
        return ADAPTER.load_inputs(SOURCE / 'inputs', SOURCE / 'input-bindings.json')

    def report(self):
        return ADAPTER.make_report(*self.bound_inputs())

    def value(self, row):
        return Fraction(row['numerator'], row['denominator'])

    def test_exact_accepted_input_set_and_source_bindings(self):
        inputs, bindings = self.bound_inputs()
        self.assertEqual(set(inputs), set(ADAPTER.INPUTS))
        self.assertEqual(len(inputs), 11)
        for name, (size, digest) in ADAPTER.INPUTS.items():
            self.assertEqual(bindings[name], {'bytes': size, 'sha256': digest})
        self.assertEqual(inputs['rtl_protocol.json'], inputs['mapped_protocol.json'])

    def test_two_edge_floor_keeps_same_edge_backend_reply_allowed(self):
        facts = self.report()['protocol_facts']
        self.assertEqual(facts['minimum_capture_spacing_clocks'], 2)
        self.assertIs(facts['same_edge_backend_request_response_permitted'], True)
        self.assertIs(facts['independent_memory_latency_contract_selected'], False)
        self.assertNotIn('synchronous_response_cycles', facts)

    def test_array_intervals_and_breakpoints_are_exact_rationals(self):
        report = self.report()
        one, four = Fraction('2.74122'), Fraction('0.714793')
        self.assertEqual(self.value(report['array_intervals_ns']['bank1']), one)
        self.assertEqual(self.value(report['array_intervals_ns']['bank4']), four)
        self.assertEqual(self.value(report['period_breakpoints_ns']['one_bank']), one / 2)
        self.assertEqual(self.value(report['period_breakpoints_ns']['four_bank']), four / 2)

    def test_piecewise_boundary_equalities_and_ceiling_ratio(self):
        one, four = Fraction('2.74122'), Fraction('0.714793')
        at_four = ADAPTER.ceiling(four, four / 2) / ADAPTER.ceiling(one, four / 2)
        at_one = ADAPTER.ceiling(four, one / 2) / ADAPTER.ceiling(one, one / 2)
        middle = (one + four) / 4
        self.assertEqual(at_four, one / four)
        self.assertEqual(at_one, 1)
        self.assertEqual(ADAPTER.ceiling(four, middle) / ADAPTER.ceiling(one, middle),
                         one / (2 * middle))

    def test_ceiling_intersection_has_no_bank_count_multiplier(self):
        one, four = Fraction('2.74122'), Fraction('0.714793')
        for interval in (one, four):
            for period in (four / 4, four / 2, one / 2, one):
                result = ADAPTER.ceiling(interval, period)
                self.assertLessEqual(result, Fraction(10**9) / interval)
                self.assertLessEqual(result, Fraction(10**9) / (2 * period))
        self.assertEqual(ADAPTER.ceiling(one, one), ADAPTER.ceiling(four, one))
        self.assertNotEqual(ADAPTER.ceiling(four, one), 4 * ADAPTER.ceiling(one, one))

    def test_clock_period_monotonicity_and_algebraic_witnesses(self):
        report = self.report()
        periods = [self.value(x['period_ns']) for x in
                   report['algebraic_witnesses_not_selected_clock_points']]
        self.assertEqual(periods, sorted(periods))
        for interval in (Fraction('2.74122'), Fraction('0.714793')):
            values = [ADAPTER.ceiling(interval, p) for p in periods]
            self.assertEqual(values, sorted(values, reverse=True))

    def test_positive_exact_number_guard_rejects_invalid_values(self):
        for value in (0, -1, True, 1.0, Decimal('NaN'), Decimal('Infinity')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ADAPTER.positive(value)
        self.assertEqual(ADAPTER.positive(Decimal('0.1')), Fraction(1, 10))
        self.assertEqual(ADAPTER.positive(Fraction(1, 7)), Fraction(1, 7))

    def test_strict_json_rejects_duplicates_and_nonfinite_constants(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                ADAPTER.parse_json(raw)
        self.assertEqual(ADAPTER.parse_json(b'{"x":0.1}')['x'], Decimal('0.1'))

    def test_input_substitution_and_registry_rewrite_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs = root / 'inputs'
            shutil.copytree(SOURCE / 'inputs', inputs)
            with (inputs / 'channel.v').open('ab') as stream:
                stream.write(b'\n')
            with self.assertRaises(ValueError):
                ADAPTER.load_inputs(inputs, SOURCE / 'input-bindings.json')
            registry = json.loads((SOURCE / 'input-bindings.json').read_text())
            registry['files']['channel.v']['sha256'] = '0' * 64
            registry_path = root / 'rewritten.json'
            registry_path.write_text(json.dumps(registry))
            with self.assertRaises(ValueError):
                ADAPTER.load_inputs(SOURCE / 'inputs', registry_path)

    def test_input_symlink_and_extra_file_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs = root / 'inputs'
            shutil.copytree(SOURCE / 'inputs', inputs)
            (inputs / 'extra.txt').write_text('extra')
            with self.assertRaises(ValueError):
                ADAPTER.load_inputs(inputs, SOURCE / 'input-bindings.json')
            second = root / 'linked-inputs'
            shutil.copytree(SOURCE / 'inputs', second)
            target = second / 'channel.v'
            target.unlink()
            target.symlink_to(SOURCE / 'inputs/channel.v')
            with self.assertRaises(ValueError):
                ADAPTER.load_inputs(second, SOURCE / 'input-bindings.json')

    def test_scientific_unknowns_raw_flags_and_scope_stay_explicit(self):
        report = self.report()
        self.assertIs(report['physical_acceptance'], False)
        self.assertIs(report['organization']['physical_row_mapping_implemented'], False)
        self.assertTrue(all(x is None for x in report['unknown'].values()))
        self.assertEqual(report['preserved_input_scientific_flags'],
                         {'pr92_report': 'unverified_pending_independent_review',
                          'pr92_provenance': 'unverified_pending_independent_review'})
        self.assertIn('actual_implementation_performance_ratio', report['unknown'])
        self.assertIn('does not prove joint achievability or bound actual performance ratios',
                      ' '.join(report['scope_notes']))

    def test_exclusive_outputs_index_and_private_nonfinite_rejection(self):
        report = self.report()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'report'
            ADAPTER.write_report(output, report, SOURCE / 'inputs')
            index = json.loads((output / 'artifacts.sha256.json').read_text())
            self.assertEqual(set(index), {'protocol-bound.json', 'provenance.json'})
            for name, digest in index.items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)
            with self.assertRaises(ValueError):
                ADAPTER.write_report(output, report, SOURCE / 'inputs')
            for index, value in enumerate(({'secret_path': '/home/server/private'}, {'n': float('inf')})):
                bad = root / ('bad' + str(index))
                with self.assertRaises(ValueError):
                    ADAPTER.write_report(bad, value, SOURCE / 'inputs')
                self.assertFalse(bad.exists())


if __name__ == '__main__':
    unittest.main()
