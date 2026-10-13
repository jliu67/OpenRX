#!/usr/bin/env python3
"""Keep upstream bytes intact; remove one duplicate net declaration for Icarus 12."""
import hashlib,json
from pathlib import Path
UPSTREAM_SHA='f76feb5557faa8bcb2868e51bf2ce7d1297be46dd67ae51d509b1ae91066a522'
def prepare(source,output):
 source=Path(source);output=Path(output)
 raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()==UPSTREAM_SHA
 declaration=b'    wire sqrtOpOut;\r\n';assert raw.count(declaration)==1
 # The ANSI output port already declares this same scalar wire. Keep its line empty.
 view=raw.replace(declaration,b'\r\n',1)
 path=output/'HardFloat-divSqrt-compile-view.v';path.write_bytes(view)
 record={'upstream_file':'rtl/execute/vendor/hardfloat/divSqrtRecFN_small.v',
  'upstream_sha256':UPSTREAM_SHA,'view_file':path.name,
  'view_sha256':hashlib.sha256(view).hexdigest(),
  'transform':'replace one duplicate scalar wire sqrtOpOut declaration with an empty CRLF line; the ANSI output already declares the net',
  'removed_declarations':1,'all_other_bytes_unchanged':True,'original_vendor_file_unchanged':True,
  'license':'original full BSD-3-Clause notices retained; separately labeled generated compile view',
  'scope':'Icarus compile only; Yosys synthesis continues to use unchanged upstream source'}
 (output/'HardFloat-compile-view.json').write_text(json.dumps(record,indent=2)+'\n')
 assert source.read_bytes()==raw
 return path
