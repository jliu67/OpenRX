import pathlib,os,json,subprocess,hashlib,datetime
p=pathlib.Path('/tmp/openrx-gem5-source/link-recovery-20261008');s=pathlib.Path('/tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9');b=s/'build/RISCV/gem5.opt'
assert int((p/'recovery-exit-code.txt').read_text())==0,'Build did not succeed'
assert os.access(b,os.X_OK),'Output is not executable'
env=dict(os.environ);env['LD_LIBRARY_PATH']='/tmp/openrx-gem5-source/native-libs:/tmp/openrx-gem5-source/apt-root/usr/lib/x86_64-linux-gnu'
commands={'build-info':['timeout','60',str(b),'--build-info'],'ldd':['ldd',str(b)],'elf-header':['readelf','-h',str(b)],'elf-dynamic':['readelf','-d',str(b)],'elf-sections':['readelf','-S',str(b)],'file':['file',str(b)]}
result={'schema':'openrx-gem5-linked-binary-identity-v1','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':str(b),'source_revision':'c8222cc67a399bfc01e8658dd14b30d5bfd634f9','sha256':hashlib.file_digest(b.open('rb'),'sha256').hexdigest(),'size_bytes':b.stat().st_size,'mode':oct(b.stat().st_mode & 0o777),'stripped_copy_size_bytes':None,'original_binary_stripped':False,'native_library_environment':env['LD_LIBRARY_PATH'],'command_results':{}}
for name,argv in commands.items():
 r=subprocess.run(argv,capture_output=True,text=True,env=env)
 (p/(name+'.log')).write_text(r.stdout+r.stderr)
 (p/(name+'-exit-code.txt')).write_text(str(r.returncode)+'\n')
 result['command_results'][name]={'argv':argv,'returncode':r.returncode,'log':name+'.log','log_sha256':hashlib.sha256((r.stdout+r.stderr).encode()).hexdigest()}
result['build_info_version_matches']='25.1.0.1' in (p/'build-info.log').read_text()
result['ldd_all_dependencies_found']='not found' not in (p/'ldd.log').read_text()
result['needed_shared_libraries']=[x.split('[',1)[1].split(']',1)[0] for x in (p/'elf-dynamic.log').read_text().splitlines() if '(NEEDED)' in x]
result['source_consistency_after']=json.loads((p/'source-consistency-after.json').read_text())
result['canonical_config_sha256']=hashlib.sha256((s/'build/RISCV/gem5.build/config').read_bytes()).hexdigest()
result['identity_verified']=all(v['returncode']==0 for v in result['command_results'].values()) and result['build_info_version_matches'] and result['ldd_all_dependencies_found'] and result['source_consistency_after']['status']=='pass' and result['canonical_config_sha256']=='e8b427ddf7a991883020766f90f8f2a08bed769f831d43d448c8f68845ab39b5'
(p/'binary-identity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['identity_verified','sha256','size_bytes','mode','build_info_version_matches','needed_shared_libraries','canonical_config_sha256']},indent=2))
if not result['identity_verified']:raise SystemExit(1)
