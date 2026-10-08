#!/usr/bin/env python3
"""Compare every archived gem5 source file with the exact extracted bytes."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import tarfile

parser = argparse.ArgumentParser()
parser.add_argument('--archive', type=Path, required=True)
parser.add_argument('--extraction-root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
changed = []
counts = {'regular_files': 0, 'symbolic_links': 0, 'hard_links': 0, 'other_nondirectories': 0}
with tarfile.open(args.archive) as tar:
    for entry in tar:
        relative = Path(entry.name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe archive member name')
        path = args.extraction_root / relative
        if entry.isfile():
            counts['regular_files'] += 1
            expected = tar.extractfile(entry).read()
            if path.is_symlink() or not path.is_file() or hashlib.sha256(expected).digest() != hashlib.sha256(path.read_bytes()).digest():
                changed.append(entry.name)
        elif entry.issym():
            counts['symbolic_links'] += 1
            if not path.is_symlink() or os.readlink(path) != entry.linkname:
                changed.append(entry.name)
        elif entry.islnk():
            counts['hard_links'] += 1
            expected = tar.extractfile(entry).read()
            if not path.is_file() or hashlib.sha256(expected).digest() != hashlib.sha256(path.read_bytes()).digest():
                changed.append(entry.name)
        elif not entry.isdir():
            counts['other_nondirectories'] += 1
            changed.append(entry.name)
report = {'status': 'pass' if not changed else 'fail',
          'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'archive': str(args.archive),
          'archive_sha256': hashlib.sha256(args.archive.read_bytes()).hexdigest(),
          'extraction_root': str(args.extraction_root),
          'archive_entry_counts': counts,
          'modified_or_missing_archive_members': changed,
          'scope': 'All archived regular files/links checked; generated build outputs and Python bytecode are outside the source archive.'}
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'regular_files': counts['regular_files'], 'modified_or_missing': len(changed)}))
raise SystemExit(0 if not changed else 1)
