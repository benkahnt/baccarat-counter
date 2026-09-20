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

# A) Pair denomination safety: selecting 0.20 is not treated as successful just
# because CDP accepted the mouse event. JavaScript must verify a semantic DOM
# state change/active marker before any Pair field is armed.
focus_start = src.index('void PragmaticFocusSignalTable')
focus = src[focus_start:]
for token in [
    'const chipSelectionSignature=el=>',
    'const chipActiveEvidence=el=>',
    '__BAC_STAKE_PREP_CHIP_VERIFY__',
    'pairChipSelectionConfirmed',
    "finishRetry('pair-chip-selection-unconfirmed')",
    'pairChipSelectAttempts',
    'operation.stakePrepRequested=false',
]:
    assert token in focus, token
assert '(operation.pairChipSelectAttempts||0)<3' in focus
# Pair targets are reached only after stakePrepared becomes true.
verify_pos = focus.index('pairChipSelectionConfirmed')
stake_ready_pos = focus.index('operation.stakePrepared=true;', verify_pos)
pair_coord_pos = focus.index('__BAC_PAIR_CLICK_COORDS__', stake_ready_pos)
assert verify_pos < stake_ready_pos < pair_coord_pos

# C++ keeps a dedicated diagnostic event for the post-click verification.
assert 'PRAGMATIC_STAKE_PREP_CHIP_VERIFY' in src

# B) Burn Probe v5: if the tile video element is not ready, a same-origin blob
# image is captured through canvas. Early small ws1 binary fragments are also
# retained so a possible fMP4 init segment is available for offline decoding.
fn_start = src.index('    std::string PragmaticBurnMultiDomProbeScript(')
fn_end = src.index('    void MaybePragmaticBurnMultiDomProbe()', fn_start)
fn = src[fn_start:fn_end]
for token in [
    "root.querySelectorAll('img')",
    "startsWith('blob:')",
    'imageJpegBase64',
    "mediaKind='blob-image'",
    'const jpegOf=',
]:
    assert token in fn, token
assert 'PRAGMATIC_VIDEO_EARLY_BINARY' in src
assert 'PragmaticVideoStreamMatchAny' in src
assert 'pragmaticVideoEarlyBinaryCapturedByStream_' in src

# Syntax-check the Burn Probe JS.
m = re.search(r'R"JS\((.*?)\)JS"', fn, re.S)
assert m
js = m.group(1).replace('__RUN__', 'test-run').replace(
    '__TARGETS__', '[{"tableid":"t1","name":"Baccarat 1"}]')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
    f.write(js + ';\n')
    js_path = Path(f.name)
subprocess.run(['node', '--check', str(js_path)], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
js_path.unlink(missing_ok=True)

# C) Burn images/video remain diagnostics only; strategy application still goes
# through the existing unique-candidate confirmation gate.
handler_start = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM__")')
handler_end = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM_ERROR__")', handler_start)
handler = src[handler_start:handler_end]
assert 'PragmaticStrategySubtractCard' not in handler
confirm_start = src.index('    void PragmaticConfirmPendingBurn(')
confirm_end = src.index('    void PragmaticStrategySubtractHand(', confirm_start)
confirm = src[confirm_start:confirm_end]
assert 'st.pendingBurnDistinctCandidates == 1' in confirm
assert '!st.pendingBurnAmbiguous' in confirm
assert confirm.count('PragmaticStrategySubtractCard(st, confirmedCard)') == 1

# D) Sensitive math, settlement and final Pair click transport are unchanged.
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

print('v21.2.102 pair-chip verification + Burn Probe v5: OK')
