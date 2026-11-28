"""Directed DATA-only interface/accounting regressions; synthetic calibration
records below exercise validation, and are not real measurement evidence.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.architecture import machine as M
from tools.architecture import memory_policies as P

ROOT = Path(__file__).resolve().parents[1]


class ContractCorrections(unittest.TestCase):
    def setUp(self):
        baseline=json.loads((ROOT/'tools/architecture/fixtures/machine-baseline.json').read_bytes())
        self.d,_=P.comparison_inputs(ROOT,baseline)
        self.d['architectures']=self.d['architectures'][:1]
        self.d['samples']=self.d['samples'][:1]
        self.a=self.d['architectures'][0]
        self.p=self.d['physical'][self.a['physical_id']]

    def row(self):return M.evaluate(self.d)['rows'][0]

    def test_relabel_cannot_bypass_typed_validation(self):
        for placement in ('all_local','static256K_cache16K_sector'):
            for keep in ({'memory_policy_id'},{'credit_contracts'},{'memory_policy_id','credit_contracts'}):
                d=copy.deepcopy(self.d);a=d['architectures'][0];a['placement']=placement
                for key in {'memory_policy_id','credit_contracts'}-keep:a.pop(key)
                with self.subTest(placement=placement,keep=keep),self.assertRaisesRegex(ValueError,'require static_prefix'):
                    M.evaluate(d)

    def test_numeric_witnesses_require_explicit_assumption_provenance(self):
        for value,scope,source in (('full_hash_residence_cycles','residence_scope','residence_source_id'),
                                   ('complete_engine_service_cycles_per_hash','service_scope','service_source_id')):
            for fields in ({},{scope:P.FULL,source:'capacity66_native'},
                           {scope:'full_hash_native_checked',source:'capacity66_native'},
                           {scope:'assumed_full_hash',source:'capacity66_native'}):
                d=copy.deepcopy(self.d);a=d['architectures'][0];a[value]=40000000;a.update(fields)
                with self.subTest(value=value,fields=fields),self.assertRaisesRegex(ValueError,'numeric witness'):
                    M.evaluate(d)
            d=copy.deepcopy(self.d);d['architectures'][0].update({value:40000000,scope:'assumed_full_hash',source:'protocol_assumptions'})
            r=M.evaluate(d)['rows'][0]
            self.assertFalse(r['numeric_witness_application']['achieved_schedule_qualified'])

    def test_assumption_scope_is_required_on_legacy_placement_too(self):
        d=json.loads((ROOT/'tools/architecture/fixtures/machine-baseline.json').read_bytes())
        d['architectures'][0]['complete_engine_service_cycles_per_hash']=40000000
        with self.assertRaisesRegex(ValueError,'numeric witness'):M.evaluate(d)

    def calibration_fixture(self,tmp):
        """Explicitly synthetic qualified-record shape, for parser tests only."""
        m=self.p['external_classes']['dataset']
        m.update(qualification='characterized',technology='synthetic-test-only',corner='synthetic-PVT',
                 source_ids=['test_calibration'],sustained_payload_Bps=1048576000000,
                 sustained_transactions_per_s=16384000000,outstanding=2000)
        m['parameter_sources']={k:'test_calibration' for k in M.MEMORY_NUMBERS if m[k] is not None}
        record=dict(schema='openrx.memory-calibration.v1',qualification='qualified_scope_specific',
            technology=m['technology'],corner=m['corner'],traffic_binding=copy.deepcopy(m['traffic_binding']),
            parameters={k:m[k] for k in M.MEMORY_NUMBERS if m[k] is not None},
            response_interpretation=m['response_interpretation'],application=dict(
                frequency_Hz=[self.d['scenarios'][0]['frequency_Hz']],hashes_per_s=self.d['target']['hashes_per_s'],
                input_sha256=[self.d['samples'][0]['input_sha256']],transactions_per_s=[16384000000]))
        path=Path(tmp)/'SYNTHETIC-calibration.json'
        self.write_calibration(path,record,m)
        return m,path,record

    def write_calibration(self,path,record,m):
        raw=json.dumps(record,sort_keys=True).encode();path.write_bytes(raw)
        self.d['sources']['test_calibration']=dict(kind='measured',technology=m['technology'],corner=m['corner'],
            path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

    def test_PVT_and_caller_label_alone_do_not_qualify_service(self):
        with tempfile.TemporaryDirectory()as tmp:
            m,path,record=self.calibration_fixture(tmp)
            self.d['sources']['test_calibration'].pop('path')
            with self.assertRaisesRegex(ValueError,'calibration evidence'):self.row()
        self.assertTrue(m['qualification']=='characterized')

    def test_bound_record_positive_and_value_or_hash_mismatch(self):
        with tempfile.TemporaryDirectory()as tmp:
            m,path,record=self.calibration_fixture(tmp)
            self.assertIsNone(self.row()['cost']['wall']['wall_power_w'])
            for field in M.MEASURED_SERVICE:
                old=m[field]
                if old is None:continue
                m[field]=old*2
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,'differs from calibration'):
                    self.row()
                m[field]=old
            path.write_bytes(path.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'evidence binding'):self.row()

    def test_calibration_traffic_load_and_frequency_scope(self):
        with tempfile.TemporaryDirectory()as tmp:
            m,path,record=self.calibration_fixture(tmp)
            base=copy.deepcopy(record)
            for field,value in (('credit_unit',P.PARENT),('coalescing',P.UNMERGED),('source_scope',P.WINDOW)):
                record=copy.deepcopy(base);record['traffic_binding'][field]=value;self.write_calibration(path,record,m)
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,'contract join'):self.row()
            for field,value in (('frequency_Hz',[1]),('hashes_per_s',1),('input_sha256',['0'*64]),('transactions_per_s',[1])):
                record=copy.deepcopy(base);record['application'][field]=value;self.write_calibration(path,record,m)
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,'outside actual traffic'):self.row()

    def test_record_requires_scope_qualification_and_matching_latency_kind(self):
        with tempfile.TemporaryDirectory()as tmp:
            m,path,record=self.calibration_fixture(tmp)
            record['qualification']='count_only';self.write_calibration(path,record,m)
            with self.assertRaisesRegex(ValueError,'scope-specific calibration'):self.row()
            record['qualification']='qualified_scope_specific';record['response_interpretation']='upper_bound';self.write_calibration(path,record,m)
            with self.assertRaisesRegex(ValueError,'latency interpretation'):self.row()

    def test_queue_known_parts_survive_unknown_base(self):
        self.p['credit_storage_cost'].update(area_mm2_per_B=1e-9,leakage_W_per_B=1e-6,event_energy_pJ=1)
        r=self.row();q=r['cost']['queue_contributions'];size=r['private_credit_storage_B']
        events=r['traffic']['credit_events_per_hash']
        self.assertAlmostEqual(r['cost']['known_partial_area_mm2'],size*1e-9)
        self.assertAlmostEqual(r['cost']['wall']['known_DC_contribution_W'],size*1e-6+events*1e-6)
        self.assertAlmostEqual(q['area_mm2'],size*1e-9)
        self.assertIsNone(r['cost']['area_mm2']);self.assertIsNone(r['cost']['wall']['wall_power_w'])

    def test_queue_and_provided_base_leakage_are_not_double_counted(self):
        self.p['static_dc_W']['logic_leakage']=7
        self.p['unit_leakage_W']={k:999 for k in M.SERVICES}  # superseded by supplied base total
        self.p['logic_source_id']='protocol_assumptions'
        self.p['credit_storage_cost'].update(leakage_W_per_B=1e-6,event_energy_pJ=1)
        r=self.row();events=r['traffic']['credit_events_per_hash']
        self.assertAlmostEqual(r['cost']['wall']['known_DC_contribution_W'],7+r['private_credit_storage_B']*1e-6+events*1e-6)
        self.p['credit_storage_cost']['leakage_W_per_B']=None
        r=self.row()
        self.assertAlmostEqual(r['cost']['wall']['known_DC_contribution_W'],7+events*1e-6)
        self.assertIsNone(r['cost']['wall']['wall_power_w'])


if __name__=='__main__':unittest.main()
