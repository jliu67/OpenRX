from pathlib import Path
import datetime,hashlib,json,tarfile
p=Path('/tmp/openrx-gem5-source/link-recovery-20261008');record=json.loads((p/'package-archive.json').read_text());archive=Path(record['archive']);manifest_path=Path('/tmp/openrx-gem5-reuse/gem5-c8222cc-linux-x86_64-20261008/package-manifest.json');expected=json.loads(manifest_path.read_text());prefix='gem5-c8222cc-linux-x86_64-20261008/'
seen=set();errors=[];total=0
with tarfile.open(archive,'r:gz') as t:
 for m in t:
  if m.isdir():continue
  if not m.isfile() or not m.name.startswith(prefix):errors.append({'member':m.name,'error':'unexpected non-regular file or path'});continue
  name=m.name[len(prefix):]
  if Path(name).is_absolute() or '..' in Path(name).parts:errors.append({'member':m.name,'error':'unsafe path'});continue
  h=hashlib.sha256();f=t.extractfile(m)
  while chunk:=f.read(1024*1024):h.update(chunk)
  if name=='package-manifest.json':
   if h.hexdigest()!=record['package_manifest_sha256']:errors.append({'member':name,'error':'manifest digest mismatch'})
   continue
  seen.add(name);total+=m.size
  e=expected.get(name)
  if not e:errors.append({'member':name,'error':'missing manifest entry'})
  elif e['sha256']!=h.hexdigest() or e['size_bytes']!=m.size or int(e['mode'],8)!=m.mode:errors.append({'member':name,'error':'file digest/size/mode mismatch'})
missing=sorted(set(expected)-seen)
result={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'pass' if not errors and not missing else 'fail','archive':str(archive),'archive_size_bytes':archive.stat().st_size,'archive_sha256':record['archive_sha256'],'archive_manifest_sha256':record['package_manifest_sha256'],'regular_files_verified':len(seen),'manifest_file_verified':True,'file_bytes_verified':total,'errors':errors,'missing_manifest_files':missing,'scope':'Streamed complete gzip/tar; every packaged regular-file digest, size and mode checked against packaged manifest, plus manifest digest; no extraction or executable mutation.'}
(p/'package-archive-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='pass' else 1)
