from pathlib import Path
import subprocess, json, time
root=Path(__file__).resolve().parents[1]
out=root/'.validation';out.mkdir(exist_ok=True)
results=[]
def run(label, cmd):
 t=time.monotonic()
 try:
  p=subprocess.run(cmd,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=70)
  ok=p.returncode==0;txt=p.stdout
 except subprocess.TimeoutExpired as e:
  ok=False;txt='TIMEOUT '+str(e)
 results.append({'test':label,'ok':ok,'seconds':round(time.monotonic()-t,3),'output':txt})
 print(('PASS ' if ok else 'FAIL ')+label,flush=True)
 if not ok: print(txt[-3500:],flush=True)
 (out/'v107_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
names=[
 'validate_v83_all_tables_trusted_click.py','validate_v84_all_tables_root_coords.py',
 'validate_v85_stoploss_telegram.py',
 'validate_v87_dynamic_pair_main_bet.py','validate_v88_pair_amount_composition.py',
 'validate_v89_sidebet_logging_no_combined_ev_gate.py',
 'validate_v90_combined_ev_toggle_excel_model.py',
 'validate_v92_telegram_signal_results.py','validate_v93_telegram_signal_settlement.py',
 'validate_v94_betify_login_gate.py','validate_v95_betify_session_stability.py',
 'validate_v96_confirmed_burn_tracking.py','validate_v97_burn_column_telegram_token_session_start.py',
 'validate_v98_burn_probe_v2.py',
 'validate_v100_chip_retry_burn_probe_v4.py','validate_v101_pair_chip_verify_burn_probe_v5.py',
 'validate_v103_session_excel_dedupe.py',
 'validate_v105_focus_main_burn_capture.py',
 'validate_v106_separate_min_edge.py','validate_v107_chip_cluster_two_phase.py','validate_balance_js.py','validate_focus_js.py']
for name in names:run(name,[__import__('sys').executable,str(root/'tests'/name)])
for name in ['confirmed_bet_accounting_test','pragmatic_main_ev_reference_test','unit_target_logic_test','session_export_test','strategy_edge_thresholds_test']:
 exe=out/name
 run(name+' compile',['g++','-std=c++20','-O2','-Wall','-Wextra','-I'+str(root/'src'),str(root/'tests'/(name+'.cpp')),'-o',str(exe)])
 if exe.exists():run(name+' execute',[str(exe)])
run('validate_session_xlsx.py',[__import__('sys').executable,str(root/'tests/validate_session_xlsx.py')])
print('TOTAL',sum(x['ok'] for x in results),'/',len(results),flush=True)

raise SystemExit(0 if all(x["ok"] for x in results) else 1)
