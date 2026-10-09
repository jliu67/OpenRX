#!/usr/bin/env python3
"""Read retained migration evidence; never submit, recover, activate or simulate.

The only writes are exclusive reviewer records in a new output directory.  Waiting
observes the already authorized pipeline; it creates no execution request.  The
original runtime extractor and strict nine-case validator remain authoritative.
"""
import argparse
import ast
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
R = Path('$OPENRX_LOCAL_ROOT')
E = R / 'migrations/20261009'
S = R / 'checkouts/execution-b4b5ffc'
ORIGINAL = Path('$OPENRX_ORIGINAL_CHECKOUT')
SOURCE_COMMIT = 'b4b5ffc5c5ee3f59e0e862a6979d265fd410d726'
ORIGINAL_COMMIT = '3a7ff8fd3529dfc7e0fd46d28ee90b267b8df2f2'
UPSTREAM_COMMIT = 'c8222cc67a399bfc01e8658dd14b30d5bfd634f9'
GROOT = R / 'builds/gem5-rebuild-03' / ('gem5-' + UPSTREAM_COMMIT)
G = GROOT / 'build/RISCV/gem5.opt'
B = E / 'build-attempt-03'
RES = R / 'artifacts/guest-resources-ranged-20261009'
ELF = R / 'artifacts/guest-20261008/openrx-runtime-probe'
RUNNER = R / 'releases/runner-v1-988cf13f/local_execution.py'
RUNNER_SHA = '988cf13f4c9c954388fb7e9d44fda632910fde41ab78392294280f176c674882'
SPEC = R / 'requests/spec-issue-27-local-runtime-b4b5ffc-attempt-01.json'
SPEC_SHA = 'd11d6f4e5043e3d51a73a0ecf52fc8aa95eb459c6546e46d4136f78013da7972'
KEY = 'issue-27-local-runtime-b4b5ffc-attempt-01'
CONFIG_SHA = 'f839a59b33a593a63c3f5bef53bfac468df0619fcc46c3583c76b08b2d08564c'
ORIGINAL_CONFIG_SHA = 'e8b427ddf7a991883020766f90f8f2a08bed769f831d43d448c8f68845ab39b5'
P = R / 'toolchains/ubuntu22-20261009/pinned-packages.json'
P_SHA = 'c3948ff082235733e12ec2264a5c050936e4fef8547446c9389cf98036b86676'
PIPELINE = E / 'validate_when_ready_v3.py'
PIPELINE_SHA = 'ace55beda986a44a931b27cc05bcf16590d63ae0cfce1504ec72059cd1c01910'
MODEL_SHA = '5608189a6f2a41a45e86f117f10af8408ab87ea1aab600294a336ab31375e7c5'
RESOURCE_SHA = '67c3838d04b617b3a4f34a874f84cc2c5517eca51c9049456bc6df19312404bb'
WRAPPER_SHA = '5c275bf3da88417970b2219614a39d136fc046d7c6c692fcf4025debb867060e'
VALIDATOR_SHA = '99f178b3f8ad84cf0b7542b108338a498a3d23d33a5738839eff96916c284617'
ELF_SHA = '8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac'
ARCHIVE_SHA = '0f4102a3ece810342b0a0124d44f9cb6a5b0aba08b436998b5e5069ab35bdba3'
MAX_TICKS = 10000000000000
CRITERIA = {
    'scope': 'distinct local gem5 rebuild and runtime-only nine-case functional smoke',
    'science': 'Original extractor and native_runtime_probe.validate_output, expect_architecture=riscv64',
    'completion': 'exit0, empty framed probe stderr, guest-complete, ordered hypercalls1/2/3',
    'provenance': 'exact source/config/archive/toolchain/loader/guest/input and full output receipt bindings',
    'model': 'single scalar RV64 AtomicSimpleCPU,1GHz,4GiB,16KiB L1d/L1i,256KiB L2,read-only base image with COW',
    'not_accepted': ['full RandomX gem5 matrix', 'full dataset', 'timing calibration', 'power',
                     'scientific checkpoint resume', 'migration completion', 'LOCAL_ACTIVE'],
    'waiting': 'No wall deadline; observe existing pipeline only. No jobs, transitions or GitHub writes.',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def syncdir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def newfile(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    syncdir(path.parent)


def newjson(path, value):
    newfile(path, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def json_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON field: ' + key)
        result[key] = value
    return result


def readjson(path):
    return json.loads(path.read_text(), object_pairs_hook=json_object)


def digest(path):
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), 'Not a regular evidence file: ' + str(path))
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
        after = os.fstat(stream.fileno())
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
            'Evidence changed while being read: ' + str(path))
    return {'path': str(path.resolve()), 'bytes': after.st_size, 'sha256': h.hexdigest()}


def sha(path):
    return digest(path)['sha256']


