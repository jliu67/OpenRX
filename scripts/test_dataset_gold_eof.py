#!/usr/bin/env python3
"""Bounded file-closure regression using verbatim production testbench tasks.

Run only through reviewed admission, from a clean frozen source. This compiles a
tiny top, never the lifecycle/DUT, native reference, cache or full hash. Explicit
tool paths are mandatory; the caller's admission binds their pinned provenance.
Every command, fixture, extracted byte range and outcome is retained externally.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from dataset_lifecycle_support import Supervisor, save, sha

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / 'rtl/dataset_capacity/tests/tb_dataset_capacity_hash_lifecycle.v'
TASKS = ('dataset_assert_native_eof', 'dataset_read_native_assertion')
DATA = '123456789abcdef0' * 8
ROW = ('0000000000000040 ' + DATA).encode()
READ_ERROR = 'actual dataset full64 address differs from retained native gold'
TRAILING_ERROR = 'native dataset gold contains trailing data'
INVALID_ERROR = 'native dataset gold descriptor invalid'
UNAVAILABLE_ERROR = 'native dataset gold descriptor unavailable'
VALUE_ERROR = 'EOF harness fixture data mismatch'


def identity(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink(), str(path)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def extract_task(text, name):
    """Return the original task bytes, with no rewritten declarations or body."""
    starts = list(re.finditer(r'(?m)^[ \t]*task[ \t]+' + re.escape(name) + r'[ \t]*;', text))
    assert len(starts) == 1, 'exactly one production task required: ' + name
    start = starts[0].start()
    end = re.search(r'\bendtask\b', text[starts[0].end():])
    assert end is not None, 'unterminated production task: ' + name
    stop = starts[0].end() + end.end()
    value = text[start:stop]
    assert len(re.findall(r'\btask\b', value)) == 1
    return value, {'start_byte': len(text[:start].encode()), 'end_byte': len(text[:stop].encode()),
        'start_line': text.count('\n', 0, start) + 1, 'bytes': len(value.encode()),
        'sha256': hashlib.sha256(value.encode()).hexdigest()}


def extract_original_footer(text):
    """Optional historical counterexample: retain the exact original statements."""
    pattern = (r'(?m)^[ \t]*status=\$fscanf\(dataset_gold_fd,[^\n]*\);\n'
               r'[ \t]*if\(status!=-1\)\$fatal\(1,"([^"\n]*)"\);')
    matches = list(re.finditer(pattern, text))
    assert len(matches) == 1, 'exactly one original status!=-1 footer required'
    match = matches[0]
    value = match.group()
    return value, match.group(1), {'start_byte': len(text[:match.start()].encode()),
        'end_byte': len(text[:match.end()].encode()), 'bytes': len(value.encode()),
        'start_line': text.count('\n', 0, match.start()) + 1,
        'sha256': hashlib.sha256(value.encode()).hexdigest()}


def cases(original_diagnostic=None):
    """Expected test stimuli/outcomes, not an alternative EOF implementation."""
    values = [
        ('valid_newline', ROW + b'\n', 1, 0, None),
        ('valid_no_newline', ROW, 1, 0, None),
        ('valid_all_whitespace_tail', ROW + b'\n\t\v\f\r ', 1, 0, None),
        ('valid_direct_empty_eof', b'', 0, 0, None),
        ('valid_direct_whitespace_eof', b'\t\n\v\f\r ', 0, 0, None),
        ('extra_complete_row', ROW + b'\n' + ROW + b'\n', 1, 0, TRAILING_ERROR),
        ('extra_partial_row', ROW + b'\n0000000000000080', 1, 0, TRAILING_ERROR),
        ('extra_malformed_text', ROW + b'\ngarbage\n', 1, 0, TRAILING_ERROR),
        ('extra_attached_suffix', ROW + b'g', 1, 0, TRAILING_ERROR),
        ('extra_nul', ROW + b'\n\x00', 1, 0, TRAILING_ERROR),
        ('extra_ff_not_eof', ROW + b'\n\xff', 1, 0, TRAILING_ERROR),
        ('required_empty_file', b'', 1, 0, READ_ERROR),
        ('required_missing_last_row', ROW + b'\n', 2, 0, READ_ERROR),
        ('required_missing_data', b'0000000000000040\n', 1, 0, READ_ERROR),
        ('required_malformed_address', b'g ' + DATA.encode() + b'\n', 1, 0, READ_ERROR),
        ('required_malformed_data', b'0000000000000040 g\n', 1, 0, READ_ERROR),
        ('required_wrong_address', b'0000000000000080 ' + DATA.encode() + b'\n', 1, 0, READ_ERROR),
        ('required_truncated_data_token', ROW[:-1] + b'\n', 1, 0, VALUE_ERROR),
        ('required_unknown_data_token', b'0000000000000040 ' + b'x' * 128 + b'\n', 1, 0, VALUE_ERROR),
        ('missing_file', None, 0, 0, INVALID_ERROR),
        ('zero_descriptor', ROW + b'\n', 0, 1, INVALID_ERROR),
        ('closed_descriptor', ROW + b'\n', 0, 2, UNAVAILABLE_ERROR),
    ]
    result = [{'name': name, 'fixture': data, 'rows': rows, 'mode': mode,
               'expected_diagnostic': diagnostic} for name, data, rows, mode, diagnostic in values]
    if original_diagnostic is not None:
        result.append({'name': 'historical_valid_eof', 'fixture': ROW + b'\n', 'rows': 1,
            'mode': 4, 'expected_diagnostic': original_diagnostic, 'historical_counterexample': True})
    return result


def tiny_top(tasks, original_footer=None):
    historical = ''
    if original_footer is not None:
        historical = ' task historical_native_eof;\n  integer status;\n begin\n' + original_footer + '\n end endtask\n'
    terminal = 'historical_native_eof();' if original_footer is not None else '$fatal(1,"historical footer absent");'
    return '''// SPDX-License-Identifier: BSD-3-Clause
// Generated bounded top. The two production tasks below are byte-identical.
module tb_dataset_gold_eof;
 integer dataset_gold_fd=0,dataset_requests_seen=0;
 reg [63:0] dataset_gold_address=0,ds_req_addr=0;
 reg [511:0] dataset_expected_data=0;
 string fixture_path,case_name;
 integer mode,required_rows,n,arg_status;
''' + '\n'.join(tasks[name] for name in TASKS) + '\n' + historical + ''' initial begin
  arg_status=$value$plusargs("fixture=%s",fixture_path);
  if(arg_status!=1)$fatal(1,"EOF harness fixture argument absent");
  arg_status=$value$plusargs("case_name=%s",case_name);
  if(arg_status!=1)$fatal(1,"EOF harness case argument absent");
  arg_status=$value$plusargs("mode=%d",mode);
  if(arg_status!=1)$fatal(1,"EOF harness mode argument absent");
  arg_status=$value$plusargs("rows=%d",required_rows);
  if(arg_status!=1||required_rows<0||required_rows>2)$fatal(1,"EOF harness row bound");
  if(mode==1)dataset_gold_fd=0;
  else dataset_gold_fd=$fopen(fixture_path,"r");
  // Missing input invokes the production descriptor guard before any row read.
  if(dataset_gold_fd===0)dataset_assert_native_eof(dataset_gold_fd);
  if(mode==2)begin
   $fclose(dataset_gold_fd);
   dataset_assert_native_eof(dataset_gold_fd);
  end
  for(n=0;n<required_rows;n=n+1)begin
   ds_req_addr=64'h40+64*n;
   dataset_read_native_assertion();
   // Fixture sanity: this is not a replacement production parser/EOF gate.
   if(dataset_expected_data!==512'h''' + DATA + ''')
    $fatal(1,"EOF harness fixture data mismatch");
  end
  if(mode==4)begin
   ''' + terminal + '''
  end else dataset_assert_native_eof(dataset_gold_fd);
  if(dataset_requests_seen!=required_rows)$fatal(1,"EOF harness row accounting");
  $fclose(dataset_gold_fd);
  $display("PASS dataset_gold_eof case=%0s rows=%0d",case_name,required_rows);
  $finish;
 end
endmodule
'''


def manifest(out):
    save(out / 'artifacts.sha256.json', {str(p.relative_to(out)): identity(p)
        for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'artifacts.sha256.json'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verilator-root', type=Path, required=True)
    parser.add_argument('--iverilog', type=Path)
    parser.add_argument('--vvp', type=Path)
    parser.add_argument('--iverilog-base', type=Path)
    parser.add_argument('--original-bench', type=Path,
        help='optional unchanged failed-run TB; extracts its exact footer counterexample')
    parser.add_argument('--jobs', type=int, default=1)
    args = parser.parse_args()
    assert 1 <= args.jobs <= 6
    assert bool(args.iverilog) == bool(args.vvp), 'explicit Icarus compiler and runtime required together'
    assert not args.iverilog_base or args.iverilog
    out = args.output.resolve(strict=False)
    assert not out.exists() and out != ROOT and ROOT not in out.parents, 'fresh external output required'
    assert re.fullmatch(r'[-A-Za-z0-9_./]+', str(out)), 'quote-free external output path required'
    toolroot = args.verilator_root.resolve(strict=True)
    tool = toolroot / 'bin/verilator'
    tools = {'verilator': identity(tool), 'verilator_bin': identity(toolroot / 'bin/verilator_bin')}
    if args.iverilog:
        args.iverilog = args.iverilog.resolve(strict=True)
        args.vvp = args.vvp.resolve(strict=True)
        tools.update({'iverilog': identity(args.iverilog), 'vvp': identity(args.vvp)})
    sources = {str(path): identity(path) for path in (BENCH, Path(__file__).resolve(),
        ROOT / 'scripts/dataset_lifecycle_support.py')}
    source_text = BENCH.read_bytes().decode('utf-8')
    extracted = {name: extract_task(source_text, name) for name in TASKS}
    task_values = {name: value for name, (value, _) in extracted.items()}
    original_footer, original_diagnostic, original = None, None, None
    if args.original_bench:
        args.original_bench = args.original_bench.resolve(strict=True)
        sources[str(args.original_bench)] = identity(args.original_bench)
        original_footer, original_diagnostic, original = extract_original_footer(args.original_bench.read_bytes().decode('utf-8'))
    out.mkdir(parents=True)
    supervisor = Supervisor(out)
    summary = {'schema': 'openrx.dataset-gold-eof.regression.v1', 'status': 'running',
        'sources': sources, 'tools': tools, 'task_extraction': {name: row for name, (_, row) in extracted.items()},
        'historical_footer_extraction': original, 'cases': [], 'full_hash_executed': False,
        'full_hash_accepted': False, 'original_failed_run_reclassified': False,
        'tool_provenance_boundary': 'Actual tool byte identities; independently pinned provenance and resource admission belong to the caller.',
        'scope': 'Verbatim production file tasks only; no DUT/native/cache/full-hash workload. Fixture value checks are regression assertions, not a new strict lexical parser.'}
    save(out / 'summary.json', summary)
    try:
        supervisor.run('source-head', ['git', 'rev-parse', 'HEAD'], timeout=10)
        supervisor.run('source-tree', ['git', 'rev-parse', 'HEAD^{tree}'], timeout=10)
        supervisor.run('source-clean', ['git', 'status', '--porcelain', '--untracked-files=all'], timeout=10)
        assert not (out / 'source-clean.log').read_text().strip(), 'clean frozen source required'
        summary['source_head'] = (out / 'source-head.log').read_text().strip()
        summary['source_tree'] = (out / 'source-tree.log').read_text().strip()
        generated = out / 'tb_dataset_gold_eof.v'
        generated.write_text(tiny_top(task_values, original_footer))
        assert all(generated.read_text().count(value) == 1 for value in task_values.values())
        summary['generated_top'] = identity(generated)
        save(out / 'task-extraction.json', {'source': identity(BENCH),
            'tasks': summary['task_extraction'], 'generated_top': identity(generated),
            'verbatim_tasks_embedded_once': True, 'historical_footer': original})
        fixtures = out / 'fixtures'; fixtures.mkdir()
        stimuli = cases(original_diagnostic)
        for case in stimuli:
            path = fixtures / (case['name'] + '.hex')
            if case['fixture'] is not None:
                path.write_bytes(case['fixture'])
            case['path'] = path
        env = dict(os.environ, VERILATOR_ROOT=str(toolroot))
        supervisor.run('verilator-version', [str(tool), '--version'], timeout=10, env=env)
        supervisor.run('compile-verilator', [str(tool), '--binary', '--timing', '-j', str(args.jobs),
            '-Wno-fatal', '--top-module', 'tb_dataset_gold_eof', '--Mdir', str(out / 'obj-verilator'),
            '-o', 'sim', str(generated)], timeout=180, env=env)
        backends = {'verilator': [str(out / 'obj-verilator/sim')]}
        if args.iverilog:
            extra = ['-B', str(args.iverilog_base.resolve(strict=True))] if args.iverilog_base else []
            supervisor.run('iverilog-version', [str(args.iverilog), *extra, '-V'], timeout=10)
            supervisor.run('vvp-version', [str(args.vvp), '-V'], timeout=10)
            supervisor.run('compile-icarus', [str(args.iverilog), *extra, '-g2012', '-s', 'tb_dataset_gold_eof',
                '-o', str(out / 'sim-icarus'), str(generated)], timeout=60)
            backends['icarus'] = [str(args.vvp), str(out / 'sim-icarus')]
        else:
            summary['icarus'] = {'status': 'explicitly_not_requested'}
        for backend, command in backends.items():
            for case in stimuli:
                diagnostic = case['expected_diagnostic']
                if case.get('historical_counterexample') and backend == 'icarus':
                    diagnostic = None  # The historical guard follows Icarus's -1 EOF convention.
                expected_code = (-6,) if backend == 'verilator' else (1,)
                if diagnostic is None:
                    expected_code = (0,)
                label = backend + '-' + case['name']
                argv = [*command, '+fixture=' + str(case['path']), '+case_name=' + case['name'],
                        '+mode=' + str(case['mode']), '+rows=' + str(case['rows'])]
                result = supervisor.run(label, argv, timeout=10, env=env if backend == 'verilator' else None,
                    expected_returncodes=expected_code)
                log = (out / (label + '.log')).read_text()
                marker = 'PASS dataset_gold_eof case=' + case['name'] + ' rows=' + str(case['rows'])
                if diagnostic is None:
                    assert log.splitlines().count(marker) == 1, 'missing unique PASS marker: ' + label
                else:
                    assert diagnostic in log, 'wrong rejection diagnostic: ' + label
                    assert 'PASS dataset_gold_eof ' not in log, 'rejected case emitted PASS: ' + label
                assert result['wall_timeout'] is False and result['group_empty_after_cleanup'] is True
                summary['cases'].append({'backend': backend, 'case': case['name'], 'rows': case['rows'],
                    'mode': case['mode'], 'expected_diagnostic': diagnostic, 'returncode': result['returncode'],
                    'fixture': identity(case['path']) if case['path'].exists() else {'path': str(case['path']), 'absent': True},
                    'historical_counterexample': bool(case.get('historical_counterexample')),
                    'expected_outcome_verified': True})
                save(out / 'summary.json', summary)
        assert all(identity(Path(path)) == expected for path, expected in sources.items()), 'source inputs changed during regression'
        assert all(identity(Path(value['path'])) == value for value in tools.values()), 'tool inputs changed during regression'
        summary.update({'status': 'pass_bounded_production_gold_eof_regression',
            'source_and_tool_inputs_unchanged': True, 'backends': list(backends),
            'cases_per_backend': len(stimuli), 'case_outcomes_verified': len(summary['cases'])})
    except BaseException as error:
        summary.update({'status': 'failed', 'error': str(error)})
        raise
    finally:
        summary['commands'] = supervisor.commands
        save(out / 'summary.json', summary)
        manifest(out)


if __name__ == '__main__':
    main()
