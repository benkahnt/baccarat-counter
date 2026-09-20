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

focus_start = src.index('void PragmaticFocusSignalTable')
focus = src[focus_start:]

# A) v104 resolves chip controls in the actual context document and retains a
# conservative direct-denomination fallback outside all table-ID tiles.
for token in [
    'const chipRackRoot=(contextEl=null)=>',
    'const doc=(contextEl&&contextEl.ownerDocument)||document;',
    'const directChipFallback=(cents,currentTable)=>',
    'const chipDirectVerified=new WeakSet();',
    "if(r.width>0&&r.height>0&&r.width<=520&&r.height<=520&&/\\bID\\s*:\\s*\\d+/i.test",
    "if(nearby.size<5||!nearby.has('0.2')||!nearby.has('1')||!nearby.has('2'))continue;",
    "source:'direct-denom-cluster'",
    'pairChipRackBeforeSignature=chipRackSignature(currentTable)',
    'const rackAfterSignature=chipRackSignature(tableAfter);',
]:
    assert token in focus, token

# Pair fields remain unreachable until denomination selection is confirmed.
verify_pos = focus.index('pairChipSelectionConfirmed')
stake_ready_pos = focus.index('operation.stakePrepared=true;', verify_pos)
pair_coords_pos = focus.index('__BAC_PAIR_CLICK_COORDS__', stake_ready_pos)
assert verify_pos < stake_ready_pos < pair_coords_pos
assert "finishRetry('pair-chip-selection-unconfirmed')" in focus

# The actual denomination selection is still backed by trusted CDP input.
coords_start = src.index('if (auto value = extractConsoleValue("__BAC_STAKE_PREP_COORDS__")')
coords_end = src.index('if (auto value = extractConsoleValue("__BAC_STAKE_PREP_CONFIRM__")', coords_start)
coords = src[coords_start:coords_end]
assert 'Input.dispatchMouseEvent' in coords
assert '"select-pair-chip-" + std::to_string(pairChipDenomCents)' in coords

# B) The screenshot must use the complete top-level page session, never the
# shortened display id or a child-frame session. v113 captures the viewport
# without a clip and retains MULTIPLAY tile coordinates as metadata only.
multi_start = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM__")')
multi_end = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM_ERROR__")', multi_start)
multi = src[multi_start:multi_end]
assert 'PragmaticRequestTopLevelBurnScreenshot(' in multi
helper_start = src.index('    uint64_t PragmaticRequestTopLevelBurnScreenshot(')
helper_end = src.index('    void HandlePragmaticBurnScreenshotResponse(', helper_start)
helper = src[helper_start:helper_end]
assert 'const std::string pageSession = PragmaticTopLevelPageSession();' in helper
assert 'SendCommandChecked("Page.captureScreenshot", params, pageSession, requestId)' in helper
assert 'pageSession, tableId, tableName, sampleIndex, probeSample,' in helper
assert 'PRAGMATIC_BURN_NATIVE_SCREENSHOT_REQUEST' in helper
assert r'\"captureBeyondViewport\":false' in helper
assert r'\"clip\"' not in helper
assert 'requested-tile-metadata-only' in helper
assert 'PragmaticStrategySubtractCard' not in helper
assert 'PragmaticStrategySubtractCard' not in multi

# Screenshot response remains diagnostic-only.
shot_start = src.index('    void HandlePragmaticBurnScreenshotResponse(')
shot_end = src.index('    void HandlePragmaticTrustedPairClickResponse(', shot_start)
shot = src[shot_start:shot_end]
assert 'PRAGMATIC_BURN_NATIVE_SCREENSHOT' in shot
assert 'jpegBase64' in shot
assert 'PragmaticStrategySubtractCard' not in shot

# C) Syntax-check the full embedded focus JavaScript after the context changes.
m = re.search(r'void PragmaticFocusSignalTable.*?std::string js = R"JS\(\(async\(\)=>\{try\{(.*?)\}\)\(\)\)JS"', src, re.S)
# validate_focus_js.py is the canonical extractor; run it instead if this
# intentionally conservative regex stops matching after formatting changes.
subprocess.run([__import__('sys').executable, str(ROOT / 'tests' / 'validate_focus_js.py')], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# D) Strategy math and Telegram settlement are unchanged from the validated
# pre-v104 line. Pair transport is intentionally changed by this release.
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

# E) v103 Excel logical-session de-duplication remains present.
subprocess.run([__import__('sys').executable, str(ROOT / 'tests' / 'validate_v103_session_excel_dedupe.py')], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print('v21.2.105 MULTIPLAY chip context + full-session Burn screenshot: OK')
