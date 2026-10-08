#!/usr/bin/env python3
"""Verify vendored bytes against the reviewed source manifest."""
import hashlib, json, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
source = root / 'vendor/randomx'
expected = json.loads((root / 'vendor/randomx.sha256.json').read_text())
actual = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(source.rglob('*')) if p.is_file()}
if actual != expected:
    changed = sorted(k for k in set(actual) | set(expected) if actual.get(k) != expected.get(k))
    print('Vendor integrity FAILED: ' + ', '.join(changed), file=sys.stderr)
    sys.exit(1)
print(f'Vendor integrity OK ({len(actual)} files)')
