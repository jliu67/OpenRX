"""Audit packaging regressions; no experimental workload or host admission."""
import copy,hashlib,json,unittest
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

if __name__=='__main__':unittest.main()
