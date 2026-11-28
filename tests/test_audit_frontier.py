"""Small DATA-only arithmetic checks, not a service or architecture simulation."""
import unittest
from experiments.audit_20261128.capacity66 import frontier as f

class Directed(unittest.TestCase):
    def test_pinned_python_is_verified_text_without_import(self):
        self.assertIsInstance(f.read(f.B/'reference/service39-shared.py',f.PINS['reference/service39-shared.py']),str)
    def test_payload_transaction_units(self):
        self.assertEqual(f.rounded_envelope(1048576)['required_transactions64_per_s'],168750000000)
        self.assertEqual(f.rounded_envelope(1572864)['required_transactions64_per_s'],89375000000)
        self.assertAlmostEqual(f.rounded_envelope(1048576)['external64_nJ_ceiling_at250W'],1.4814814814814814)
    def test_peak_is_only_efficiency_sensitivity(self):
        self.assertEqual([x['minimum_stacks']for x in f.rounded_envelope(1048576)['stacks_at_assumed_payload_efficiency']],[71,88,141])
        self.assertEqual([x['minimum_stacks']for x in f.rounded_envelope(1572864)['stacks_at_assumed_payload_efficiency']],[38,47,75])
    def test_residence_raises_engines_states_capacity_and_credits(self):
        a=f.provision(2000000,8000000,1,1048576,1,1,1)
        b=f.provision(2000000,12000000,1,1048576,1,1,1)
        self.assertEqual((a['engines'],a['provisioned_contexts']),(4000,4000))
        self.assertEqual((b['engines'],b['provisioned_contexts']),(6000,6000))
        self.assertEqual(b['assumed_backing_child_credits'],12000)
        self.assertEqual(b['local_data_B'],6000*1048576)
    def test_compute_and_transport_cannot_be_free(self):
        a=f.provision(5683860,8000000,4,1048576,1,1,1)
        self.assertEqual(a['engines'],2842);self.assertEqual(a['provisioned_contexts'],11368)
        self.assertFalse(a['local_data_fits8GiB'])
        b=f.provision(1,1,1,1048576,1,4000001,1)
        self.assertEqual(b['engines'],2001)
    def test_distinct_class_latency_and_integer_input(self):
        self.assertEqual(f.credits(16384000000,100),1639)
        self.assertEqual(f.credits(93563000000,100),9357)
        with self.assertRaises(ValueError):f.provision(True,1,1,1048576,1,1,1)
    def test_four_context_rounding_and_paid_returns(self):
        p=f.rounded_envelope(1572864)
        self.assertEqual(p['data_only_contexts_at8GiB'],5461)
        self.assertEqual(p['full4context_engine_residence_ceiling_at2GHz'],10920000)
        a=f.provision(1,8000001,4,1572864,1,1,1)
        self.assertEqual(a['provisioned_contexts'],4004)
        self.assertEqual(a['declared_return_storage_B'],4004*384)
