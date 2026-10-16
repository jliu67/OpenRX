#!/usr/bin/env python3
"""Fail closed on the explicitly pinned superscalar CI toolchain; retain evidence."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'scripts/superscalar-toolchain.lock.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(lock):
    errors = []
    actual = {'packages': {}, 'files': {}, 'directories': {}}
    for package, expected in lock['packages'].items():
        result = subprocess.run(['dpkg-query', '-W', '-f=${Version}', package],
                                capture_output=True, text=True)
        version = result.stdout.strip()
        actual['packages'][package] = {'version': version, 'returncode': result.returncode}
        if result.returncode or version != expected:
            errors.append('package version mismatch: ' + package)
    for name, expected in lock['files'].items():
        path = Path(name)
        if not path.is_file():
            errors.append('missing tool: ' + name)
            continue
        value = {'sha256': digest(path), 'resolved_path': str(path.resolve())}
        actual['files'][name] = value
        if value != expected:
            errors.append('tool identity mismatch: ' + name)
    for name, expected in lock['directories'].items():
        path = Path(name)
        files, generated_cache = {}, {}
        for p in sorted(path.rglob('*')):
            if not p.is_file():
                continue
            relative = p.relative_to(path)
            # Jammy's Python postinstall generates interpreter-specific bytecode.
            # Pin its official .py source; report cache bytes without pinning them.
            is_cache = (name == '/usr/share/yosys' and
                        relative.parts[0] == '__pycache__' and p.suffix == '.pyc')
            (generated_cache if is_cache else files)[str(relative)] = digest(p)
        canonical = hashlib.sha256(json.dumps(files, sort_keys=True,
                                              separators=(',', ':')).encode()).hexdigest()
        actual['directories'][name] = {'files': files, 'canonical_sha256': canonical,
                                      'unbound_generated_python_cache': generated_cache}
        if files != expected['files'] or canonical != expected['canonical_sha256']:
            errors.append('tool support directory mismatch: ' + name)
    return actual, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    lock = json.loads(LOCK.read_text())
    actual, errors = inspect(lock)
    report = {'schema': 'openrx.superscalar.hosted-toolchain-check.v1',
              'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'lock_sha256': digest(LOCK), 'actual': actual,
              'errors': errors, 'status': 'pass' if not errors else 'fail',
              'scope': 'Tool identity only; no scientific workload or acceptance.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    if errors:
        raise SystemExit('; '.join(errors))
    print('Pinned superscalar tool identities verified; scientific validation remains separate.')


if __name__ == '__main__':
    main()
