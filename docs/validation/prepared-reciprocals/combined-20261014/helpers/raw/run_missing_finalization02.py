"""Run only the missing finalizer from the unchanged combined source."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
RUNNER_SHA = '657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b'


def validate_summary(summary):
    assert summary['status'] == 'pass'
    assert summary['synthesis_requested'] is True
    assert summary['source_unchanged_after_run'] is True
    assert summary['fixture_inputs_unchanged_after_run'] is True
    assert summary['rtl_modes'] == len(summary['rtl']) == 41
    assert summary['mapped_modes'] == len(summary['mapped']) == 19
    assert len(summary['mapping']) == 3
    assert summary['invalid_parameter_cases'] == 4
    assert summary['native_invalid_input_cases'] == 6
    assert len(summary['full_profile_order']) == 4


def main():
    source, execution = map(lambda x: Path(x).resolve(), sys.argv[1:])
    assert source == Path('/tmp/openrx-combined-source-0kazbk4f')
    assert source.is_dir() and not (source / '.git').exists()
    assert execution.is_dir() and source != execution and source not in execution.parents
    manifest = json.loads((execution / 'manifest.json').read_text())
    assert manifest['migration_state'] == 'LOCAL_ACTIVE' and manifest['kind'] == 'simulation'
    assert manifest['request_key'] == 'issue69-combined-finalization-recovery02'
    assert manifest['runner']['sha256'] == RUNNER_SHA
    assert manifest['resources']['MemoryMax'] == '4294967296'
    assert manifest['resources']['CPUQuota'] == '600%'
    assert manifest['resources']['MemorySwapMax'] == '2G'
    assert manifest['resources']['TasksMax'] == 256 and manifest['resources']['global_slots'] == 1
    kernel = json.loads((execution / 'prelaunch-kernel-check.json').read_text())
    assert kernel['safe'] and kernel['production_enforced'] and kernel['production_required']
    assert not kernel['errors'] and len(os.sched_getaffinity(0)) >= 6
    group = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split(':')[-1].lstrip('/')
    def resources():
        return {name: (group / name).read_text().strip() for name in [
            'cpu.max', 'memory.max', 'memory.swap.max', 'pids.max', 'cpu.stat',
            'memory.peak', 'memory.events', 'memory.swap.peak', 'pids.current'] if (group / name).exists()}
    stages = [{'phase': 'payload-start', 'at_epoch': time.time(), 'kernel': resources()}]
    (execution / 'combined-resource-stages.json').write_text(json.dumps(stages, indent=2) + '\n')
    drivers = ['scripts/test_regfile_blake2b.py', 'scripts/test_scratchpad_finalization.py']
    before = {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in drivers}
    output = execution / 'combined-finalization'
    argv = [sys.executable, '-B', 'scripts/test_scratchpad_finalization.py', '--output', str(output), '--synthesize']
    started = time.monotonic()
    print('START missing-finalization-only; original unit/seed attempt remains preserved', flush=True)
    with (execution / 'finalization-console.log').open('xb') as log:
        result = subprocess.run(argv, cwd=source, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                                stdout=log, stderr=subprocess.STDOUT)
    command = {'label': 'finalization', 'argv': argv, 'returncode': result.returncode,
               'wall_seconds': time.monotonic() - started}
    (execution / 'combined-commands.json').write_text(json.dumps([command], indent=2) + '\n')
    stages.append({'phase': 'finalization-complete', 'at_epoch': time.time(), 'kernel': resources()})
    (execution / 'combined-resource-stages.json').write_text(json.dumps(stages, indent=2) + '\n')
    assert result.returncode == 0, command
    summary = json.loads((output / 'summary.json').read_text())
    validate_summary(summary)
    assert before == {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in drivers}
    (execution / 'combined-driver-postcheck.json').write_text(json.dumps(before, indent=2) + '\n')
    print('Missing finalization regression completed; original wrapper failure retained; independent review required.', flush=True)


if __name__ == '__main__':
    main()
