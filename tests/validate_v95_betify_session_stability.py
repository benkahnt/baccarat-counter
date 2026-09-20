from pathlib import Path
import re
import subprocess
import tempfile
from test_toolchain import temporary_directory

root = Path(__file__).resolve().parents[1]
src = (root / 'src' / 'main.cpp').read_text(encoding='utf-8')
build = (root / 'build.bat').read_text(encoding='ascii')
readme = (root / 'README.md').read_text(encoding='utf-8')

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'Baccarat Counter v21.2.123' in src
assert 'v21.2.95 – Betify-Session stabilisiert' in readme

# Passive session watch: Deposit/Withdraw and registration-only controls are
# neutral. Only a visible password/login control may emit AUTO_LOGOUT_DETECTED.
watch_method = src.index('    std::string PragmaticSessionWatchScript() const')
watch_end = src.index('    std::string PragmaticProbeScript(', watch_method)
watch = src[watch_method:watch_end]
assert "if(pass||openLogin)" in watch
assert "if(pass||openLogin||openRegister)" not in watch
assert "exact(d,'Einzahlung')" not in watch
assert "exact(d,'Deposit')" not in watch
assert "exact(d,'Auszahlung')" not in watch
assert "exact(d,'Withdraw')" not in watch
assert "return'session-watch:guest-account-action'" not in watch
assert "detail:pass?'Betify Loginformular sichtbar':'Betify Anmelden/Login sichtbar'" in watch
assert "if(logoutAction||AUTH_BALANCE_RECENT)" in watch

# Probe Stage 0 has the same neutral policy. Stage 1/2 still retain the v94
# strong-auth gate, where Deposit/Withdraw are allowed only as an ambiguous
# WAIT state and can never prove LOGIN_COMPLETE.
probe_method = src.index('    std::string PragmaticProbeScript(')
probe_end = src.index('    std::string EvolutionBootstrapScript() const', probe_method)
probe = src[probe_method:probe_end]
stage0_start = probe.index('if(RECOVERY_STAGE===0')
stage0_end = probe.index('if(!RECOVERY_STAGE)return;', stage0_start)
stage0 = probe[stage0_start:stage0_end]
assert "if(pass || openLogin)" in stage0
assert "openRegister" not in stage0
assert "guestAccountAction" not in stage0
assert "recoveryExactButton(d,'Einzahlung')" not in stage0
assert "recoveryExactButton(d,'Deposit')" not in stage0
assert "recoveryExactButton(d,'Auszahlung')" not in stage0
assert "recoveryExactButton(d,'Withdraw')" not in stage0
assert "'AUTO_LOGOUT_DETECTED'" in stage0
assert "if(logoutAction || AUTH_BALANCE_RECENT)" in stage0

stage1_start = probe.index('if(RECOVERY_STAGE===1', stage0_end)
stage2_start = probe.index('if(RECOVERY_STAGE===2', stage1_start)
stage3_start = probe.index('if((RECOVERY_STAGE===3||RECOVERY_STAGE===4)', stage2_start)
stage1 = probe[stage1_start:stage2_start]
stage2 = probe[stage2_start:stage3_start]
assert "recoveryExactButton(d,'Einzahlung')" in stage1
assert "recoveryEmit('WAIT_LOGIN_AUTH'" in stage1
assert "if(logoutAction||AUTH_BALANCE_RECENT)" in stage1
assert "recoveryExactButton(d,'Einzahlung')" in stage2
assert "if(logoutAction||AUTH_BALANCE_RECENT)" in stage2
assert "recoveryEmit('WAIT_LOGIN_COMPLETE'" in stage2

# Native defense-in-depth must reject old/stale ambiguous logout payloads
# before providerLoginComplete is cleared or shoe counts are invalidated.
handler_start = src.index('                if (action == "AUTO_LOGOUT_DETECTED") {')
handler_end = src.index('                } else if (action == "SESSION_LOGGED_IN") {', handler_start)
handler = src[handler_start:handler_end]
assert 'PRAGMATIC_AMBIGUOUS_LOGOUT_IGNORED' in handler
for token in ['Einzahlung', 'Deposit', 'Auszahlung', 'Withdraw', 'Withdrawal']:
    assert f'detail.find("{token}")' in handler
assert handler.index('if (ambiguousAccountAction)') < handler.index('providerLoginComplete_.store(false')
assert handler.index('if (ambiguousAccountAction)') < handler.index('PragmaticInvalidateForSessionLoss(detail);')

# Validate both embedded JavaScript programs exactly as C++ assembles them.
watch_js_start = src.index('std::string js = R"JS(', watch_method)
watch_js_end = src.index('        return js;', watch_js_start)
watch_segment = src[watch_js_start:watch_js_end]
watch_chunks = list(re.finditer(r'R"JS\((.*?)\)JS"', watch_segment, re.S))
assert len(watch_chunks) == 3, len(watch_chunks)
watch_js = (watch_chunks[0].group(1) + 'test-run' +
            watch_chunks[1].group(1) + 'false' +
            watch_chunks[2].group(1))

probe_js_start = src.index('std::string js = R"JS(', probe_method)
probe_js_end = src.index('        const std::string targetMarker', probe_js_start)
probe_segment = src[probe_js_start:probe_js_end]
probe_chunks = list(re.finditer(r'R"JS\((.*?)\)JS"', probe_segment, re.S))
assert len(probe_chunks) == 6, len(probe_chunks)
probe_js = (probe_chunks[0].group(1) + 'test-run' +
            probe_chunks[1].group(1) + 'false' +
            probe_chunks[2].group(1) + 'false' +
            probe_chunks[3].group(1) + 'false' +
            probe_chunks[4].group(1) + '0' +
            probe_chunks[5].group(1))
probe_js = probe_js.replace('__BCP_SELECTED_PROVIDER_GAME_URL__',
                            'https://betify2.so/de/play/107240-baccarat-1')

with temporary_directory() as d:
    d = Path(d)
    wp = d / 'session-watch.js'
    pp = d / 'login-gate.js'
    wp.write_text(watch_js, encoding='utf-8')
    pp.write_text(probe_js, encoding='utf-8')
    subprocess.run(['node', '--check', str(wp)], check=True)
    subprocess.run(['node', '--check', str(pp)], check=True)

print('v21.2.96 Betify session stability / false logout regression: OK')
