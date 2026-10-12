"""Actual bounded RandomX integration controls. Run AFTER build_steady.sh.

Not discovered by the pre-build tooling suite. No pool connection or power claim.
"""
import importlib.util
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / 'build/steady/openrx-steady'
UPSTREAM_BINARY = ROOT / 'build/randomx/randomx-benchmark'
EVIDENCE = ROOT / 'build/validation'
TRIAL_OUTPUT = None
STAGED_BUILD = False
spec = importlib.util.spec_from_file_location('steady', ROOT / 'scripts/steady_benchmark.py')
steady = importlib.util.module_from_spec(spec)
spec.loader.exec_module(steady)


class NativeTests(unittest.TestCase):
    def test_source_contract(self):
        upstream = (ROOT / 'vendor/randomx/src/tests/benchmark.cpp').read_text()
        adapter = (ROOT / 'benchmarks/steady/main.cpp').read_text()
        for digest in steady.REFERENCES.values():
            self.assertIn(digest, upstream)
            self.assertIn(digest, adapter)
        original = re.search(r'blockTemplate_\[\]\s*=\s*\{([^}]+)', upstream).group(1)
        copied = re.search(r'block\[\]\s*=\s*\{([^}]+)', adapter).group(1)
        self.assertEqual(re.findall(r'0x[0-9a-f]+', original), re.findall(r'0x[0-9a-f]+', copied))

    def test_cli_rejects_bad_options_before_allocation(self):
        cases = [['--threads', '0'], ['--threads', '257'], ['--nonces', '-1'],
                 ['--nonces', '2147483648'], ['--repeats', '0'], ['--aes', 'auto'],
                 ['--min-seconds', 'nan'], ['--min-seconds', 'inf'], ['--min-seconds', '-1'],
                 ['--threads', '2', '--nonces', '1'], ['--warmup-nonces', '-1'],
                 ['--versions', 'v1,v1'], ['--threads', '1', '--threads', '2'],
                 ['--unknown', '1'], ['--threads'], ['--affinity', '1']]
        evidence = []
        for args in cases:
            p = subprocess.run([str(BINARY)] + args, capture_output=True, text=True, timeout=5)
            evidence.append({'args': args, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
            self.assertEqual(p.returncode, 1, args)
            self.assertEqual(p.stdout, '', args)
            self.assertIn('ERROR:', p.stderr, args)
        (EVIDENCE / 'steady-cli-errors.json').write_text(json.dumps(evidence, indent=2) + '\n')

    def trial(self, threads, aes, nonces=17, minimum=0, warmup=6):
        command = [sys.executable, str(ROOT / 'scripts/steady_benchmark.py'),
                   '--threads', str(threads), '--aes', aes, '--nonces', str(nonces),
                   '--warmup-nonces', str(warmup), '--repeats', '2', '--min-seconds', str(minimum),
                   '--timeout', '420']
        command += ['--binary', str(BINARY)]
        if STAGED_BUILD:
            command += ['--build-root', str(BUILD_ROOT)]
        if TRIAL_OUTPUT is not None:
            command += ['--output-dir', str(TRIAL_OUTPUT / f'trial-{threads}-{aes}-{nonces}')]
        p = subprocess.run(command, capture_output=True, text=True, timeout=450)
        self.assertTrue(p.stdout.strip(), p.stderr)
        output = Path(p.stdout.strip().splitlines()[-1])
        report = json.loads((output / 'run.json').read_text())
        self.assertEqual(report['status'], 'rejected-duration' if minimum else 'ok', report)
        self.assertEqual(p.returncode, 1 if minimum else 0, report)
        records = [json.loads(line) for line in (output / 'adapter.jsonl').read_text().splitlines()]
        controls = [r for r in records if r.get('phase') == 'control']
        self.assertEqual(len(controls), 2)
        for control in controls:
            self.assertEqual(control['digest'], steady.REFERENCES[control['version']])
            self.assertTrue(control['reference_matches'])
        self.assertEqual(sum(r.get('phase') == 'warmup' for r in records), 4 if warmup else 0)
        self.assertEqual(sum(r.get('phase') == 'measurement' for r in records), 4)
        print(json.dumps({'native_control': {'threads': threads, 'aes': aes, 'nonces': nonces,
              'warmup_nonces': warmup, 'status': report['status'], 'output': str(output),
              'control_digests': {r['version']: r['digest'] for r in controls}}}), flush=True)
        return records

    def test_one_worker_hardware_repeated_known_hashes(self):
        self.trial(1, 'hardware', nonces=1000)

    def test_one_worker_software(self):
        self.trial(1, 'software')

    def test_two_workers_duration_rejection(self):
        self.trial(2, 'hardware', minimum=1000000, warmup=0)

    def test_three_workers_software_uneven_partition(self):
        records = self.trial(3, 'software')
        # Non-reference count: compare against the UNMODIFIED upstream harness too.
        for version in ('v1', 'v2'):
            command = [str(UPSTREAM_BINARY), '--mine', '--jit',
                       '--threads', '3', '--init', '2', '--nonces', '17', '--seed', '0', '--softAes']
            if version == 'v2':
                command.append('--v2')
            p = subprocess.run(command, capture_output=True, text=True, timeout=180)
            evidence = {'command': command, 'returncode': p.returncode,
                        'stdout': p.stdout, 'stderr': p.stderr}
            (EVIDENCE / ('steady-differential-' + version + '.json')).write_text(
                json.dumps(evidence, indent=2) + '\n')
            self.assertEqual(p.returncode, 0, evidence)
            match = re.search(r'Calculated result:\s*([0-9a-f]{64})', p.stdout)
            self.assertIsNotNone(match, evidence)
            for record in records:
                if record.get('phase') == 'measurement' and record['version'] == version:
                    self.assertEqual(record['digest'], match.group(1))
            print('Differential 17-nonce / 3-worker / software-AES ' + version + ': MATCH', flush=True)


BUILD_ROOT = ROOT / 'build'


def configure(argv=None):
    global BINARY, UPSTREAM_BINARY, BUILD_ROOT, EVIDENCE, TRIAL_OUTPUT, STAGED_BUILD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-root', type=Path)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--upstream-binary', type=Path)
    parser.add_argument('--output-dir', type=Path, help='Fresh external directory for all control evidence')
    args, remaining = parser.parse_known_args(argv)
    STAGED_BUILD = args.build_root is not None
    BUILD_ROOT = (args.build_root or ROOT / 'build').resolve()
    BINARY = (args.binary or BUILD_ROOT / 'steady/openrx-steady').resolve()
    UPSTREAM_BINARY = (args.upstream_binary or BUILD_ROOT / 'randomx/randomx-benchmark').resolve()
    if args.output_dir:
        try:
            EVIDENCE = steady.external_output(args.output_dir)
            steady.check(EVIDENCE != BUILD_ROOT and EVIDENCE not in BUILD_ROOT.parents
                         and BUILD_ROOT not in EVIDENCE.parents, 'output and build roots must be disjoint')
            steady.check(all(EVIDENCE != p and EVIDENCE not in p.parents for p in (BINARY, UPSTREAM_BINARY)),
                         'output must not contain control binaries')
            EVIDENCE.mkdir(parents=True, exist_ok=False)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        TRIAL_OUTPUT = EVIDENCE
    else:
        EVIDENCE = ROOT / 'build/validation'
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        TRIAL_OUTPUT = None
    if STAGED_BUILD:
        try:
            steady.validate_build(BUILD_ROOT, BINARY)
            steady.check(UPSTREAM_BINARY == (BUILD_ROOT / 'randomx/randomx-benchmark').resolve(),
                         'upstream binary differs from staged build')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(str(exc))
    return remaining


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *configure()], verbosity=2)
