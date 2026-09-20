from pathlib import Path
import hashlib
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / 'src' / 'main.cpp').read_text(encoding='utf-8')
build_b = (ROOT / 'build.bat').read_bytes()
build = build_b.decode('utf-8', errors='replace')
readme = (ROOT / 'README.md').read_text(encoding='utf-8')

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'BaccaratCounter/21.2.110' in src
assert 'Baccarat Counter v21.2.123' in src
assert '# Baccarat Counter v21.2.123' in readme
assert b'\r\n' in build_b and build_b.count(b'\r\n') > 50

# A) v99 capture finding: stake prep must not fail immediately if the chip
# selector has not rendered a few milliseconds after table focus.
focus_start = src.index('void PragmaticFocusSignalTable')
focus_end = src.index('void PragmaticRememberRuntimeSession', focus_start) if 'void PragmaticRememberRuntimeSession' in src[focus_start:] else len(src)
focus = src[focus_start:]
assert "const chipTarget=(cents,currentTable)=>" in focus
assert '__BAC_STAKE_PREP_WAITING__' in focus
assert "finishRetry('stake-prep-control-not-found')" not in focus
assert 'stakeControlWaitStartedAt' in focus and 'stakeControlWaitLogAt' in focus
assert "pairChipCandidates:phase==='pair'?(lastChipSearchDiag" in focus
assert "querySelectorAll('button,[role=\"button\"],[data-value],[data-amount],[data-chip],[data-denomination],[aria-label],[title],input')" in focus
assert "ROOT_WINDOW.setTimeout(probeAndMaybeArm,180)" in focus

# A2) Multiplay activation uses the table-name/header coordinates and a native
# trusted CDP click; no betting spot is used for this activation click.
assert '__BAC_TILE_ACTIVATE_COORDS__' in focus
assert '__BAC_TILE_ACTIVATE_COORDS__' in src
assert 'PRAGMATIC_TILE_ACTIVATE_TRUSTED_CLICK' in src
activate_js = focus[focus.index("__BAC_TILE_ACTIVATE_COORDS__")-1200:focus.index("__BAC_TILE_ACTIVATE_COORDS__")+1200]
assert 'const nameNode=exactNameNode();' in activate_js
assert 'const nameEl=nameNode&&nameNode.parentElement;' in activate_js
activate_handler_start = src.index('if (auto value = extractConsoleValue("__BAC_TILE_ACTIVATE_COORDS__")')
activate_handler_end = src.index('if (auto value = extractConsoleValue("__BAC_STAKE_PREP_COORDS__")', activate_handler_start)
activate_handler = src[activate_handler_start:activate_handler_end]
assert 'betsOpenStillConfirmed' in activate_handler
assert 'PragmaticAutoBetRequestActive(*tableId, *sourceGameId)' in activate_handler
assert 'Input.dispatchMouseEvent' in activate_handler

# B) Burn Probe v4 must execute through the proven runtime even if Chrome only
# exposes /desktop/launcher/ and the MULTIPLAY document lives in iframe#MTB.
fn_start = src.index('    std::string PragmaticBurnMultiDomProbeScript(')
fn_end = src.index('    void MaybePragmaticBurnMultiDomProbe()', fn_start)
fn = src[fn_start:fn_end]
assert "document.getElementById('MTB')" in fn
assert 'context=\'launcher/MTB\'' in fn
assert 'mtb.contentWindow' in fn
assert 'const NF=w.NodeFilter||NodeFilter;' in fn
assert "const visible=el=>" in fn
# Off-screen rendered tiles are accepted: the v99 viewport intersection gate
# (r.bottom/r.top/innerHeight) is no longer part of this helper.
visible_line = re.search(r"const visible=el=>\{.*?\};", fn, re.S).group(0)
for forbidden in ('r.bottom>0', 'r.top<innerHeight', 'r.left<innerWidth'):
    assert forbidden not in visible_line
assert 'context,hostHref,href,rootFound' in fn

probe_start = src.index('    void MaybePragmaticBurnMultiDomProbe()')
probe_end = src.index('    static std::string PragmaticJoinCards', probe_start)
probe = src[probe_start:probe_end]
assert 'const std::vector<std::string> sessions = PragmaticRuntimeSessions();' in probe
assert 'for (const auto& sid : sessions)' in probe
assert 'lower.find("/desktop/multibaccarat/")' not in probe

# Syntax-check Burn Probe v4 JS with a synthetic table target.
m = re.search(r'R"JS\((.*?)\)JS"', fn, re.S)
assert m, 'MULTIPLAY Burn DOM JS raw literal not found'
js = m.group(1).replace('__RUN__', 'test-run').replace(
    '__TARGETS__', '[{"tableid":"t1","name":"Baccarat 1"}]')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
    f.write(js + ';\n')
    js_path = Path(f.name)
subprocess.run(['node', '--check', str(js_path)], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
js_path.unlink(missing_ok=True)

# C) Burn safety gate remains unchanged: DOM/video diagnostics cannot directly
# modify composition; first betsopen still performs the single-candidate proof.
handler_start = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM__")')
handler_end = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM_ERROR__")', handler_start)
handler = src[handler_start:handler_end]
assert 'if (!rootFound) return;' in handler
assert 'st.pendingBurnDomConsensusSamples >= 2' in handler
assert 'eligibleCount == 0 && st.pendingBurnDomCommitted' in handler
assert 'PragmaticStageBurnDomConsensus' in handler
assert 'PragmaticStrategySubtractCard' not in handler

confirm_start = src.index('    void PragmaticConfirmPendingBurn(')
confirm_end = src.index('    void PragmaticStrategySubtractHand(', confirm_start)
confirm = src[confirm_start:confirm_end]
assert 'st.pendingBurnDistinctCandidates == 1' in confirm
assert '!st.pendingBurnAmbiguous' in confirm
assert confirm.count('PragmaticStrategySubtractCard(st, confirmedCard)') == 1

# D) Sensitive math, Telegram settlement and the final trusted Pair click
# transport remain byte-identical in behavior/hashes from v99.
def extract_function(text, signature):
    i = text.index(signature)
    b = text.index('{', i)
    depth = 0
    state = 'normal'
    esc = False
    j = b
    while j < len(text):
        c = text[j]
        n = text[j + 1] if j + 1 < len(text) else ''
        if state == 'line':
            if c == '\n': state = 'normal'
        elif state == 'block':
            if c == '*' and n == '/': state = 'normal'; j += 1
        elif state == 'str':
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': state = 'normal'
        elif state == 'char':
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == "'": state = 'normal'
        else:
            if c == '/' and n == '/': state = 'line'; j += 1
            elif c == '/' and n == '*': state = 'block'; j += 1
            elif c == '"': state = 'str'
            elif c == "'": state = 'char'
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return text[i:j + 1]
        j += 1
    raise AssertionError('unbalanced function')

hashes = {
    'PragmaticStrategyMath(const PragmaticTableRuntime& st) const': 'c9be49425035bb2b84569b8c803c92d690024314ede223982e43441e78a2c9bf',
    'QueueTelegramSignalSettlement(HWND hwnd': '2726f2b51a6a0213761aa66bfcb120ff7e585489eb4b422f7f1be67bd55a3117',
    'bool PragmaticClickPairBet(': '298a181b6081de73354c78aeee9f26fa34ed47473ac9de48ef5757baadc93b05',
}
for signature, expected in hashes.items():
    body = extract_function(src, signature)
    assert hashlib.sha256(body.encode()).hexdigest() == expected, signature

print('v21.2.102 chip-control retry + trusted tile activation + Burn Probe v4: OK')
