"""Portable regression suite; on Windows use an x64 Native Tools prompt."""
from pathlib import Path
import ast, json, os, subprocess, sys, time
from test_toolchain import compile_cpp

root = Path(__file__).resolve().parents[1]
os.chdir(root)
out = root/'.validation'; out.mkdir(exist_ok=True)
temp = out/'tmp';temp.mkdir(exist_ok=True)
os.environ['TEMP'] = os.environ['TMP'] = str(temp)
previous = json.loads((out/'v111_results.json').read_text(encoding='utf-8')) if '--failed' in sys.argv and (out/'v111_results.json').exists() else []
results=[x for x in previous if x['ok']]
passed={x['test'] for x in results}
def run(name, action):
    if name in passed:return
    start=time.monotonic()
    try:
        output=action()
        result={'test':name,'ok':True,'output':str(output or '')}
    except Exception as e:
        result={'test':name,'ok':False,'output':str(e)}
    result['seconds']=round(time.monotonic()-start,3)
    results.append(result)
    print(('PASS ' if result['ok'] else 'FAIL ')+name,flush=True)
    if not result['ok']:print(result['output'][-3000:],flush=True)
    (out/'v111_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
def command(args):
    p=subprocess.run(args,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
    if p.returncode:raise RuntimeError(p.stdout)
    return p.stdout

tree=ast.parse((root/'tests/run_v107_suite.py').read_text(encoding='utf-8'))
names=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='names' for t in n.targets))
names.extend(['validate_v108_chip_selector_transport.py', 'validate_v110_configured_export_model.py', 'validate_v111_tie_evolution_telegram.py'])
for name in names:run(name,lambda name=name:command([sys.executable,str(root/'tests'/name)]))
for name in ['confirmed_bet_accounting_test','pragmatic_main_ev_reference_test','unit_target_logic_test','session_export_test','strategy_edge_thresholds_test']:
    def compile_and_run(name=name):
        exe=compile_cpp(root/'tests'/(name+'.cpp'),out/name,[root/'src'])
        return command([str(exe)])
    run(name+' compile + execute',compile_and_run)
run('validate_session_xlsx.py',lambda:command([sys.executable,str(root/'tests/validate_session_xlsx.py')]))
print('TOTAL',sum(x['ok'] for x in results),'/',len(results),flush=True)
raise SystemExit(0 if all(x['ok'] for x in results) else 1)