def command(argv, cwd=None, env=None):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True)
    require(result.returncode == 0, 'Read-only command failed: ' + repr(argv) + ': ' + result.stderr)
    return result.stdout


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inspect_model(config, resources, readfile, m5out):
    """Inspect actual SimObject config without importing/executing fs.py."""
    board = config['board']
    require(config['full_system'] is True and board['mem_mode'] == 'atomic', 'Wrong full-system memory mode')
    cores = board['processor']['cores']
    require(len(cores) == 1, 'Wrong actual CPU count')
    core = cores[0]['core']
    require(core['type'] == 'BaseAtomicSimpleCPU' and core['cxx_class'] == 'gem5::AtomicSimpleCPU',
            'Wrong actual CPU model')
    require(core['cpu_id'] == 0 and core['numThreads'] == 1, 'Wrong actual core/thread configuration')
    isa = core['isa']
    require(len(isa) == 1 and isa[0]['type'] == 'RiscvISA' and isa[0]['riscv_type'] == 'RV64'
            and isa[0]['enable_rvv'] is False, 'Actual guest is not scalar RV64')
    clock = board['clk_domain']
    require(clock['type'] == 'SrcClockDomain' and clock['clock'] == [1000]
            and core['clk_domain'] == 'board.clk_domain', 'Wrong actual 1GHz core clock')
    require(board['mem_ranges'] == ['2147483648:6442450944'], 'Wrong actual 4GiB guest memory')
    hierarchy = board['cache_hierarchy']
    sizes = {'l1d-cache-0': 16384, 'l1i-cache-0': 16384, 'l2-cache-0': 262144}
    for name, size in sizes.items():
        require(hierarchy[name]['type'] == 'Cache' and hierarchy[name]['size'] == size,
                'Wrong actual cache configuration: ' + name)
    image = board['disk']['vio']['image']
    require(image['type'] == 'CowDiskImage' and image['read_only'] is False
            and image['child']['type'] == 'RawDiskImage' and image['child']['read_only'] is True
            and image['child']['image_file'] == str(resources / 'ubuntu.img'), 'Base disk is not read-only/COW')
    workload = board['workload']
    require(workload['type'] == 'RiscvBootloaderKernelWorkload'
            and workload['bootloader_filename'] == str(resources / 'opensbi')
            and workload['object_file'] == str(resources / 'vmlinux'), 'Wrong actual firmware/kernel binding')
    require(workload['command_line'] == 'console=ttyS0 root=/dev/vda1 disk_device=/dev/vda rw init=/sbin/gem5_init.sh no_systemd',
            'Wrong actual guest command line')
    require(board['readfile'] == str(readfile) and workload['dtb_filename'] == str(m5out / 'device.dtb'),
            'Wrong actual readfile/device tree paths')
    require(workload['wait_for_remote_gdb'] is False, 'Unexpected remote debugger wait')
    return {'cpu': core['cxx_class'], 'cores': 1, 'rvv': False, 'clock_period_ticks': clock['clock'][0],
            'ram_bytes': 4294967296, 'cache_sizes_bytes': sizes, 'base_image_read_only': True, 'cow': True}


def loader_entries(raw):
    entries = {}
    require('not found' not in raw, 'Missing dynamic library')
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith('linux-vdso.so.'):
            continue
        linked = re.fullmatch(r'\s*(\S+) => (/\S+) \(0x[0-9a-fA-F]+\)', line)
        direct = re.fullmatch(r'\s*(/\S+) \(0x[0-9a-fA-F]+\)', line)
        require(linked is not None or direct is not None, 'Unrecognized loader entry: ' + line)
        name, path = (linked[1], linked[2]) if linked else (Path(direct[1]).name, direct[1])
        require(name not in entries, 'Duplicate loader SONAME: ' + name)
        entries[name] = {'path': str(Path(path).resolve(strict=True)), 'interpreter': linked is None}
    require(entries, 'Empty dynamic loader closure')
    return entries


