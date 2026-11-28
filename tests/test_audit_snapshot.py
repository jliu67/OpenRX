"""Audit packaging regressions; no experimental workload or host admission."""
import copy,hashlib,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments.audit_20261128 import check_snapshot as A

class AuditSnapshot(unittest.TestCase):
    def test_published_snapshot_checks(self):
        self.assertEqual(A.check()['wall_powers_known'],0)

    def test_lossless_window_and_tamper_detection(self):
        raw=b'I 0 0\nF complete\n'
        fixture=dict(schema='openrx.exact-token-pool.v1',tokens=['I','0','F','complete'],rows=[[0,1,1],[2,3]],original_bytes=len(raw),original_sha256=hashlib.sha256(raw).hexdigest())
        self.assertEqual(A.decode_window(fixture),raw)
        for change in ('token','truncated','index','boolean'):
            bad=copy.deepcopy(fixture)
            if change=='token':bad['tokens'][0]='J'
            elif change=='truncated':bad['rows'].pop()
            elif change=='index':bad['rows'][0][0]=99
            else:bad['rows'][0][0]=False
            with self.assertRaises(ValueError):A.decode_window(bad)

    def test_bundle_has_no_private_locations_or_credentials(self):
        bad_patterns=[b'/' + b'home/',b'/' + b'run/user/',b'Sentinel'+b'_',b'github'+b'_pat_',b'ghp'+b'_']
        paths=[r['path']for r in json.loads((A.HERE/'PROVENANCE.json').read_bytes())['files']]
        for relative in paths:
            raw=(A.ROOT/relative).read_bytes()
            for pattern in bad_patterns:self.assertNotIn(pattern,raw,relative)

    def test_live_source_can_evolve_without_rebaselining_snapshot(self):
        source=A.ROOT/'tools/architecture/machine.py'
        original=Path.read_bytes
        def read(path):
            return b'# independently tested current source\n' if path==source else original(path)
        with mock.patch.object(Path,'read_bytes',read):
            self.assertEqual(source.read_bytes(),b'# independently tested current source\n')
            self.assertEqual(A.verify_manifest(),81)

    def test_retained_evidence_tamper_still_fails(self):
        target=A.HERE/'evidence/capacity66/native.jsonl'
        original=Path.read_bytes
        def read(path):
            raw=original(path)
            return bytes([raw[0]^1])+raw[1:] if path==target else raw
        with mock.patch.object(Path,'read_bytes',read),self.assertRaisesRegex(ValueError,'retained public-copy hash'):
            A.verify_manifest()

    def test_local_manifest_cannot_be_rebaselined(self):
        target=A.HERE/'PROVENANCE.json';original=Path.read_bytes
        def read(path):
            return original(path)+b'\n' if path==target else original(path)
        with mock.patch.object(Path,'read_bytes',read),self.assertRaisesRegex(ValueError,'immutable local manifest'):
            A.verify_manifest()

    def test_historical_source_tamper_still_fails(self):
        original=A.git_bytes
        def read(*args):
            raw=original(*args)
            if args==('cat-file','blob',A.SNAPSHOT_COMMIT+':tools/architecture/machine.py'):
                return bytes([raw[0]^1])+raw[1:]
            return raw
        with mock.patch.object(A,'git_bytes',side_effect=read),self.assertRaisesRegex(ValueError,'historical public-copy hash'):
            A.verify_manifest()

    def test_wrong_tree_and_blob_length_fail(self):
        with mock.patch.object(A,'git_bytes',return_value=b'0'*40+b'\n'),self.assertRaisesRegex(ValueError,'historical tree identity'):
            A.verify_manifest()
        with self.assertRaisesRegex(ValueError,'historical blob length'):
            A.historical_bytes('tools/architecture/machine.py',0)
        with self.assertRaisesRegex(ValueError,'historical repository path'):
            A.historical_bytes('../machine.py',0)

    def test_missing_historical_objects_fail_closed(self):
        with tempfile.TemporaryDirectory() as d,mock.patch.object(A,'ROOT',Path(d)):
            with self.assertRaisesRegex(ValueError,'git fetch --no-tags --depth=1 origin '+A.SNAPSHOT_COMMIT):
                A.verify_manifest()

    def test_shallow_repository_needs_only_exact_snapshot_objects(self):
        # Reuse local objects read-only: no network, complete-history fetch or
        # duplicate source archive is needed. The shallow boundary hides parents.
        objects=subprocess.check_output(['git','-C',str(A.ROOT),'rev-parse',
            '--path-format=absolute','--git-path','objects'],text=True).strip()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            subprocess.run(['git','init','--bare','--quiet',str(root)],check=True)
            (root/'objects/info/alternates').write_text(objects+'\n')
            subprocess.run(['git','-C',d,'update-ref','HEAD',A.SNAPSHOT_COMMIT],check=True)
            (root/'shallow').write_text(A.SNAPSHOT_COMMIT+'\n')
            self.assertEqual(subprocess.check_output(['git','-C',d,'rev-list','--count','HEAD'],text=True).strip(),'1')
            here=root/'experiments/audit_20261128';shutil.copytree(A.HERE,here)
            with mock.patch.object(A,'ROOT',root),mock.patch.object(A,'HERE',here):
                self.assertEqual(A.verify_manifest(),81)

if __name__=='__main__':unittest.main()
