"""Windows x64 regression suite for the one-shot Pragmatic chip test."""
from pathlib import Path
import ast, json, os, subprocess, sys, time
from test_toolchain import compile_cpp

root = Path(__file__).resolve().parents[1]
os.chdir(root)
out = root / '.validation'
out.mkdir(exist_ok=True)
temp = out / 'tmp'
temp.mkdir(exist_ok=True)
os.environ['TEMP'] = os.environ['TMP'] = str(temp)
result_file = out / 'v115_results.json'
previous = json.loads(result_file.read_text(encoding='utf-8')) if '--failed' in sys.argv and result_file.exists() else []
results = [case for case in previous if case['ok']]
passed = {case['test'] for case in results}

def run(name, action):
    if name in passed:
        return
    start = time.monotonic()
    try:
        output = action()
        case = {'test': name, 'ok': True, 'output': str(output or '')}
    except Exception as exc:
        case = {'test': name, 'ok': False, 'output': str(exc)}
    case['seconds'] = round(time.monotonic() - start, 3)
    results.append(case)
    print(('PASS ' if case['ok'] else 'FAIL ') + name, flush=True)
    if not case['ok']:
        print(case['output'][-3000:], flush=True)
    result_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')

def command(args):
    process = subprocess.run(args, cwd=root, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, timeout=120)
    if process.returncode:
        raise RuntimeError(process.stdout)
    return process.stdout

tree = ast.parse((root / 'tests/run_v107_suite.py').read_text(encoding='utf-8'))
names = next(ast.literal_eval(node.value) for node in tree.body
             if isinstance(node, ast.Assign) and
             any(isinstance(target, ast.Name) and target.id == 'names'
                 for target in node.targets))
names.extend([
    'validate_v108_chip_selector_transport.py',
    'validate_v110_configured_export_model.py',
    'validate_v111_tie_evolution_telegram.py',
    'validate_v112_betting_window.py',
    'validate_v113_viewport.py',
    'validate_v113_signal_accounting.py',
    'validate_v114_default_mode.py',
    'validate_v115_manual_chip_test.py',
])
for name in names:
    run(name, lambda name=name: command([sys.executable, str(root / 'tests' / name)]))
for name in ['confirmed_bet_accounting_test', 'pragmatic_main_ev_reference_test',
             'unit_target_logic_test', 'session_export_test',
             'strategy_edge_thresholds_test']:
    def compile_and_run(name=name):
        exe = compile_cpp(root / 'tests' / (name + '.cpp'), out / name, [root / 'src'])
        return command([str(exe)])
    run(name + ' compile + execute', compile_and_run)
run('validate_session_xlsx.py',
    lambda: command([sys.executable, str(root / 'tests/validate_session_xlsx.py')]))
print('TOTAL', sum(case['ok'] for case in results), '/', len(results), flush=True)
raise SystemExit(0 if all(case['ok'] for case in results) else 1)
