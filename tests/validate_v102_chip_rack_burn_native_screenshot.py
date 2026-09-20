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

# A) The denomination lookup is constrained to the real chip rack. The old
# document-wide "0,2" lookup could hit a table-minimum label instead.
focus_start = src.index('void PragmaticFocusSignalTable')
focus = src[focus_start:]
for token in [
    'const denomCanonical=s=>',
    'const chipRackRoot=(contextEl=null)=>',
    "new Set(['0.2','1','2','5','25','100','250','1000'])",
    "if(/\\bID\\s*:\\s*\\d+/i.test(txt))continue;",
    "if(found.size<3||!found.has('0.2')||!found.has('1')||!found.has('2'))continue;",
    'const directChipFallback=(cents,currentTable)=>',
    "source:'direct-denom-cluster'",
    "rack.querySelectorAll('button,[role=\"button\"],[data-value],[data-amount],[data-chip],[aria-label],[title],input')",
    'pairChipRackBeforeSignature=chipRackSignature(currentTable)',
    'rackSignatureChanged',
    '__BAC_STAKE_PREP_CHIP_VERIFY__',
]:
    assert token in focus, token
assert 'if(leaves.length>1200)break;' in focus

# Pair-only signals use the exact rack point with a native trusted CDP click;
# a JavaScript click is merely a warm-up and never bypasses this click.
handler_start = src.index('if (auto value = extractConsoleValue("__BAC_STAKE_PREP_COORDS__")')
handler_end = src.index('if (auto value = extractConsoleValue("__BAC_STAKE_PREP_CONFIRM__")', handler_start)
handler = src[handler_start:handler_end]
assert 'pairChipDomClicked' in handler
assert 'if (allSent && (!mainRequired || mainChipCents != pairChipDenomCents))' in handler
assert '!pairChipDomClicked' not in handler[handler.index('bool allSent = true;'):]
assert '"select-pair-chip-" + std::to_string(pairChipDenomCents)' in handler
assert 'Input.dispatchMouseEvent' in handler

# Pair targets are still gated behind post-selection verification.
verify_pos = focus.index('pairChipSelectionConfirmed')
stake_ready_pos = focus.index('operation.stakePrepared=true;', verify_pos)
pair_coord_pos = focus.index('__BAC_PAIR_CLICK_COORDS__', stake_ready_pos)
assert verify_pos < stake_ready_pos < pair_coord_pos
assert "finishRetry('pair-chip-selection-unconfirmed')" in focus

# B) Native Chrome viewport screenshots retain the MULTIPLAY tile coordinates
# as diagnostic metadata. They must not resize the live page through CDP clip.
burn_fn_start = src.index('    std::string PragmaticBurnMultiDomProbeScript(')
burn_fn_end = src.index('    void MaybePragmaticBurnMultiDomProbe()', burn_fn_start)
burn_fn = src[burn_fn_start:burn_fn_end]
for token in [
    'const toHostPageRect=rr=>',
    'rootPageRect:rp',
    'rootPageX:rp?rp.x:-1',
    'rootPageY:rp?rp.y:-1',
    'rootPageW:rp?rp.w:0',
    'rootPageH:rp?rp.h:0',
]:
    assert token in burn_fn, token

multi_handler_start = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM__")')
multi_handler_end = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM_ERROR__")', multi_handler_start)
multi_handler = src[multi_handler_start:multi_handler_end]
for token in [
    'PragmaticRequestTopLevelBurnScreenshot(',
    'pragmaticBurnNativeScreenshotCountByTable_',
    'pragmaticBurnNativeProbeSamplesByTable_',
    'probeSample == 1 || probeSample == 5',
    'probeSample == 10 || probeSample == 15',
]:
    assert token in multi_handler, token
assert 'PragmaticStrategySubtractCard' not in multi_handler
helper_start = src.index('    uint64_t PragmaticRequestTopLevelBurnScreenshot(')
helper_end = src.index('    void HandlePragmaticBurnScreenshotResponse(', helper_start)
helper = src[helper_start:helper_end]
assert 'SendCommandChecked("Page.captureScreenshot", params, pageSession, requestId)' in helper
assert 'const std::string pageSession = PragmaticTopLevelPageSession();' in helper
assert r'\"captureBeyondViewport\":false' in helper
assert r'\"clip\"' not in helper
assert 'requested-tile-metadata-only' in helper
assert 'pragmaticBurnScreenshotRequests_.empty()' in helper
assert 'PragmaticStrategySubtractCard' not in helper

shot_start = src.index('    void HandlePragmaticBurnScreenshotResponse(')
shot_end = src.index('    void HandlePragmaticTrustedPairClickResponse(', shot_start)
shot = src[shot_start:shot_end]
assert 'PRAGMATIC_BURN_NATIVE_SCREENSHOT' in shot
assert 'jpegBase64' in shot
assert 'PragmaticStrategySubtractCard' not in shot
assert 'HandlePragmaticBurnScreenshotResponse(json);' in src

# Syntax-check the embedded MULTIPLAY Burn JS.
m = re.search(r'R"JS\((.*?)\)JS"', burn_fn, re.S)
assert m
js = m.group(1).replace('__RUN__', 'test-run').replace(
    '__TARGETS__', '[{"tableid":"t1","name":"Baccarat 1"}]')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
    f.write(js + ';\n')
    js_path = Path(f.name)
subprocess.run(['node', '--check', str(js_path)], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
js_path.unlink(missing_ok=True)

# C) Burn still enters strategy only through the proven unique-candidate gate.
confirm_start = src.index('    void PragmaticConfirmPendingBurn(')
confirm_end = src.index('    void PragmaticStrategySubtractHand(', confirm_start)
confirm = src[confirm_start:confirm_end]
assert 'st.pendingBurnDistinctCandidates == 1' in confirm
assert '!st.pendingBurnAmbiguous' in confirm
assert confirm.count('PragmaticStrategySubtractCard(st, confirmedCard)') == 1

# D) Sensitive Edge math, Telegram settlement and real Pair bet transport are
# unchanged from the validated v101 line.
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
}
for signature, expected in hashes.items():
    body = extract_function(src, signature)
    assert hashlib.sha256(body.encode()).hexdigest() == expected, signature

print('v21.2.102 chip-rack selection + v113 safe Burn viewport screenshot: OK')
