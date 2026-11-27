"""Expose the experimental source/entry-point checks to Foundation discovery.

Native RTL reproduction still requires admitted assets and a capped local host.
"""
import importlib.util
from pathlib import Path

path=Path(__file__).resolve().parents[1]/'experiments/shared_context_vm/tools/test_shared_vm.py'
spec=importlib.util.spec_from_file_location('shared_context_vm_delivery_checks',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Delivery=module.Delivery