class Review:
    def __init__(self, out):
        self.out = out
        self.checks = []

    def passed(self, name, evidence):
        record = {'at': now(), 'check': name, 'passed': True, 'evidence': evidence}
        self.checks.append(record)
        newjson(self.out / ('check-%02d.json' % len(self.checks)), record)
        print('PASS ' + name, flush=True)

    def check_fixed(self):
        pins = {
            RUNNER: RUNNER_SHA, SPEC: SPEC_SHA, PIPELINE: PIPELINE_SHA, P: P_SHA,
            S / 'simulator/gem5/run.py': WRAPPER_SHA, S / 'simulator/gem5/fs.py': MODEL_SHA,
            S / 'simulator/gem5/resources.json': RESOURCE_SHA, S / 'tests/native_runtime_probe.py': VALIDATOR_SHA,
            R / 'artifacts/gem5-source-c8222cc.tar.gz': ARCHIVE_SHA,
            E / 'source-inventory.json': 'ef04d97b22ac53e673bddee0458c3f00c5d08b846c996c3f80b2135f95c0cadf',
            E / 'original-tracked-sha256.json': 'a7d58ca2b8de7828011cc4213309f8059c68177036b57ea0c318fee4177c6fef',
            ELF: ELF_SHA,
        }
        observations = []
        for path, expected in pins.items():
            item = digest(path)
            require(item['sha256'] == expected, 'Fixed review binding drift: ' + str(path))
            observations.append(item)
        self.spec = readjson(SPEC)
        require(self.spec['request_key'] == KEY and self.spec['source_commit'] == SOURCE_COMMIT
                and self.spec['runner_sha256'] == RUNNER_SHA and self.spec['wall_timeout_seconds'] is None,
                'Owner request semantics differ')
        self.passed('fixed_reviewed_bindings', observations)
        sys.path.insert(0, str(S))
        from simulator.gem5 import run, prepare, bundle
        self.wrapper, self.prepare, self.bundle = run, prepare, bundle
        self.runner = import_file('openrx_independent_runner', RUNNER)

    def check_sources(self):
        require(command(['git', 'rev-parse', 'HEAD'], ORIGINAL).strip() == ORIGINAL_COMMIT,
                'Original checkout commit changed')
        original = readjson(E / 'original-tracked-sha256.json')
        require(original['commit'] == ORIGINAL_COMMIT and len(original['files']) == 694, 'Original inventory identity changed')
        for item in original['files']:
            actual = digest(ORIGINAL / item['path'])
            require(actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes'],
                    'Original scientific/project bytes changed: ' + item['path'])
        inventory = readjson(E / 'source-inventory.json')
        require(inventory['source_commit'] == UPSTREAM_COMMIT and inventory['archive_sha256'] == ARCHIVE_SHA
                and len(inventory['files']) == 10933, 'Upstream source inventory identity changed')
        for item in inventory['files']:
            actual = digest(GROOT / item['path'])
            require(actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes'],
                    'Actual rebuild source changed: ' + item['path'])
        require(command(['git', 'rev-parse', 'HEAD'], S).strip() == SOURCE_COMMIT, 'Execution source HEAD drift')
        require(not command(['git', 'status', '--porcelain', '--untracked-files=all'], S).strip(), 'Execution source is dirty')
        tracked = command(['git', 'ls-files', '-s'], S).splitlines()
        require(len(tracked) == 890, 'Reviewed execution source file count changed')
        for line in tracked:
            prefix, relative = line.split('\t', 1)
            mode, blob, stage = prefix.split()
            require(mode in {'100644', '100755'} and stage == '0', 'Unexpected tracked source object')
            path = S / relative
            raw = path.read_bytes()
            require(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == blob,
                    'Execution file differs from Git object: ' + relative)
        require(all(not p.is_symlink() and not (p.stat().st_mode & 0o222) for p in [S, *S.rglob('*')]),
                'Frozen execution checkout has writable entries or symlinks')
        scientific_paths = ['simulator/gem5/fs.py', 'simulator/gem5/resources.json', 'simulator/gem5/prepare.py',
                            'simulator/gem5/bundle.py', 'tests/native_runtime_probe.py', 'tests/native_riscv_probe.py',
                            'simulator/runtime-probe/main.c', 'simulator/probe/main.cpp']
        for relative in scientific_paths:
            require((S / relative).read_bytes() == (ORIGINAL / relative).read_bytes(),
                    'Scientific implementation/criterion changed: ' + relative)
        old_ast = ast.parse((ORIGINAL / 'simulator/gem5/run.py').read_text())
        new_ast = ast.parse((S / 'simulator/gem5/run.py').read_text())
        old_defs = {n.name: ast.dump(n, include_attributes=False) for n in old_ast.body if isinstance(n, ast.FunctionDef)}
        new_defs = {n.name: ast.dump(n, include_attributes=False) for n in new_ast.body if isinstance(n, ast.FunctionDef)}
        require(old_defs.keys() == new_defs.keys(), 'Wrapper function set changed')
        require([n for n in old_defs if old_defs[n] != new_defs[n]] == ['run_process'],
                'Wrapper scientific extraction/main changed beyond reviewed process control')
        self.passed('original_and_actual_rebuild_sources_preserved', {
            'original_files': 694, 'upstream_files': 10933, 'execution_git_files': 890,
            'execution_source_commit': SOURCE_COMMIT, 'upstream_commit': UPSTREAM_COMMIT,
            'scientific_files_equal_original': scientific_paths, 'only_changed_wrapper_function': 'run_process'})

    def check_build(self):
        self.build = readjson(B / 'build-result.json')
        command_record = readjson(B / 'build-command.json')
        require(self.build['returncode'] == 0 and self.build['source_changed'] == []
                and self.build['build-info_exit'] == 0 and self.build['loader_exit'] == 0,
                'Completed build evidence failed')
        require(self.build['config_sha256_after'] == CONFIG_SHA, 'Build completion config changed')
        self.binary = digest(G)
        require(self.binary['sha256'] == self.build['binary_sha256'] and self.binary['bytes'] == self.build['binary_bytes'],
                'Actual distinct simulator binary differs from completed build')
        require(self.binary['sha256'] != '3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6',
                'Distinct rebuild unexpectedly claims unavailable original identity')
        self.bundle.elf_host(G)
        generated = G.parent / 'gem5.build/config'
        require(sha(generated) == CONFIG_SHA and sha(B / 'canonical-config') == CONFIG_SHA,
                'Actual/retained generated config drift')
        canonical = ORIGINAL / 'docs/validation/m3-fs/build-20261008/canonical-config'
        require(sha(canonical) == ORIGINAL_CONFIG_SHA, 'Original canonical config drift')
        optional = {b'HAVE_PNG=y\n', b'HAVE_HDF5=y\n', b'HAVE_PROTOBUF=y\n'}
        require(b''.join(line for line in generated.read_bytes().splitlines(keepends=True) if line not in optional)
                == canonical.read_bytes(), 'Generated config differs beyond reviewed optional host dependencies')
        self.bundle.check_config(generated.read_text())
        self.bundle.check_build_info((B / 'build-info.log').read_text())
        require(command_record['source_commit'] == UPSTREAM_COMMIT and command_record['source_archive_sha256'] == ARCHIVE_SHA,
                'Build command upstream provenance mismatch')
        self.passed('completed_distinct_simulator_rebuild', {
            'binary': self.binary, 'build_result': digest(B / 'build-result.json'),
            'build_command': command_record, 'generated_config_sha256': CONFIG_SHA,
            'original_generated_config_sha256': ORIGINAL_CONFIG_SHA,
            'only_optional_host_dependency_additions': ['HAVE_PNG=y', 'HAVE_HDF5=y', 'HAVE_PROTOBUF=y'],
            'original_binary_restored': False, 'scientific_model_criteria_changed': False})

    def check_dependencies(self):
        pins = readjson(P)
        require(len(pins['pins']) == 41 and len(pins['archives']) == 41, 'Unexpected core pin count')
        installed = []
        for pin in pins['pins']:
            actual = command(['dpkg-query', '-W', '-f=${Version}', pin['package']]).strip()
            require(actual == pin['version'], 'Installed package version drift: ' + pin['package'])
            installed.append({'package': pin['package'], 'version': actual})
        for item in pins['archives']:
            actual = digest(P.parent / item['file'])
            require(actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes'],
                    'Archived package integrity drift: ' + item['file'])
        self.profile_dir = R / ('toolchains/gem5-runtime-' + self.binary['sha256'][:12])
        profile_path = self.profile_dir / 'runtime-libraries.json'
        self.profile = readjson(profile_path)
        require(self.profile['binary_sha256'] == self.binary['sha256']
                and self.profile['core_package_manifest_sha256'] == P_SHA
                and self.profile['installed_core_pins_verified'] == 41, 'Runtime profile provenance drift')
        expected = {}
        for item in self.profile['libraries']:
            require(item['soname'] not in expected, 'Duplicate retained library SONAME')
            expected[item['soname']] = item
            require(item['pinned_copy'] == str(self.profile_dir / 'lib' / item['soname']), 'Pinned library path drift')
            for path in [Path(item['pinned_copy']), Path(item['host_path'])]:
                actual = digest(path)
                require(actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes'],
                        'Pinned/host runtime library drift: ' + str(path))
            require(not (Path(item['pinned_copy']).stat().st_mode & 0o222), 'Pinned copy is writable')
        require(sum(item['interpreter'] is True for item in expected.values()) == 1, 'Missing/ambiguous host ELF interpreter')
        retained = loader_entries(self.profile['pinned_ldd'])
        require(set(retained) == set(expected), 'Retained loader closure SONAME set drift')
        self.env = dict(self.runner.DEFAULT_ENV, LD_LIBRARY_PATH=str(self.profile_dir / 'lib'))
        actual_raw = command(['ldd', str(G)], env=self.env)
        newfile(self.out / 'actual-pinned-ldd.log', actual_raw.encode())
        observed = loader_entries(actual_raw)
        require(set(observed) == set(expected), 'Actual pinned loader closure SONAME set drift')
        for name, actual in observed.items():
            item = expected[name]
            require(actual['interpreter'] is item['interpreter'] and sha(Path(actual['path'])) == item['sha256'],
                    'Actual loader library/interpreter differs: ' + name)
            target = item['host_path'] if item['interpreter'] else item['pinned_copy']
            require(actual['path'] == str(Path(target).resolve()), 'Actual loader path is not approved profile: ' + name)
            require(retained[name]['path'] == actual['path'] and retained[name]['interpreter'] is actual['interpreter'],
                    'Recorded loader path differs: ' + name)
        info = command([str(G), '--build-info'], env=self.env)
        newfile(self.out / 'actual-pinned-build-info.log', info.encode())
        self.bundle.check_build_info(info)
        self.bundle.check_build_info((self.profile_dir / 'pinned-build-info.log').read_text())
        self.passed('core_toolchain_and_actual_pinned_loader_verified', {
            'core_packages': installed, 'archived_debs_verified': 41, 'profile': digest(profile_path),
            'actual_loader': observed, 'actual_build_info': digest(self.out / 'actual-pinned-build-info.log'),
            'limitation': 'Host ELF interpreter and current core pins verified; no offline/hermetic host closure claimed'})

    def check_guest_inputs(self):
        manifest = readjson(S / 'simulator/gem5/resources.json')
        observations = []
        for item in manifest['resources']:
            observed = self.prepare.verify(RES / item['filename'], item)
            observations.append(dict(item, observed=observed))
        self.guest_resources = observations
        info = self.wrapper.elf_info(ELF)
        require(info['sha256'] == ELF_SHA and info['bytes'] == 13760, 'Recovered runtime ELF identity drift')
        self.passed('expected_guest_assets_verified', {'resources': observations, 'runtime_elf': info,
                                                      'recovered_exact_original_elf': True})

    def check_preflight(self):
        path = E / 'local-validation-preflight.json'
        self.preflight = readjson(path)
        p = self.preflight
        require(p['state'] == 'LOCAL_VALIDATING' and p['source_commit'] == SOURCE_COMMIT
                and p['runner_sha256'] == RUNNER_SHA and p['request_key'] == KEY and p['request_spec_sha256'] == SPEC_SHA,
                'Preflight source/runner/request binding drift')
        require(p['build'] == self.build and p['build_result_sha256'] == sha(B / 'build-result.json'), 'Preflight completed build binding drift')
        require(p['build_unit']['Result'] == 'success' and p['build_unit']['ExecMainStatus'] == '0'
                and p['original_binary_restored'] is False and p['new_binary_pinned'] is True,
                'Preflight build/identity claim rejected')
        require(p['guest_resources_verified'] is True and p['guest_runtime_sha256'] == ELF_SHA
                and p['runtime_library_profile_sha256'] == sha(self.profile_dir / 'runtime-libraries.json')
                and p['core_package_pins_verified'] == 41, 'Preflight guest/dependency binding drift')
        journal = self.runner.events(R / 'state/events.jsonl')
        evidence = digest(path)
        transitions = [item for item in journal if item.get('state') == 'LOCAL_VALIDATING' and item.get('evidence') == evidence]
        require(len(transitions) == 1, 'No unique authoritative preflight-backed LOCAL_VALIDATING transition')
        require(self.runner.current_state(R) == 'LOCAL_VALIDATING', 'Actual runtime review requires LOCAL_VALIDATING, not activation')
        self.passed('evidence_backed_local_validating_transition', {
            'preflight': evidence, 'authoritative_transition': transitions[0], 'observed_state': 'LOCAL_VALIDATING'})

    def check_execution(self):
        self.capture = readjson(E / 'runtime-capture-summary.json')
        submitted = readjson(E / 'runtime-execution-id.json')
        self.execution_id = self.capture['execution_id']
        require(self.runner.ID_RE.fullmatch(self.execution_id) and submitted['execution_id'] == self.execution_id,
                'Runtime execution identity drift')
        require(self.capture['request_key'] == KEY and self.capture['migration_complete'] is False,
                'Capture request/acceptance status drift')
        self.directory = R / 'executions' / self.execution_id
        self.manifest = readjson(self.directory / 'manifest.json')
        m = self.manifest
        require(m['schema'] == 'openrx.local.execution.v1' and m['execution_id'] == self.execution_id
                and m['request_key'] == KEY and m['kind'] == 'validation'
                and m['validation_scope'] == 'guest-runtime-smoke' and m['migration_state'] == 'LOCAL_VALIDATING',
                'Execution admission scope/identity drift')
        require(m['cwd'] == str(S) and m['env'] == self.env and m['scientific_acceptance'] == 'unverified',
                'Execution environment/scientific status drift')
        require(m['runner'] == self.runner.digest(RUNNER) and sha(self.directory / 'runner.py') == RUNNER_SHA,
                'Execution runner release/snapshot drift')
        self.payload = self.directory / 'payload'
        expected_argv = [str(Path('/usr/bin/python3').resolve()), 'simulator/gem5/run.py', '--gem5', str(G),
                         '--resources', str(RES), '--runtime-binary', str(ELF), '--output-dir', str(self.payload),
                         '--max-ticks', str(MAX_TICKS), '--stop-file', str(self.directory / 'stop.request')]
        require(m['argv'] == expected_argv, 'Execution argv differs from reviewed runtime-only request')
        expected_inputs = {str(p) for p in [G, ELF, RES / 'opensbi', RES / 'vmlinux', RES / 'ubuntu.img', self.profile_dir, SPEC]}
        require(len(m['inputs']) == 7 and {i['path'] for i in m['inputs']} == expected_inputs,
                'Missing/duplicate/extra input binding')
        require(len(m['sources']) == 1 and m['sources'][0]['path'] == str(S), 'Missing/extra source binding')
        expected_resources = {'MemoryMax': '6G', 'MemorySwapMax': '1G', 'CPUQuota': '200%', 'TasksMax': 256,
                              'Nice': 10, 'NoNewPrivileges': True, 'global_slots': 1}
        require(m['resources'] == expected_resources and m['resource_lock'] == str(R / 'locks/execution.lock'),
                'Execution resource limit/locking policy differs')
        require(m['unit'] == 'openrx-' + self.execution_id + '.service', 'Execution service name differs')
        self.runner.check_bindings(R, self.directory, m)
        self.integrity = self.runner.verify(R, self.execution_id)
        require(self.integrity['integrity_verified'] is True and self.integrity['status'] == 'PROCESS_EXITED',
                'Actual retained execution integrity/status rejected')
        self.receipt = readjson(self.directory / 'receipt.json')
        self.process = readjson(self.directory / 'process-result.json')
        require(self.process['status'] == 'PROCESS_EXITED' and self.process['returncode'] == 0
                and self.process['signals'] == [] and self.receipt['process'] == self.process,
                'Actual child failed or was interrupted')
        require(self.receipt['resume_allowed'] is False and self.receipt['systemd']['SERVICE_RESULT'] == 'success',
                'Finalization manager result/resume claim rejected')
        require(self.capture['receipt_sha256'] == sha(self.directory / 'receipt.json'), 'Capture receipt binding drift')
        submission = readjson(self.directory / 'submission-result.json')
        require(submission['returncode'] == 0, 'Service submission failed')
        launch = readjson(self.directory / 'submission-command.json')['argv']
        require(launch == self.runner.systemd_command(R, self.directory, m), 'Service command/resource/finalizer properties drift')
        events = self.runner.events(self.directory / 'events.jsonl')
        statuses = [item.get('status') for item in events]
        require(statuses.count('RUNNING') == 1 and statuses.count('CHILD_STARTED') == 1
                and statuses.count('PROCESS_EXITED') == 1 and statuses.count('FINALIZED') == 1,
                'Execution event history missing/duplicate lifecycle events')
        require(statuses.index('RUNNING') < statuses.index('CHILD_STARTED') < statuses.index('PROCESS_EXITED') < statuses.index('FINALIZED'),
                'Execution lifecycle event order inconsistent')
        current_unit = self.runner.unit_status(m['unit'])
        require(current_unit.get('ActiveState') not in {'active', 'activating', 'deactivating'}, 'Execution service remains live')
        self.passed('actual_execution_admission_and_retained_integrity', {
            'execution_id': self.execution_id, 'manifest': digest(self.directory / 'manifest.json'),
            'receipt': digest(self.directory / 'receipt.json'), 'process': self.process,
            'lifecycle_statuses': statuses, 'unit_observation': current_unit,
            'unit_limitation': 'If transient unit is not found, manager defaults are not terminal service evidence',
            'integrity_verification': self.integrity, 'resource_limits': expected_resources,
            'all_inputs_and_source_bound_before_launch_rechecked_now': True})

    def check_actual_runtime(self):
        report_path = self.payload / 'report.json'
        self.report = readjson(report_path)
        report = self.report
        require(self.capture['report_sha256'] == sha(report_path) and self.capture['runtime_status'] == 'pass'
                and self.capture['runtime_validated'] is True, 'Candidate capture report mismatch/failure')
        expected = {'schema_version': 1, 'evidence_class': 'full-system-functional', 'status': 'pass',
                    'boot_observed': True, 'runtime_validated': True, 'hash_controls_requested': False,
                    'full_dataset': False, 'timing_calibrated': False, 'power_measured': False,
                    'timeout_seconds': None, 'gem5_source_commit_expected': UPSTREAM_COMMIT,
                    'source_build_provenance_required_separately': True, 'max_ticks_per_simulate_call': MAX_TICKS,
                    'returncode': 0}
        for name, value in expected.items():
            require(type(report.get(name)) is type(value) and report[name] == value, 'Actual report field mismatch: ' + name)
        require(not report.get('interrupted') and 'error' not in report, 'Actual report records failure/interruption')
        require(report['gem5_binary_sha256'] == self.binary['sha256'] and report['config_sha256'] == MODEL_SHA
                and report['resource_manifest_sha256'] == RESOURCE_SHA, 'Actual report simulator/model/resource binding drift')
        require(report['guest_binaries'] == {'runtime': self.wrapper.elf_info(ELF)}
                and report['resources'] == self.guest_resources, 'Actual report guest bindings differ')
        readfile = self.payload / 'guest.sh'
        require(readfile.read_bytes() == self.wrapper.guest_script({'runtime': ELF}).encode(),
                'Actual readfile differs from unchanged exact runtime payload generator')
        require(report['readfile_sha256'] == sha(readfile), 'Actual readfile hash drift')
        m5out = self.payload / 'm5out'
        require(report['command'] == [str(G), '--outdir=' + str(m5out), str(S / 'simulator/gem5/fs.py'),
                                      '--resources', str(RES), '--readfile', str(readfile), '--max-ticks', str(MAX_TICKS)],
                'Actual nested simulator command differs')
        terminals = list(m5out.glob('*terminal*'))
        require(len(terminals) == 1 and terminals[0].stat().st_size <= 32 * 1024**2,
                'Missing/ambiguous/oversized actual guest serial')
        terminal = terminals[0]
        require(report['guest_serial_sha256'] == sha(terminal), 'Actual raw guest serial hash drift')
        raw = terminal.read_text()
        body, errors = self.wrapper.extract_probe(raw, 'runtime')
        require((self.payload / 'runtime.jsonl').read_text() == body
                and (self.payload / 'runtime-stderr.log').read_text() == errors,
                'Stored extracted runtime streams differ from raw serial frames')
        result = self.wrapper.load_validator('native_runtime_probe')(body, expect_architecture='riscv64')
        require(result == {'checks_passed': 9, 'architecture': 'riscv64',
                           'flush_path': 'linux-riscv-flush-icache', 'timing_calibrated': False},
                'Strict original runtime validator result differs')
        require(report['validated'] == {'runtime': result}, 'Report strict runtime verdict differs from independent replay')
        require('OPENRX_GUEST_COMPLETE' in raw and 'Kernel booted, In gem5 init...' in raw,
                'Guest completion/Linux init marker missing')
        require(re.search(r'Linux version 6\.8\.12(?:\s|\()', raw) is not None
                and 'PRETTY_NAME="Ubuntu 24.04 LTS"' in raw and 'VERSION_ID="24.04"' in raw,
                'Expected pinned Linux/Ubuntu guest not observed')
        simulation = readjson(m5out / 'simulation.json')
        require(report['simulation'] == simulation, 'Actual simulation/report snapshots differ')
        expected_simulation = {'schema_version': 1, 'evidence_class': 'full-system-functional',
                               'cpu': 'AtomicSimpleCPU', 'cores': 1, 'rvv': False, 'guest_ram': '4GiB',
                               'cache_hierarchy': 'PrivateL1PrivateL2WalkCacheHierarchy',
                               'l1d_size': '16KiB', 'l1i_size': '16KiB', 'l2_size': '256KiB',
                               'timing_calibrated': False, 'power_measured': False, 'execution_stage': 'finished',
                               'max_ticks_per_simulate_call': MAX_TICKS, 'last_exit_code': 0}
        for name, value in expected_simulation.items():
            require(type(simulation.get(name)) is type(value) and simulation[name] == value,
                    'Actual simulation field mismatch: ' + name)
        events = simulation['events']
        require([item['hypercall'] for item in events] == [1, 2, 3]
                and [item['event'] for item in events] == ['kernel-booted', 'after-boot-started', 'after-boot-finished'],
                'Incomplete/incorrect actual Linux event sequence')
        require(all(type(item['tick']) is int and item['tick'] >= 0 for item in events), 'Invalid observed event ticks')
        model = inspect_model(readjson(m5out / 'config.json'), RES, readfile, m5out)
        runner_stdout = json.loads((self.directory / 'stdout.log').read_text(), object_pairs_hook=json_object)
        require(runner_stdout == report, 'Runner stdout does not retain exact final scientific report')
        logs = [terminal, self.payload / 'runtime.jsonl', self.payload / 'runtime-stderr.log',
                self.payload / 'stdout.log', self.payload / 'stderr.log', self.directory / 'stdout.log', self.directory / 'stderr.log',
                m5out / 'config.json', m5out / 'config.ini', m5out / 'device.dtb', m5out / 'device.dts', m5out / 'stats.txt']
        self.passed('actual_guest_boot_and_strict_nine_case_runtime', {
            'scientific_report': digest(report_path), 'strict_validator_result': result,
            'framed_runtime_stderr_empty': not errors.strip(), 'guest_linux': '6.8.12', 'guest_distribution': 'Ubuntu24.04LTS',
            'guest_complete': True, 'hypercall_events': events, 'actual_model': model,
            'readfile': digest(readfile), 'retained_raw_logs_and_model': [digest(p) for p in logs],
            'outer_stderr_policy': 'Retained and inspectable; empty only required for framed runtime probe stderr',
            'scientific_scope': 'functional runtime-only; no RandomX gem5 matrix/timing/power/resume acceptance'})
        self.runner.check_bindings(R, self.directory, self.manifest)
        final = self.runner.verify(R, self.execution_id)
        require(final == self.integrity, 'Final retained integrity verdict changed during independent replay')
        require(sha(G) == self.binary['sha256'] and sha(PIPELINE) == PIPELINE_SHA
                and sha(SPEC) == SPEC_SHA and sha(RUNNER) == RUNNER_SHA, 'Final simulator/controller/request/runner drift')
        self.passed('inputs_and_output_receipt_reverified_after_independent_replay', final)


