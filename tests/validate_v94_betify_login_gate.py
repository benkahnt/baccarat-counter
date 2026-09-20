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
assert 'v21.2.94 – Betify-Login-Gate' in readme

# The 2026-09-15 bug: Deposit/Withdraw was visible to a signed-out visitor and
# must never be sufficient for SESSION_LOGGED_IN / LOGIN_COMPLETE.
assert 'betifyAuthenticatedBalanceTick_' in src
assert 'AUTH_BALANCE_RECENT' in src
assert 'Einzahlung/Deposit sichtbar, aber kein starker Login-Nachweis' in src
assert "recoveryEmit('WAIT_LOGIN_AUTH'" in src
assert 'Betify Kontostand sicher erkannt' in src
assert 'Betify angemeldet (Kontostand sicher erkannt)' in src
assert "if(accountAction || logoutAction)" not in src
assert "if(accountAction||logoutAction)" not in src
assert "if(logoutAction||accountAction)" not in src
assert "if(guestAccountAction||logoutAction)" not in src
assert "if(logoutAction||guestAccountAction)" not in src

# Strong positive proofs: explicit logout control or a recently validated
# account balance. Signed-out evidence retains priority.
probe_method = src.index('    std::string PragmaticProbeScript(')
probe_end = src.index('    std::string EvolutionBootstrapScript() const', probe_method)
probe = src[probe_method:probe_end]
assert "if(pass || openLogin)" in probe
assert "if(logoutAction || AUTH_BALANCE_RECENT)" in probe
assert probe.count("if(logoutAction||AUTH_BALANCE_RECENT)") >= 2
assert "recoveryExactButton(d,'Log in')" in probe
assert "recoveryExactButton(d,'Sign in')" in probe
assert 'recoveryLoginLink(d)' in probe
assert "getAttribute('aria-label')" in probe
assert "getAttribute('title')" in probe

watch_method = src.index('    std::string PragmaticSessionWatchScript() const')
watch_end = src.index('    std::string PragmaticProbeScript(', watch_method)
watch = src[watch_method:watch_end]
assert "if(pass||openLogin)" in watch
assert "if(logoutAction||AUTH_BALANCE_RECENT)" in watch
assert "if(guestAccountAction)" not in watch
assert "action:'AUTO_LOGOUT_DETECTED'" in watch

# Validate both modified embedded JavaScript programs exactly as C++ assembles
# them (using representative dynamic values).
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
            probe_chunks[4].group(1) + '1' +
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

print('v21.2.96 retains v94 strong-auth login gate; passive Deposit logout removed: OK')
