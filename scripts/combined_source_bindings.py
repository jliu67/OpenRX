#!/usr/bin/env python3
"""Verify staged PR70/main source reconciliation without executing workloads.

Historical input maps and the original PR70 declaration are immutable. Only
enumerated reviewed-parent or staged metadata successors may differ from them.
Source identity permits retaining old evidence; it does not execute or accept
the combined hardware context. Original prepared219 and sequence73 stay strict.
"""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from prepared_parent_bindings import default_zero, digest_map, load, require, sha, source_path

HELPER = 'scripts/combined_source_bindings.py'
DECLARATION = 'docs/validation/prepared-reciprocals/combined-source-bindings.json'
OLD_DECLARATION = 'docs/validation/prepared-reciprocals/parent-source-bindings.json'
OLD_DECLARATION_SHA = '76db0119fe6a87d06838954b19049c7fcefa185d23027fe4adbd6dbca8f8636d'
PARENTS = {'reviewed_pr70': '35c2cae61092107acb2c684bbca308aca8fb280b',
           'merged_main': '5f28dd4363504ecf33a8f10451c53405773c564f'}
# The 258 executed finalizer inputs retain their already-declared metadata
# corrections in the published259 map; neither historical map is rewritten.
MANIFESTS = {
    'legacy53': ('docs/validation/divsqrt-execute-20261013/compat-rtl-inputs.json',
                 'c2ac02cc67539a065ab96f40d3ba00c18f474294ebda082133c4ddb67e6464b7', 53),
    'sequence69': ('docs/validation/program-sequence-20261013/server-current/inputs.json',
                   '3ef49b7f6ffbce270676aa5f45cecd344008a08009e19cf6184cecc04e29822b', 69),
    'prepared219': ('docs/validation/prepared-reciprocals/server/inputs.json',
                    'e99a52558ba45e4a75635ac36e992a311ac07c0bd60ab075eeceb14489ad8227', 219),
    'regression73': ('docs/validation/prepared-reciprocals/program-sequence-regression/inputs.json',
                     'f70cacc7702f2a2ecd62a7e6761cc47ed15047d1313008772ccb5ef51b801fe2', 73),
    'regfile246': ('docs/validation/regfile-blake2b-20261013/server/inputs.json',
                   '5235c3cff1de5ac3fcc16f56b7ccae07c9296f001179d3b99ce97cda9ff93328', 246),
    'finalizer259': ('docs/validation/scratchpad-finalization-20261013/server/published-head-inputs.json',
                     '2a2af1d12308eb9a69a28df47a87181b7aa3148c08b3f9a96c188e05ad786912', 259),
}
EXECUTED_FINALIZER = ('docs/validation/scratchpad-finalization-20261013/server/inputs.json',
                      '893a051b7a726f3454077ae63ee0eae217362ad56d171e6f768ffb624da91a21', 258)
REVIEWED = {
    'rtl/execute/randomx_integer_execute.v': ('reviewed_prepared_rtl', 'prepared219'),
    'rtl/execute/randomx_integer_iteration.v': ('reviewed_prepared_rtl', 'prepared219'),
    'scripts/test_program_sequence.py': ('reviewed_program_sequence_driver', 'regression73'),
}
STAGED = {
    'scripts/test_regfile_blake2b.py': 'binding_report_driver',
    'scripts/test_scratchpad_finalization.py': 'binding_report_driver',
    '.github/workflows/integer-execute.yml': 'workflow_dependency_triggers',
    '.github/workflows/regfile-blake2b.yml': 'workflow_dependency_triggers',
    '.github/workflows/scratchpad-finalization.yml': 'workflow_dependency_triggers',
}
CONTEXTS = {'regfile': 'sequence69', 'finalizer': 'regfile246'}


def manifest_record(key):
    path, digest, count = MANIFESTS[key]
    return {'path': path, 'sha256': digest, 'source_count': count}


