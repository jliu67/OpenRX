#!/usr/bin/env python3
"""Independent register byte-pattern corpus; native BLAKE2b supplies digests."""
import random,json
from pathlib import Path
def prepare(out,accepted_registers):
 out=Path(out);rng=random.Random(0x626c616b653262);rows=[bytes(256),bytes([255])*256,bytes(range(256)),bytes(255-i for i in range(256))]
 for i in range(256):
  row=bytearray(256);row[i]=128;rows.append(bytes(row))
 rows.extend(bytes(rng.randrange(256) for _ in range(256)) for _ in range(256))
 native=0
 for line in Path(accepted_registers).read_text().splitlines():
  p,record,mode=line.split();assert len(record)==512;rows.append(bytes.fromhex(record)[::-1]);native+=1
 assert native==8
 (out/'register-inputs.hex').write_text('\n'.join(row[::-1].hex() for row in rows)+'\n')
 (out/'hash-corpus.json').write_text(json.dumps({'vectors_per_digest':len(rows),'digest_sizes':[32,64],'zero_ones_sequence_inverse':4,'each_byte_single_high_bit':256,'seeded_arbitrary_bytes':256,'accepted_full_native_program_register_files':native,'seed':'0x626c616b653262','byte_layout':'R[64],F[64],E[64],A[64], little endian words; unkeyed256 bytes'},indent=2)+'\n')
 return len(rows)