def pipeline_unit():
    result = subprocess.run(['systemctl', '--user', 'show', 'openrx-migration-validation-pipeline-v3-20261009.service',
                             '-p', 'LoadState', '-p', 'ActiveState', '-p', 'SubState', '-p', 'Result', '-p', 'ExecMainStatus'],
                            capture_output=True, text=True)
    return {'query_returncode': result.returncode,
            **dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--self-sha256', help='Required external reviewed checker SHA for evidence acceptance')
    parser.add_argument('--wait', action='store_true', help='Observe existing capture/pipeline without a wall deadline')
    parser.add_argument('--describe', action='store_true', help='Print criteria without reading evidence or creating files')
    args = parser.parse_args(argv)
    if args.describe:
        print(json.dumps(CRITERIA, indent=2))
        return 0
    require(args.output_dir is not None and args.self_sha256 is not None, 'Review requires new output-dir and external checker SHA')
    own = digest(Path(__file__))
    require(own['sha256'] == args.self_sha256 and re.fullmatch(r'[0-9a-f]{64}', args.self_sha256), 'Reviewer script differs from external reviewed digest')
    out = args.output_dir.absolute()
    require(out.parent == E and not out.is_symlink(), 'Reviewer output must be a new direct-child directory under migration evidence')
    out.mkdir(mode=0o700)
    syncdir(out.parent)
    review = Review(out)
    newjson(out / 'review-intent.json', {'at': now(), 'checker': own, 'criteria': CRITERIA,
                                        'argv': sys.argv, 'writes': 'new reviewer evidence only',
                                        'launches_science_or_services': False})
    accepted = False
    error = None
    try:
        while not (E / 'runtime-capture-summary.json').exists():
            observed = pipeline_unit()
            require(args.wait, 'Actual local runtime capture is not available; no acceptance inferred')
            require(observed.get('ActiveState') in {'active', 'activating', 'deactivating'},
                    'Existing pipeline ended without actual runtime capture: ' + repr(observed))
            print('WAITING existing pipeline/capture only: ' + repr(observed), flush=True)
            time.sleep(30)
        review.check_fixed()
        review.check_sources()
        review.check_build()
        review.check_dependencies()
        review.check_guest_inputs()
        review.check_preflight()
        review.check_execution()
        review.check_actual_runtime()
        require(sha(Path(__file__)) == args.self_sha256, 'Reviewer changed during review')
        accepted = True
    except Exception as exc:
        error = {'type': type(exc).__name__, 'message': str(exc)}
        newfile(out / 'review-failure-traceback.log', traceback.format_exc().encode())
        print('FAIL ' + str(exc), flush=True)
    receipt = {'schema': 'openrx.local-migration.independent-runtime-review.v1', 'at': now(),
               'checker': own, 'independent_review_accepted': accepted, 'checks_completed': review.checks,
               'execution_id': getattr(review, 'execution_id', None), 'error': error,
               'scope': CRITERIA['scope'], 'migration_complete': False, 'activation_authorized': False,
               'scientific_milestones_closed': [],
               'remaining_gates': ['actual gem5 safe-stop evidence and independent review',
                                   'GitHub docs/handoffs consistency', 'reviewed PR merge', 'final cutover receipt'],
               'limitations': ['Runtime-only nine-case acceptance; complete gem5 RandomX matrix remains open',
                               'No calibrated timing/power or scientific checkpoint resume acceptance',
                               'No whole Codex-session shutdown or physical host reboot demonstration',
                               'Host interpreter/core pins verified; no hermetic offline dependency closure claimed',
                               'Original unavailable simulator has not been recovered; new rebuilt identity retained']}
    newjson(out / 'independent-runtime-review.json', receipt)
    print(json.dumps({'accepted_scope': accepted, 'receipt': str(out / 'independent-runtime-review.json'),
                      'receipt_sha256': sha(out / 'independent-runtime-review.json'), 'migration_complete': False}), flush=True)
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