def pinned_map(root, specification):
    relative, digest, count = specification
    path = source_path(root, relative)
    require(sha(path) == digest, 'historical manifest bytes changed: ' + relative)
    values = digest_map(load(path), relative)
    require(len(values) == count, 'historical manifest count changed: ' + relative)
    return values


def validate(root):
    """Check the complete exact declaration and all unchanged historical paths."""
    root = Path(root).resolve()
    declaration_path = source_path(root, DECLARATION)
    declaration = load(declaration_path)
    require(isinstance(declaration, dict) and set(declaration) == {
        'schema_version', 'parents', 'original_declaration', 'historical_manifests',
        'executed_finalizer_manifest', 'successors', 'scope'}, 'unexpected combined declaration fields')
    require(type(declaration['schema_version']) is int and declaration['schema_version'] == 1,
            'wrong combined declaration schema')
    require(declaration['parents'] == PARENTS, 'wrong exact combined parents')
    require(declaration['original_declaration'] == {'path': OLD_DECLARATION, 'sha256': OLD_DECLARATION_SHA},
            'original PR70 declaration binding changed')
    require(sha(source_path(root, OLD_DECLARATION)) == OLD_DECLARATION_SHA,
            'original PR70 declaration bytes changed')
    require(declaration['historical_manifests'] == {key: manifest_record(key) for key in MANIFESTS},
            'combined historical manifest identities changed')
    require(declaration['executed_finalizer_manifest'] == {
        'path': EXECUTED_FINALIZER[0], 'sha256': EXECUTED_FINALIZER[1], 'source_count': EXECUTED_FINALIZER[2]},
        'executed finalizer manifest binding changed')
    require(isinstance(declaration['scope'], str) and declaration['scope'].strip(), 'combined scope missing')
    maps = {key: pinned_map(root, value) for key, value in MANIFESTS.items()}
    executed_finalizer = pinned_map(root, EXECUTED_FINALIZER)
    successors = declaration['successors']
    require(isinstance(successors, dict) and set(successors) == set(REVIEWED) | set(STAGED),
            'combined successor path set must match the exact allowlist')
    original = load(root / OLD_DECLARATION)
    for relative, row in successors.items():
        require(isinstance(row, dict) and set(row) == {'kind', 'sha256', 'validation_state'},
                'unexpected combined successor fields: ' + relative)
        digest_map({relative: row['sha256']}, 'successor')
        if relative in REVIEWED:
            kind, basis = REVIEWED[relative]
            require(row['kind'] == kind and row['validation_state'] == 'reviewed_parent_source_match',
                    'reviewed successor state changed: ' + relative)
            require(row['sha256'] == maps[basis][relative], 'reviewed successor digest is stale: ' + relative)
            if kind == 'reviewed_prepared_rtl':
                require(row['sha256'] == original['overrides'][relative]['candidate_sha256'],
                        'original reviewed RTL successor changed: ' + relative)
                default_zero(source_path(root, relative), original['overrides'][relative]['module'])
        else:
            require(row['kind'] == STAGED[relative] and row['validation_state'] == 'staged_not_executed',
                    'staged metadata cannot claim executed acceptance: ' + relative)
        require(sha(source_path(root, relative)) == row['sha256'], 'combined live successor changed: ' + relative)

    reports = {}
    for key, values in maps.items():
        changes = []
        for relative, historical in values.items():
            current = sha(source_path(root, relative))
            if current == historical:
                continue
            require(key not in ('prepared219', 'regression73'), 'retained executable input changed: ' + relative)
            require(relative in successors and current == successors[relative]['sha256'],
                    'undeclared historical source changed: ' + relative)
            changes.append({'path': relative, 'historical_sha256': historical,
                            'current_sha256': current, **successors[relative]})
        reports[key] = {**manifest_record(key), 'historical_manifest_bytes_preserved': True,
                        'unchanged_live_source_count': len(values) - len(changes),
                        'all_recorded_live_source_bytes_unchanged': not changes,
                        'declared_live_successors': changes}

    input_bindings = {HELPER: sha(source_path(root, HELPER)), DECLARATION: sha(declaration_path),
                      'scripts/prepared_parent_bindings.py': sha(source_path(root, 'scripts/prepared_parent_bindings.py')),
                      OLD_DECLARATION: OLD_DECLARATION_SHA, EXECUTED_FINALIZER[0]: EXECUTED_FINALIZER[1]}
    input_bindings.update({value[0]: value[1] for value in MANIFESTS.values()})
    # Every live path read by this guard is an input to its source-only result.
    # Binding it here does not claim it was executed by the component workload.
    input_bindings.update({path: sha(source_path(root, path))
                           for values in maps.values() for path in values})
    published_finalizer = maps['finalizer259']
    prior_metadata = [{'path': path, 'executed_sha256': executed_finalizer[path],
                       'published_parent_sha256': published_finalizer[path],
                       'current_sha256': sha(source_path(root, path)),
                       'status': 'already_declared_merged_main_metadata_successor'}
                      for path in sorted(executed_finalizer)
                      if executed_finalizer[path] != published_finalizer[path]]
    prior_additions = [{'path': path, 'published_parent_sha256': published_finalizer[path],
                        'status': 'already_declared_merged_main_input_addition'}
                       for path in sorted(set(published_finalizer) - set(executed_finalizer))]
    return {'schema_version': 1, 'parents': PARENTS, 'historical_sources': reports,
            'executed_finalizer_manifest_bytes_preserved': True,
            'prior_finalizer_metadata_successors': prior_metadata,
            'prior_finalizer_published_input_additions': prior_additions,
            'original_pr70_declaration_bytes_preserved': True,
            'original_prepared219_live_bytes_unchanged': reports['prepared219']['all_recorded_live_source_bytes_unchanged'],
            'original_regression73_live_bytes_unchanged': reports['regression73']['all_recorded_live_source_bytes_unchanged'],
            'combined_context_previously_executed': False, 'fresh_native_or_hdl_validation_performed': False,
            'staged_metadata_successors': {path: successors[path] for path in STAGED},
            'input_bindings': input_bindings,
            'scope': 'Fresh source-binding checks only. Reviewed-parent input identity retains old prepared and '
                     'program-sequence evidence; combined seed/finalizer execution and independent acceptance are separate.'}


