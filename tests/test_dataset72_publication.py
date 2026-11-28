"""Bounded DATA validation only; no timing simulation, native or HDL execution."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from experiments.dataset_service72 import validate as C

class Closure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config_raw=(C.ROOT/'INPUTS.json').read_bytes()
        cls.pins=C.strict(cls.config_raw)['files']
        cls.records=C.relative_read(cls.pins['records'])
        cls.template=C.strict(C.relative_read(cls.pins['templates']))
        cls.originals=C.decode(cls.records,cls.template)
        cls.data=C.strict(cls.originals['ordered'])
        cls.native=cls.originals['native_items']
        cls.csv=cls.originals['item_csv']

    def test_exact_retained_native_closure(self):
        r=C.close(self.config_raw)
        self.assertEqual((r['records'],r['input_bytes'],r['canonical_digest']),(16384,52,C.DIGEST))
        self.assertFalse(r['causal_ready']);self.assertEqual(r['new_simulations'],0)
        self.assertIsNone(r['full_hash_residence_cycles']);self.assertIsNone(r['measured_service_Bps'])

    def test_order_tamper_and_truncation(self):
        for change in ('swap','truncate','address'):
            d=copy.deepcopy(self.data)
            if change=='swap':d['rows'][0],d['rows'][1]=d['rows'][1],d['rows'][0]
            elif change=='truncate':d['rows'].pop()
            else:d['rows'][0][2]+=64
            with self.subTest(change=change),self.assertRaises(ValueError):C.validate_rows(d,self.native,self.csv)

    def test_epoch_and_tag_are_owned(self):
        for index in (1,3,4):
            d=copy.deepcopy(self.data);d['rows'][0][index]+=1
            with self.subTest(index=index),self.assertRaisesRegex(ValueError,'owner/epoch'):C.validate_rows(d,self.native,self.csv)

    def test_boolean_is_not_address_or_ordinal(self):
        d=copy.deepcopy(self.data);d['rows'][0][2]=False
        with self.assertRaisesRegex(ValueError,'u64 record'):C.validate_rows(d,self.native,self.csv)

    def test_native_order_mismatch(self):
        n=self.native.splitlines(keepends=True);n[0],n[1]=n[1],n[0]
        with self.assertRaisesRegex(ValueError,'native address order'):C.validate_rows(self.data,b''.join(n),self.csv)

    def test_same_address_cannot_change_dataset_value(self):
        seen=set();index=None
        for i,row in enumerate(self.data['rows']):
            if row[2]in seen:index=i;break
            seen.add(row[2])
        self.assertIsNotNone(index)
        lines=self.native.splitlines();a,value=lines[index].split(b' ')
        lines[index]=a+b' '+(b'0' if value[:1]!=b'0' else b'1')+value[1:]
        with self.assertRaisesRegex(ValueError,'immutable dataset value'):
            C.validate_rows(self.data,b'\n'.join(lines)+b'\n',self.csv)

    def test_csv_mismatch(self):
        n=self.csv.splitlines(keepends=True);n[1],n[2]=n[2],n[1]
        with self.assertRaisesRegex(ValueError,'csv order'):C.validate_rows(self.data,self.native,b''.join(n))

    def test_progress_must_not_be_promoted_to_ready(self):
        with self.assertRaisesRegex(ValueError,'missing causal'):
            C.causal_gate(C.COLUMNS,hashlib.sha256(bytes.fromhex(C.INPUT_HEX)).hexdigest())
        with self.assertRaisesRegex(ValueError,'immutable input'):
            C.causal_gate(set(),'0'*64)

    def test_mapping_geometry_and_padding(self):
        for channels in (1,64):
            for a in (0,64,8192,524288,C.DATASET_B-64):
                self.assertEqual(C.reconstruct(C.location(a,channels),channels),a)
        self.assertEqual(C.location(64*64,64),(0,0,0,0,8))
        with self.assertRaises(ValueError):C.location(1)
        with self.assertRaises(ValueError):C.location(True)
        with self.assertRaises(ValueError):C.reconstruct((0,3,3,65535,1016),64)

    def test_source_hash_not_just_length(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fixture';p.write_bytes(b'abc')
            with self.assertRaisesRegex(ValueError,'integrity'):
                C.relative_read(dict(path='fixture',bytes=3,sha256='0'*64),Path(d))

    def test_duplicate_or_nonfinite_json_reject(self):
        for raw in (b'{"a":1,"a":2}',b'{"a":NaN}'):
            with self.assertRaises(ValueError):C.strict(raw)

    def test_timing_promotion_reject(self):
        d=copy.deepcopy(self.data);d['request_edge_or_offered_arrival_inferred']=True
        with self.assertRaisesRegex(ValueError,'source-order scope'):C.validate_rows(d,self.native,self.csv)

    def test_corrected_periodic_not_active_fraction_product(self):
        b=C.periodic_bounds();self.assertEqual(b['max_ACT_per_3900ns'],680)
        self.assertAlmostEqual(float(b['one_ACT_per64B_Bps'])/1e9,11.158974358974358)
        self.assertGreater(b['one_ACT_per64B_Bps'],(4/28)*(4733/5200)*(64/0.75)*1e9)

    def test_binary_reconstruction_hashes_every_original(self):
        self.assertEqual(set(self.originals),set(C.ORIGINALS))
        for key,raw in self.originals.items():
            self.assertEqual(len(raw),C.ORIGINALS[key]['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),C.ORIGINALS[key]['sha256'])

    def test_record_reorder_value_and_legacy_coordinate_tamper(self):
        for offset in (0,8,16):
            raw=bytearray(self.records);raw[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(ValueError):C.decode(bytes(raw),self.template)
        with self.assertRaises(ValueError):C.decode(self.records[:-1],self.template)
        with self.assertRaises(ValueError):C.decode(self.records+b'\x00',self.template)

    def test_relative_roles_reject_escape_and_absolute(self):
        for path in ('../outside','/outside'):
            pin=dict(path=path,bytes=0,sha256='0'*64)
            with self.subTest(path=path),self.assertRaises(ValueError):C.relative_read(pin)

    def test_original_hash_and_unknowns_cannot_be_relabelled(self):
        m=C.strict(self.config_raw);m['originals']['native_items']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'rebaselined'):C.close(json.dumps(m).encode())
        for key,value in [('causal_ready',True),('measured_service_Bps',1),('read_energy_pJ',1),('full_hash_residence_cycles',1)]:
            m=C.strict(self.config_raw);m[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'unknown service'):C.close(json.dumps(m).encode())

    def test_active_interval_is_not_idle_padded_service(self):
        r=C.intervals(100,180,200,0,1000,640)
        self.assertEqual((r['active_ticks'],r['padded_observation_ticks'],r['idle_padding_ticks']),(100,1000,900))
        self.assertEqual(r['active_payload_B_per_tick'],10*r['padded_duty_average_B_per_tick'])
        self.assertFalse(r['sustainable_service_qualified'])
        with self.assertRaises(ValueError):C.intervals(100,180,170,0,1000,640)

    def test_public_text_roles_have_no_private_locations(self):
        patterns=[b'/' + b'home/',b'/' + b'run/user/',b'/' + b'sys/fs/cgroup/',b'Sentinel'+b'_',b'github'+b'_pat_',b'ghp'+b'_']
        for path in C.ROOT.iterdir():
            if path.is_file()and path.name!='records.bin':
                for pattern in patterns:self.assertNotIn(pattern,path.read_bytes(),path.name)

    def test_portable_copy_has_no_original_host_dependency(self):
        import importlib.util
        import shutil
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);package=root/'experiments/dataset_service72'
            shutil.copytree(C.ROOT,package)
            (root/'docs').mkdir()
            shutil.copyfile(C.ROOT.parents[1]/'docs/status-evidence-20261020.json',root/'docs/status-evidence-20261020.json')
            spec=importlib.util.spec_from_file_location('portable_dataset72',package/'validate.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            r=module.close()
            self.assertEqual((r['records'],r['canonical_digest']),(16384,C.DIGEST))
            self.assertFalse(r['causal_ready']);self.assertIsNone(r['measured_service_Bps'])

if __name__=='__main__':unittest.main()
