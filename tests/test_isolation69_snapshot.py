"""Ordinary retained-DATA publication tests; never invokes HDL or scientific tools."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock
from experiments.audit_20261128.isolation69 import analyze, check as P

R = P.HERE


class Collector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checked = P.check()
        proof = json.loads((P.EVIDENCE / 'PROVENANCE.json').read_bytes())
        cls.emitted = proof['sanitized_emitted_bench_path']
        cls.raw = (P.EVIDENCE / 'simulation.txt').read_bytes()

    def parse(self, raw):
        return analyze.activity(raw, emitted_bench_path=self.emitted)

    def reject(self, old, new):
        self.assertIn(old, self.raw)
        with self.assertRaises(ValueError):
            self.parse(self.raw.replace(old, new, 1))

    def test_designated_host_scoped_acceptance(self):
        d = self.parse(self.raw)
        self.assertEqual(d['diagnostics'], dict(first=40, snapshots=16, gates=2, known_and_history_equal=True))
        self.assertEqual((d['accepted_pairs'], d['cycles']), (209, 321))
        self.assertFalse(d['native_flag_oracle'])
        for row in d['rows']:
            if row['phase'] in (1, 3):
                self.assertEqual(row['isolated'], dict(binary=0, fourstate=0))

    def test_local_source_terminal(self):
        # Synthetic DATA transform only; never a claimed local HDL output.
        raw = self.raw.replace(self.emitted.encode(), str(R / 'tb_compare.v').encode())
        analyze.activity(raw)
        with self.assertRaises(ValueError):
            analyze.activity(self.raw)

    def test_original_negative_controls_retained(self):
        raw = (P.HERE.parent / 'evidence/isolation68/simulation.txt').read_bytes()
        with self.assertRaises(ValueError): self.parse(raw)
        import re
        self.assertEqual(sum(int(m[1]) for m in re.finditer(r'ACT id=(?:8|9|1[0-5]) phase=1 binary=\d+ fourstate=(\d+)', raw.decode())), 88)
        old = json.loads((P.HERE.parent / 'evidence/isolation68/result.json').read_bytes())
        self.assertEqual(old['status'], 'FAILED_NO_RETRY')

    def test_missing_records(self):
        lines = self.raw.splitlines(keepends=True)
        for start in (b'FIRST ', b'SNAP ', b'GATE ', b'ACT ', b'PASS '):
            with self.subTest(start=start), self.assertRaises(ValueError):
                self.parse(b''.join(lines[:next(i for i, l in enumerate(lines) if l.startswith(start))] + lines[next(i for i, l in enumerate(lines) if l.startswith(start)) + 1:]))

    def test_duplicate_and_extra(self):
        lines = self.raw.splitlines(keepends=True)
        for prefix in (b'FIRST ', b'SNAP ', b'GATE ', b'ACT '):
            i = next(i for i, l in enumerate(lines) if l.startswith(prefix))
            j = next(j for j in range(i + 1, len(lines)) if lines[j].startswith(prefix))
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                self.parse(b''.join(lines[:j] + [lines[i]] + lines[j + 1:]))
        with self.assertRaises(ValueError):
            self.parse(self.raw + b'extra\n')
        i, j = [i for i, l in enumerate(lines) if l.startswith(b'FIRST id=9 phase=0')][:2]
        with self.assertRaises(ValueError):
            self.parse(b''.join(lines[:j] + [lines[i]] + lines[j + 1:]))

    def test_snapshot_unknown_count(self):
        self.reject(b'unknown=0', b'unknown=1')

    def test_snapshot_unknown_bits(self):
        self.reject(b'unknown=0 prior=0000000000000000000000000000000000', b'unknown=0 prior=x000000000000000000000000000000000')

    def test_snapshot_history(self):
        self.reject(b'unknown=0 prior=0000000000000000000000000000000000', b'unknown=0 prior=0000000000000000000000000000000001')

    def test_gate_unknown_and_nonzero(self):
        for new in (b'accepted=x/0', b'accepted=1/0', b'add=x/0', b'add=1/0', b'mul=z/0', b'mul=1/0'):
            key = new.split(b'=')[0] + b'=0/0'
            with self.subTest(new=new): self.reject(key, new)

    def test_snapshot_identity_time(self):
        self.reject(b'SNAP label=1 id=8 time=27000', b'SNAP label=2 id=8 time=27000')
        self.reject(b'GATE label=2 time=28000', b'GATE label=2 time=28001')

    def test_first_identity_and_phase(self):
        self.reject(b'FIRST id=9 phase=0', b'FIRST id=7 phase=0')
        self.reject(b'FIRST id=9 phase=0', b'FIRST id=9 phase=1')

    def test_first_time_and_multiplicity(self):
        self.reject(b'FIRST id=9 phase=0 time=0', b'FIRST id=9 phase=0 time=30000')
        self.reject(b'FIRST id=14 phase=0 time=2720000', b'FIRST id=14 phase=2 time=2720000')

    def test_first_stream_history(self):
        self.reject(b'phase=2 time=680000 prior=049a0825e4e80000005228ed1ce9be8d09', b'phase=2 time=680000 prior=049a0825e4e80000005228ed1ce9be8d08')

    def test_first_stream_unknown(self):
        self.reject(b'phase=2 time=680000 prior=0000000000000000000000000000000000', b'phase=2 time=680000 prior=x000000000000000000000000000000000')

    def test_vector_width_and_unused_bits(self):
        self.reject(b'SNAP label=1 id=9 time=27000 unknown=0 prior=000000000000000000', b'SNAP label=1 id=9 time=27000 unknown=0 prior=00000000000000000')
        self.reject(b'SNAP label=1 id=9 time=27000 unknown=0 prior=000000000000000000', b'SNAP label=1 id=9 time=27000 unknown=0 prior=400000000000000000')

    def test_allstate_idle_held(self):
        for phase in (1, 3):
            for count in (b'binary=1 fourstate=0', b'binary=0 fourstate=1'):
                with self.subTest(phase=phase, count=count):
                    self.reject(f'ACT id=8 phase={phase} binary=0 fourstate=0'.encode(), f'ACT id=8 phase={phase} '.encode() + count)

    def test_miter_totals(self):
        for key, old in ((b'native', b'12'), (b'corners', b'192'), (b'accepted', b'209'), (b'cycles', b'321'), (b'unknown_controls', b'3'), (b'reset_cancel', b'1')):
            with self.subTest(key=key): self.reject(key + b'=' + old, key + b'=0')

    def test_terminal(self):
        for old, new in ((b':137: $finish', b':138: $finish'), (b'at 3206000', b'at 3206001'), (b'(1ps)', b'(1ns)'), (self.emitted.encode(), b'/wrong/tb_compare.v')):
            with self.subTest(new=new): self.reject(old, new)

    def test_framing_and_bounds(self):
        for raw in (self.raw[:-1], self.raw.replace(b'\n', b'\r\n'), self.raw + b'\x00', b'X' * 16385, self.raw.replace(b'ACT id=0', b'ACT id=00')):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError): self.parse(raw)

    def test_whole_result_must_remain_failed(self):
        import copy
        status=json.loads((P.EVIDENCE/'status.json').read_bytes())
        receipt=json.loads((P.EVIDENCE/'result.json').read_bytes())
        prefix=(P.EVIDENCE/'synth-baseline-prefix.txt').read_bytes()
        for key,value in [('status','PASS'),('overall_pass',True),('physical_acceptance',True),('scientific_retry_allowed',True)]:
            bad=copy.deepcopy(status);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):P.outcome(bad,receipt,prefix)
        for change in ('known_synth_rc','run_isolated'):
            bad=copy.deepcopy(status)
            if change=='known_synth_rc':bad['stages'][2]['returncode']=0
            else:bad['stages'][3]=dict(name='synth-isolated',capture_complete=True,returncode=0)
            with self.subTest(change=change),self.assertRaises(ValueError):P.outcome(bad,receipt,prefix)

    def test_public_copy_tamper_rejected(self):
        original=Path.read_bytes;target=P.EVIDENCE/'simulation.txt'
        def read(p):
            raw=original(p)
            return raw+b'extra\n' if p==target else raw
        with mock.patch.object(Path,'read_bytes',read),self.assertRaisesRegex(ValueError,'evidence integrity'):
            P.check()

    def test_projected_counts_cannot_depart_from_raw(self):
        import copy
        status=json.loads((P.EVIDENCE/'status.json').read_bytes())
        activity=self.parse(self.raw)
        for key,value in [('accepted_pairs',210),('records',107),('native_flags_oracle',True),('isolated_idle_held_fourstate',1)]:
            claim=copy.deepcopy(status['functional_claim']);claim[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):P.activity_claim(claim,activity)

    def test_public_scope_paths_redacted(self):
        r=json.loads((P.EVIDENCE/'result.json').read_bytes())
        self.assertEqual(r['kernel_limits']['service_cgroup'],'[resource-scope-redacted]')
        self.assertTrue(all(x['path']=='[resource-scope-redacted]' for x in r['kernel_limits']['groups']))
        patterns=[b'/' + b'home/',b'/' + b'run/user/',b'/' + b'sys/fs/cgroup/',b'Sentinel'+b'_',b'github'+b'_pat_',b'ghp'+b'_']
        for base in (P.HERE,P.EVIDENCE):
            for p in base.iterdir():
                if p.is_file():
                    for pattern in patterns:self.assertNotIn(pattern,p.read_bytes(),str(p.relative_to(P.ROOT)))
                if p.is_symlink():
                    self.assertFalse(p.readlink().is_absolute())
                    self.assertTrue(p.resolve().is_relative_to(P.ROOT))


if __name__ == '__main__':
    unittest.main()
