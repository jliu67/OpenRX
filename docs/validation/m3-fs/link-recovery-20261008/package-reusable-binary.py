import datetime,hashlib,json,os,pathlib,shutil,subprocess,tarfile,time
scratch=pathlib.Path('/tmp/openrx-gem5-source');proof=scratch/'link-recovery-20261008';identity=json.loads((proof/'binary-identity.json').read_text());assert identity['identity_verified']
repo=pathlib.Path('/workspace/scratch/62a7e35b1ac5/OpenRandomX')
bundle=pathlib.Path('/tmp/openrx-gem5-reuse/gem5-c8222cc-linux-x86_64-20261008');bundle.mkdir(parents=True,exist_ok=True)
for part in ['bin','python/lib','source','evidence','licenses']:(bundle/part).mkdir(parents=True,exist_ok=True)
shutil.copy2(identity['path'],bundle/'bin/gem5.opt')
assert hashlib.file_digest((bundle/'bin/gem5.opt').open('rb'),'sha256').hexdigest()==identity['sha256']
runtime=pathlib.Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/python')
shutil.copy2(runtime/'lib/libpython3.12.so.1.0',bundle/'python/lib/libpython3.12.so.1.0')
shutil.copytree(runtime/'lib/python3.12',bundle/'python/lib/python3.12',dirs_exist_ok=True,ignore=shutil.ignore_patterns('site-packages','__pycache__','*.pyc'))
shutil.copy2(runtime/'lib/python3.12/LICENSE.txt',bundle/'licenses/CPython-LICENSE.txt')
source=pathlib.Path(identity['source_consistency_after']['extraction_root'])/'gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9'
for name in ['COPYING','LICENSE']:shutil.copy2(source/name,bundle/'licenses'/('gem5-'+name))
shutil.copy2(scratch/'gem5-c8222cc.tar.gz',bundle/'source/gem5-c8222cc.tar.gz')
shutil.copy2(proof/'binary-identity.json',bundle/'binary-identity.json')
for name in ['build-20261008','resume-20261008','link-recovery-20261008']:
 shutil.copytree(repo/'docs/validation/m3-fs'/name,bundle/'evidence'/name,dirs_exist_ok=True)
for name in ['GEM5-REVIEW.md','CROSS-ELF-REVIEW.md']:
 f=repo/'docs/validation/m3-fs'/name
 if f.is_file():shutil.copy2(f,bundle/'evidence'/name)
