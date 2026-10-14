#!/usr/bin/env python3
"""Check the exact declared prepared-reciprocal successor without running HDL.

Without a declaration, every accepted parent source must retain its old digest.
With one, exactly two RTL paths may differ, and both must match the immutable
server input record and keep the runtime-reciprocal default PREPARED_RCP=0.
Retained PASS records are evidence from that server run, not a fresh execution.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

sys.dont_write_bytecode = True

ACCEPTED_PARENT = '7f299c74f81332257eefd775086b355969ad85f3'
CANDIDATE_BASE = '8f3b9bc3d7f0182d66185abe95310f0bab00274b'
MANIFEST = 'docs/validation/divsqrt-execute-20261013/compat-rtl-inputs.json'
MANIFEST_SHA256 = 'c2ac02cc67539a065ab96f40d3ba00c18f474294ebda082133c4ddb67e6464b7'
DECLARATION = 'docs/validation/prepared-reciprocals/parent-source-bindings.json'
HELPER = 'scripts/prepared_parent_bindings.py'
SERVER = 'docs/validation/prepared-reciprocals/server/'
SERVER_INPUTS = SERVER + 'inputs.json'
SERVER_INPUTS_SHA256 = 'e99a52558ba45e4a75635ac36e992a311ac07c0bd60ab075eeceb14489ad8227'
SERVER_ARTIFACTS_SHA256 = '81a37d88668addbb0a518f93c8bd8f462e46d3cb4c57236ddc88b269bc9dfa96'
OVERRIDES = {
    'rtl/execute/randomx_integer_execute.v': 'randomx_integer_execute',
    'rtl/execute/randomx_integer_iteration.v': 'randomx_integer_iteration',
}
EVIDENCE = {
    'inputs.json': SERVER_INPUTS_SHA256,
    'summary.json': '24b7ba811fe0a9e772211a9f2277c7e4a3161364c88e74229e5e42bab789c663',
    'pass-records.json': '555bbeeeacc3ad46aef64bf172bf5189489e94139974bff54cf37d13baa4bae6',
    'commands.json': '903659b7fe4cae91c6da64b2aecefd68b8a07302edefa191ae28276c294fb1ae',
}
RTL_LABELS = {f'rtl-cache-{p}-{s}' for p in (0, 1) for s in (0, 1)} | \
             {f'rtl-iteration-{p}-{s}' for p in (0, 1) for s in (0, 1)} | \
             {'rtl-core-guard', 'rtl-default-transport-0', 'rtl-default-transport-1'}
MAPPED_LABELS = {f'mapped-cache-{p}-{s}' for p in (0, 1) for s in (0, 1)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_path(root, relative):
    require(isinstance(relative, str), 'binding path must be a string')
    path = PurePosixPath(relative)
    require(relative and not path.is_absolute() and '..' not in path.parts and
            relative == path.as_posix() and '\\' not in relative, 'unsafe binding path: ' + relative)
    resolved = (root / relative).resolve()
    require(root in resolved.parents and resolved.is_file(), 'missing or external binding: ' + relative)
    return resolved


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON binding key: ' + key)
        result[key] = value
    return result


def load(path):
    return json.loads(path.read_text(), object_pairs_hook=unique_object)


def digest_map(value, label):
    require(isinstance(value, dict) and value, label + ' must be a nonempty digest map')
    for path, digest in value.items():
        require(isinstance(path, str) and isinstance(digest, str) and
                re.fullmatch(r'[0-9a-f]{64}', digest) is not None, label + ' has an invalid digest/path')
    return value


def default_zero(path, module):
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', path.read_text(), flags=re.S)
    headers = re.findall(r'\bmodule\s+' + re.escape(module) + r'\s*#\s*\((.*?)\)\s*\(', text, re.S)
    require(len(headers) == 1, 'missing or ambiguous module parameter header: ' + module)
    parameters = headers[0]
    require(len(re.findall(r'\bPREPARED_RCP\s*=', parameters)) == 1 and
            re.search(r'(?:^|,)\s*(?:parameter\s+)?(?:integer\s+)?PREPARED_RCP\s*=\s*0\s*(?=,|$)',
                      parameters) is not None,
            'PREPARED_RCP default must remain 0: ' + module)


def validate(root):
    """Return an honest byte-binding report, or reject before any payload."""
    root = Path(root).resolve()
    manifest_path = source_path(root, MANIFEST)
    require(sha(manifest_path) == MANIFEST_SHA256, 'accepted compatibility manifest bytes changed')
    accepted = digest_map(load(manifest_path), 'accepted manifest')
    declaration_path = root / DECLARATION
    overrides = {}
    recorded = {}
    bindings = {MANIFEST: MANIFEST_SHA256, HELPER: sha(source_path(root, HELPER))}
    if declaration_path.exists():
        declaration_path = source_path(root, DECLARATION)
        declaration = load(declaration_path)
        require(isinstance(declaration, dict) and set(declaration) == {
            'schema_version', 'accepted_parent', 'candidate_base', 'accepted_manifest',
            'executed_inputs', 'default_prepared_rcp', 'overrides', 'reason'}, 'unexpected declaration fields')
        require(declaration['schema_version'] == 1 and declaration['accepted_parent'] == ACCEPTED_PARENT and
                declaration['candidate_base'] == CANDIDATE_BASE, 'wrong declaration parent/schema')
        require(declaration['accepted_manifest'] == {'path': MANIFEST, 'sha256': MANIFEST_SHA256},
                'declaration accepted manifest binding is stale')
        require(declaration['executed_inputs'] == {'path': SERVER_INPUTS, 'sha256': SERVER_INPUTS_SHA256},
                'declaration recorded server binding is stale')
        require(type(declaration['default_prepared_rcp']) is int and declaration['default_prepared_rcp'] == 0,
                'declaration must retain default PREPARED_RCP=0')
        require(isinstance(declaration['reason'], str) and declaration['reason'].strip(), 'declaration reason missing')
        overrides = declaration['overrides']
        require(isinstance(overrides, dict) and set(overrides) == set(OVERRIDES),
                'declaration must override exactly the two executor/iteration paths')
        server_inputs = source_path(root, SERVER_INPUTS)
        require(sha(server_inputs) == SERVER_INPUTS_SHA256, 'recorded server inputs bytes changed')
        recorded = digest_map(load(server_inputs), 'recorded server inputs')
        require(len(recorded) == 219, 'recorded server source count changed')
        bindings.update({DECLARATION: sha(declaration_path), SERVER_INPUTS: SERVER_INPUTS_SHA256})

    successors = []
    for relative, old_digest in accepted.items():
        current = source_path(root, relative)
        if relative in overrides:
            row = overrides[relative]
            require(isinstance(row, dict) and set(row) == {'module', 'accepted_sha256', 'candidate_sha256'},
                    'unexpected successor fields: ' + relative)
            require(row['module'] == OVERRIDES[relative], 'wrong successor module: ' + relative)
            require(row['accepted_sha256'] == old_digest, 'stale accepted successor digest: ' + relative)
            default_zero(current, row['module'])
            require(isinstance(row['candidate_sha256'], str) and
                    re.fullmatch(r'[0-9a-f]{64}', row['candidate_sha256']) is not None and
                    row['candidate_sha256'] != old_digest, 'invalid candidate successor digest: ' + relative)
            require(recorded.get(relative) == row['candidate_sha256'], 'stale recorded candidate digest: ' + relative)
            require(sha(current) == row['candidate_sha256'], 'changed candidate source: ' + relative)
            successors.append({'path': relative, **row})
        else:
            require(sha(current) == old_digest, 'changed undeclared accepted source: ' + relative)
    for relative, digest in recorded.items():
        require(sha(source_path(root, relative)) == digest, 'changed recorded server source: ' + relative)

    return {'schema_version': 1, 'accepted_parent': ACCEPTED_PARENT, 'bindings': len(accepted),
            'manifest_path': MANIFEST, 'manifest_sha256': MANIFEST_SHA256,
            'declaration_used': bool(overrides), 'unchanged_accepted_bindings': len(accepted) - len(overrides),
            'all_accepted_driver_IP_RTL_bytes_unchanged': not overrides,
            'all_other_accepted_paths_unchanged': True, 'declared_successors': successors,
            'default_PREPARED_RCP_0_verified': bool(overrides),
            'recorded_server_input_bindings': len(recorded), 'all_recorded_server_inputs_bytes_unchanged': bool(recorded),
            'input_bindings': bindings,
            'scope': 'Source bytes and declared default mode only; no new native execution, HDL simulation or synthesis.'}


def verify_evidence(root):
    """Check retained evidence identities and outcomes without replaying work."""
    root = Path(root).resolve()
    artifact_path = source_path(root, SERVER + 'artifacts.sha256.json')
    require(sha(artifact_path) == SERVER_ARTIFACTS_SHA256, 'retained artifact manifest bytes changed')
    artifacts = digest_map(load(artifact_path), 'retained output artifacts')
    for name, digest in EVIDENCE.items():
        require(artifacts.get(name) == digest and sha(source_path(root, SERVER + name)) == digest,
                'retained evidence binding changed: ' + name)
    summary = load(root / SERVER / 'summary.json')
    records = load(root / SERVER / 'pass-records.json')
    require(summary['status'] == 'pass' and summary['rtl_checks'] == 11 and summary['mapped_checks'] == 4 and
            summary['unexpected_failures'] == 0 and summary['invalid_parameter_or_abi_guards'] == 3 and
            summary['full_hash_performance_accepted'] is False, 'retained server scope/outcome mismatch')
    require(set(summary['rtl']) == RTL_LABELS and set(summary['mapped']) == MAPPED_LABELS and
            set(records) == RTL_LABELS | MAPPED_LABELS, 'retained PASS label set changed')
    for label in sorted(records):
        log = source_path(root, SERVER + label + '.log')
        require(sha(log) == artifacts.get(label + '.log'), 'retained PASS log digest changed: ' + label)
        require(isinstance(records[label], str) and records[label].startswith('PASS ') and
                log.read_text().splitlines() == [records[label]], 'retained PASS/log mismatch: ' + label)
        group = summary['rtl'] if label in RTL_LABELS else summary['mapped']
        parsed = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', records[label])}
        require(group[label] == parsed, 'retained summary/PASS mismatch: ' + label)
        if label in MAPPED_LABELS:
            require(records[label] == records[label.replace('mapped-', 'rtl-', 1)], 'mapped/RTL PASS mismatch: ' + label)
    commands = load(root / SERVER / 'commands.json')
    require(len(commands) == 41 and len({row['label'] for row in commands}) == 41, 'retained command set changed')
    negative = {'invalid-cache', 'invalid-executor', 'invalid-legacy-netlist'}
    require({row['label'] for row in commands if row['expected_failure']} == negative, 'retained negative guard set changed')
    for row in commands:
        require(type(row['returncode']) is int and 'error' not in row and
                ((row['returncode'] != 0) if row['label'] in negative else (row['returncode'] == 0)),
                'retained command failed unexpectedly: ' + row['label'])
    return {'retained_server_rtl_checks': 11, 'retained_server_mapped_checks': 4,
            'retained_server_command_records': 41, 'retained_negative_elaboration_guards': 3,
            'retained_artifacts_manifest_sha256': SERVER_ARTIFACTS_SHA256,
            'retained_evidence_only': True, 'fresh_native_simulation_or_synthesis': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-evidence', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve() if args.output else None
    if output and (output == root or root in output.parents or output.exists()):
        parser.error('fresh report output outside source required')
    try:
        report = validate(root)
        if args.check_evidence and report['declaration_used']:
            report['retained_evidence'] = verify_evidence(root)
        report['status'] = 'pass'
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = {'status': 'failed', 'error': str(exc), 'scope': 'Source/evidence checks only; no payload executed.'}
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2), file=sys.stderr)
        return 1
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