def validate_context(root, context):
    """Keep exact legacy behavior when the additive declaration is absent."""
    root = Path(root).resolve()
    require(context in CONTEXTS, 'unknown combined component context')
    key = CONTEXTS[context]
    if not (root / DECLARATION).exists():
        values = pinned_map(root, MANIFESTS[key])
        for relative, digest in values.items():
            require(sha(source_path(root, relative)) == digest, 'legacy accepted source changed: ' + relative)
        return {'context': context, 'declaration_used': False, 'accepted_source_bindings': len(values),
                'all_original_and_accepted_bytes_unchanged': True,
                'input_bindings': {HELPER: sha(source_path(root, HELPER)), MANIFESTS[key][0]: MANIFESTS[key][1]}}
    report = validate(root)
    changes = report['historical_sources'][key]['declared_live_successors']
    return {**report, 'context': context, 'declaration_used': True,
            'accepted_source_bindings': MANIFESTS[key][2],
            'all_original_and_accepted_bytes_unchanged': not changes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--context', choices=tuple(CONTEXTS))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or output == root or root in output.parents):
        parser.error('fresh report outside source required')
    try:
        report = validate_context(root, args.context) if args.context else validate(root)
        report['status'] = 'pass'
    except (OSError, ValueError, KeyError, TypeError) as error:
        report = {'status': 'failed', 'error': str(error), 'fresh_native_or_hdl_validation_performed': False}
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