wrapper=bundle/'bin/run-gem5'
wrapper.write_text('''#!/bin/sh\nset -eu\nbundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)\nexport LD_LIBRARY_PATH="$bundle_dir/python/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\nexport PYTHONHOME="$bundle_dir/python"\nexec "$bundle_dir/bin/gem5.opt" "$@"\n''')
wrapper.chmod(0o755)
clean={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'}
r=subprocess.run(['timeout','60',str(wrapper),'--build-info'],env=clean,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
(proof/'package-clean-env-build-info.log').write_text(r.stdout+r.stderr)
(proof/'package-clean-env-build-info-exit-code.txt').write_text(str(r.returncode)+'\n')
ldenv=dict(clean);ldenv['LD_LIBRARY_PATH']=str(bundle/'python/lib')
ld=subprocess.run(['ldd',str(bundle/'bin/gem5.opt')],env=ldenv,capture_output=True,text=True)
(proof/'package-clean-env-ldd.log').write_text(ld.stdout+ld.stderr)
(proof/'package-clean-env-ldd-exit-code.txt').write_text(str(ld.returncode)+'\n')
clean_pass=r.returncode==0 and 'gem5 version 25.1.0.1' in r.stdout and ld.returncode==0 and 'not found' not in ld.stdout+ld.stderr
package_metadata={'schema':'openrx-local-gem5-reuse-package-v1','kind':'locally compiled upstream simulator; not a GitHub CI artifact','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_revision':identity['source_revision'],'source_archive_url':'https://codeload.github.com/gem5/gem5/tar.gz/'+identity['source_revision'],'source_archive_sha256':identity['source_consistency_after']['archive_sha256'],'source_archive_size_bytes':(bundle/'source/gem5-c8222cc.tar.gz').stat().st_size,'binary_original_sha256':identity['sha256'],'binary_original_size_bytes':identity['size_bytes'],'binary_original_stripped':False,'canonical_config_sha256':identity['canonical_config_sha256'],'build_recipe_difference':'--limit-ld-memory-usage supported upstream linker option, --without-tcmalloc; original canonical source/ISA/config/objects unchanged','clean_environment_wrapper_preflight_passed':clean_pass,'clean_environment':clean,'preflight_commands':{'build_info':['timeout','60',str(wrapper),'--build-info'],'ldd':['ldd',str(bundle/'bin/gem5.opt')]},'preflight_returncodes':{'build_info':r.returncode,'ldd':ld.returncode},'bundled_python':{'version':'3.12.14','shared_library':'python/lib/libpython3.12.so.1.0','stdlib':'python/lib/python3.12','excluded':['site-packages','__pycache__','*.pyc']},'host_requirements':['Linux x86_64','glibc 2.39 and GNU C++ runtime compatible with Ubuntu 24.04 build host','system libz, libstdc++, libm, libgcc_s, libc and transitive libpthread/librt/libdl/libutil; actual ldd logs retained'],'guest_resources_included':False,'guest_execution_result_included':False,'licensing':'Unmodified upstream LICENSE/COPYING and original source archive preserve complete per-file upstream notices. Bundled CPython LICENSE.txt retained.'}
if not clean_pass:
 wrapper.unlink()
 package_metadata['wrapper_omitted_reason']='Clean environment preflight failed; use exact original native-library environment from binary-identity.json instead.'
(package_file:=bundle/'package-provenance.json').write_text(json.dumps(package_metadata,indent=2)+'\n')
(proof/'package-provenance.json').write_text(package_file.read_text())
(bundle/'README.md').write_text('''# Local upstream gem5 reusable build\n\nThis package preserves the original unstripped gem5 25.1.0.1 executable compiled locally from upstream revision c8222cc67a399bfc01e8658dd14b30d5bfd634f9. It is not a GitHub CI artifact. Source and configuration consistency, complete source-build attempts, the prior linker OOM and the successful supported low-memory link retry are recorded under evidence/. The executable SHA-256 and size are recorded in binary-identity.json and package-provenance.json.\n\nRun `bin/run-gem5 --build-info` after extraction. The wrapper locates its own bundled Python shared library and standard library using relative paths. A clean environment preflight passed on this Ubuntu 24.04 x86_64 host; portability to other operating systems, CPU architectures or older native libraries has not been tested. System glibc, zlib and GNU C++ runtime requirements are recorded in the actual loader logs.\n\nThe original binary has not been stripped or modified. The immutable 16.45 MB upstream source archive preserves all original per-file copyright/license notices; top-level upstream notices and CPython's license are also supplied under licenses/. This package contains no guest kernel, firmware, disk image or guest execution result. Reuse the separately pinned project resources for a full-system run.\n\nThe initial source build used the canonical RISC-V config, six workers and `--without-tcmalloc`. Final linking used the upstream-supported `--limit-ld-memory-usage`, which adds GNU ld `--no-keep-memory` without source or Kconfig changes. See complete commands, environment and build outcome records under evidence/.\n''')
for name in ['package-clean-env-build-info.log','package-clean-env-build-info-exit-code.txt','package-clean-env-ldd.log','package-clean-env-ldd-exit-code.txt','package-provenance.json']:
 shutil.copy2(proof/name,bundle/'evidence/link-recovery-20261008'/name)
files={}
for f in sorted(bundle.rglob('*')):
 if f.is_file():files[str(f.relative_to(bundle))]={'size_bytes':f.stat().st_size,'mode':oct(f.stat().st_mode & 0o777),'sha256':hashlib.file_digest(f.open('rb'),'sha256').hexdigest()}
(bundle/'package-manifest.json').write_text(json.dumps(files,indent=2)+'\n')
archive=bundle.parent/(bundle.name+'.tar.gz');started=time.monotonic()
print(json.dumps({'stage':'package-preflight','clean_environment_wrapper_preflight_passed':clean_pass,'files':len(files),'uncompressed_files_bytes':sum(v['size_bytes'] for v in files.values()),'archive_target':str(archive)}),flush=True)
with tarfile.open(archive,'w:gz',compresslevel=1) as tar:tar.add(bundle,arcname=bundle.name)
result={'archive':str(archive),'archive_size_bytes':archive.stat().st_size,'archive_sha256':hashlib.file_digest(archive.open('rb'),'sha256').hexdigest(),'packaging_elapsed_seconds':time.monotonic()-started,'clean_environment_wrapper_preflight_passed':clean_pass,'original_binary_sha256':identity['sha256'],'source_archive_sha256':package_metadata['source_archive_sha256'],'package_manifest_sha256':hashlib.file_digest((bundle/'package-manifest.json').open('rb'),'sha256').hexdigest()}
(proof/'package-archive.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
if not clean_pass:raise SystemExit(1)
