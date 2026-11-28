"""Small retained-DATA regressions. No simulator, runner, native or RTL job."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.architecture import machine as M
from tools.architecture import memory_policies as P

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/'tools/architecture/fixtures/machine-baseline.json'


class IntermediatePolicies(unittest.TestCase):
    def setUp(self):
        self.baseline = json.loads(FIXTURE.read_bytes())
        self.d, self.windows = P.comparison_inputs(ROOT, self.baseline)

    def rows(self):
        return M.evaluate(self.d)['rows']

    def test_legacy48_exact(self):
        rows = M.evaluate(self.baseline)['rows']
        raw = json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
        self.assertEqual((len(rows),hashlib.sha256(raw).hexdigest()),
            (48,'89a40aac637f1cb001b2e667aab9b93460f1f29ee1660e6e21737272b0fe02cd'))

    def test_source_projection_and_no_fullhash_witness(self):
        M.verify_sources(self.d)
        rows = self.rows()
        self.assertEqual(len(rows),6)
        self.assertEqual({r['local_capacity_B_per_context'] for r in rows},set(P.CAPACITIES))
        for r in rows:
            self.assertIsNone(r['full_hash_residence_cycles'])
            self.assertIsNone(r['cost']['wall']['wall_power_w'])
            self.assertFalse(r['demonstrated_hardware_feasibility'])

    def test_real_macro_front_and_backing_separation(self):
        rows = {r['local_capacity_B_per_context']:r for r in self.rows() if r['nonce']==0}
        a,b=rows[1048576],rows[1572864]
        self.assertEqual(a['traffic']['private_macro_read16'],1208619)
        self.assertEqual(b['traffic']['private_macro_read16'],1327523)
        self.assertEqual(a['traffic']['SP_front_read16'],1440000)
        self.assertEqual(a['traffic']['external_classes']['scratchpad_backing'],dict(read64=93563,write64=58701))
        self.assertEqual(a['traffic']['local_refill16'],0)
        self.assertEqual(rows[2097152]['traffic']['external_classes']['scratchpad_backing'],dict(read64=0,write64=0))
        self.assertEqual(rows[2097152]['external_backing_B'],0)

    def test_auxiliary_and_backing_scale_with_credit_residence(self):
        r=next(r for r in self.rows() if r['nonce']==0 and r['local_capacity_B_per_context']==1048576)
        self.assertEqual(r['provisioned_contexts'],7614)
        self.assertEqual(r['target_engine_minimum_or_planning_count'],7614)
        self.assertEqual(r['private_aux_B'],7614*(65536+384))
        self.assertEqual(r['external_backing_B'],7614*1048576)
        self.assertEqual(r['external_service']['classes']['scratchpad_backing']['credit_supply'],15228)
        self.assertEqual(r['target_resource_instance_counts']['integer64'],2*7614)

    def test_larger_residence_reprovisions_every_dependent_count(self):
        old=self.rows()[0];a=self.d['architectures'][0]
        a.update(contexts_per_engine=4,full_hash_residence_cycles=80000000,residence_scope='assumed_full_hash',residence_source_id='protocol_assumptions')
        r=self.rows()[0]
        self.assertEqual(r['provisioned_contexts'],40000)
        self.assertEqual(r['target_engine_minimum_or_planning_count'],10000)
        self.assertGreater(r['private_data_B'],old['private_data_B'])
        self.assertEqual(r['external_backing_B'],40000*1048576)
        self.assertEqual(r['external_service']['classes']['dataset']['credit_supply'],80000)
        self.assertEqual(r['private_credit_storage_B'],40000*384)

    def test_parent_child_and_coalescing_joins_reject(self):
        for field,value in (('credit_unit',P.PARENT),('coalescing',P.UNMERGED),('source_scope',P.WINDOW),('capacity_B',1572864),('capacity_B',1048576.0)):
            d=copy.deepcopy(self.d);a=d['architectures'][0]
            d['physical'][a['physical_id']]['external_classes']['scratchpad_backing']['traffic_binding'][field]=value
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'contract join'):
                M.evaluate(d)

    def test_policy_and_sample_identity_reject(self):
        a=self.d['architectures'][0];self.d['memory_policies'][a['memory_policy_id']]['cases'][0]['digest_hex']='0'*64
        with self.assertRaisesRegex(ValueError,'immutable identity'):self.rows()

    def test_projection_tamper_rejected_under_unchanged_pins(self):
        a=self.d['architectures'][0];self.d['memory_policies'][a['memory_policy_id']]['cases'][0]['backing_read64']+=1
        with self.assertRaisesRegex(ValueError,'retained capacity/phase projection'):M.verify_sources(self.d)

    def test_window_cannot_become_fullhash_residence(self):
        a=self.d['architectures'][0];a['full_hash_residence_cycles']=10000000;a['residence_scope']=P.WINDOW
        with self.assertRaisesRegex(ValueError,'window-to-fullhash'):self.rows()
        comparators=P.window_comparators(self.windows)
        self.assertEqual(len(comparators),4)
        for c in comparators:
            self.assertIsNone(c['full_hash_residence_cycles'])
            self.assertEqual(c['traffic_contract']['credit_unit'],P.PARENT)

    def test_dataset_latency_does_not_relabel_backing(self):
        a=self.d['architectures'][0];p=self.d['physical'][a['physical_id']]
        before=self.rows()[0]
        p['external_classes']['dataset']['response_latency_s']=1e-9
        after=self.rows()[0]
        self.assertEqual(before['credit_driven_engine_floors']['scratchpad_backing'],after['credit_driven_engine_floors']['scratchpad_backing'])
        self.assertEqual(after['external_service']['classes']['dataset']['necessary_outstanding_average'],17)

    def test_no_free_credit_storage_and_energy(self):
        a=self.d['architectures'][0];p=self.d['physical'][a['physical_id']]
        p['logic_source_id']='protocol_assumptions'
        p['aux_area_mm2_per_context']=0;p['aux_leakage_W_per_context']=0;p['RF_metadata_J_per_hash']=0
        p['logic_base_leakage_W_per_engine']=0;p['unit_leakage_W']={k:0 for k in M.SERVICES}
        p['credit_storage_cost'].update(area_mm2_per_B=1e-9,leakage_W_per_B=1e-6,event_energy_pJ=1)
        r=self.rows()[0]
        self.assertAlmostEqual(r['cost']['known_partial_area_mm2'],r['private_credit_storage_B']*1e-9)
        transfers=r['traffic']['external_read64']+r['traffic']['external_write64']
        self.assertAlmostEqual(r['cost']['wall']['known_DC_contribution_W'],r['private_credit_storage_B']*1e-6+2*transfers*1e-6)
        self.assertIsNone(r['cost']['wall']['wall_power_w'])
        self.d['sources']['unbound_credit']={'kind':'measured','technology':None,'corner':None}
        p['credit_storage_cost']['source_id']='unbound_credit'
        with self.assertRaisesRegex(ValueError,'credit costs require bound PVT'):
            self.rows()

    def test_macro_energy_uses_local_not_front_traffic(self):
        a=self.d['architectures'][0];p=self.d['physical'][a['physical_id']]
        m=p['private_memory'];m.update(read_energy_pJ=1,write_energy_pJ=2)
        m['parameter_sources'].update(read_energy_pJ='protocol_assumptions',write_energy_pJ='protocol_assumptions')
        r=self.rows()[0]
        self.assertAlmostEqual(r['cost']['wall']['known_DC_contribution_W'],(1208619+2*534076)*1e-6)

    def test_private_limit_charges_auxiliary_and_credits(self):
        r=self.rows()[0];self.d['target']['private_capacity_B']=r['private_data_B']
        self.assertTrue(self.rows()[0]['fixed_pool_capacity_rejected'])

    def test_inactive_backing_does_not_get_free_or_charged_active_credits(self):
        r=next(r for r in self.rows() if r['local_capacity_B_per_context']==2097152)
        self.assertEqual(r['traffic']['credit_storage_B_per_context'],192)
        self.assertNotIn('scratchpad_backing',r['credit_driven_engine_floors'])

    def test_completion_footer_is_required_exact(self):
        data,_=P.load_evidence(ROOT)
        records=data['capacity66_native'];records[-1]['completed_inputs']=1
        with self.assertRaisesRegex(ValueError,'completion footer'):
            P.policies(records,data['capacity66_validated'])


if __name__=='__main__':
    unittest.main()
