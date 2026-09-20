from pathlib import Path
import hashlib
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / 'src' / 'main.cpp').read_text(encoding='utf-8')
build = (ROOT / 'build.bat').read_text(encoding='utf-8', errors='replace')
readme = (ROOT / 'README.md').read_text(encoding='utf-8')

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'Baccarat Counter v21.2.123' in src
assert '# Baccarat Counter v21.2.123' in readme
assert 'Burn Probe v3' in readme

# A) Existing protocol/raw probe is retained.
assert 'PRAGMATIC_BURN_RAW_FRAME' in src
assert 'PragmaticMaybeStageAlternateBurnEvidence' in src
assert 'MaybePragmaticBurnDomProbe();' in src

# B) New Multiplay visual probe operates on all active burn windows, not only
# the primary launcher table.
assert 'PragmaticBurnMultiDomProbeScript' in src
assert 'MaybePragmaticBurnMultiDomProbe' in src
assert 'pragmaticBurnRawProbeUntilByTable_' in src
assert 'now - pragmaticBurnMultiDomLastEvalTick_ < 220ULL' in src
assert '/desktop/multibaccarat/' in src
assert '__BAC_PRAGMATIC_BURN_MULTI_DOM__' in src
assert 'PRAGMATIC_BURN_MULTI_DOM_SAMPLE' in src
assert 'exactTextParents' in src and 'findRoot' in src
assert 'rootFound' in src and 'eligibleCount' in src and 'singleCard' in src
assert 'structure' in src and 'snapshot' in src
assert "querySelectorAll('svg,img,video,canvas')" in src
assert "root.querySelectorAll('svg,use,img,video,canvas,[data-rank],[data-suit]')" in src

# B2) Video is a third diagnostic channel.  The tableconfig video URL is used
# only to associate a short binary evidence sample with the active shoe, while
# a rendered MULTIPLAY <video> may contribute up to three JPEG diagnostics.
assert 'std::string videoLocation;' in src
assert 'ExtractJsonString(payload, "video_location")' in src
assert 'PragmaticBurnVideoWindowMatch' in src
assert 'PRAGMATIC_BURN_VIDEO_BINARY' in src
assert 'pragmaticBurnVideoBinaryCapturedByTable_' in src
assert 'count < 3' in src
assert "root.querySelectorAll('video')" in src
assert "toDataURL('image/jpeg',0.65)" in src
assert 'videoJpegBase64' in src and 'videoFrameError' in src

# Extract and syntax-check Multiplay JS expression with a synthetic target.
fn_start = src.index('    std::string PragmaticBurnMultiDomProbeScript(')
fn_end = src.index('    void MaybePragmaticBurnMultiDomProbe()', fn_start)
fn = src[fn_start:fn_end]
m = re.search(r'R"JS\((.*?)\)JS"', fn, re.S)
assert m, 'MULTIPLAY Burn DOM JS raw literal not found'
js = m.group(1).replace('__RUN__', 'test-run').replace(
    '__TARGETS__', '[{"tableid":"t1","name":"Baccarat 1"}]')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
    f.write(js + ';\n')
    js_path = f.name
subprocess.run(['node', '--check', js_path], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
Path(js_path).unlink(missing_ok=True)

# C) Safety gate: a virtualized/missing tile must never count as card
# disappearance. Repeated same card + zero cards on the STILL LOCATED tile is
# required before staging.
handler_start = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM__")')
handler_end = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM_ERROR__")', handler_start)
handler = src[handler_start:handler_end]
assert 'if (!rootFound) return;' in handler
assert 'st.pendingBurnDomConsensusSamples >= 2' in handler
assert 'eligibleCount == 0 && st.pendingBurnDomCommitted' in handler
assert 'PragmaticStageBurnDomConsensus' in handler
assert 'eligibleCount > 1 && st.pendingBurnDomCommitted' in handler
assert 'PRAGMATIC_BURN_MULTI_DOM_AMBIGUOUS' in handler
assert 'PragmaticStrategySubtractCard' not in handler

# Synthetic state checks including tile virtualization.
def sequence(obs):
    # obs: (root_found, card_count/single card) where None means no card.
    card = ''
    samples = 0
    committed = False
    staged = False
    ambiguous = False
    last_t = None
    t = 0
    for root_found, value in obs:
        t += 220
        if not root_found:
            # Native code returns immediately: virtualization is not disappearance.
            continue
        if value == 'MULTI':
            if committed and not staged:
                ambiguous = True
                committed = False
            if not staged:
                card = ''; samples = 0
            last_t = t
            continue
        if value is None:
            if committed and not staged and card:
                staged = True
            if not staged:
                card = ''; samples = 0
            last_t = t
            continue
        if staged:
            continue
        if card == value and last_t is not None and 0 <= t-last_t <= 1200:
            samples += 1
        else:
            card = value; samples = 1; committed = False
        last_t = t
        if samples >= 2 and not committed:
            committed = True
    return staged, ambiguous

assert sequence([(True,'KH'),(True,'KH'),(True,None)]) == (True, False)
assert sequence([(True,'KH'),(True,'KH'),(False,None)]) == (False, False)
assert sequence([(True,'KH'),(False,None),(True,'KH'),(True,None)]) == (True, False)
assert sequence([(True,'KH'),(True,'QH'),(True,None)]) == (False, False)
assert sequence([(True,'KH'),(True,'KH'),(True,'MULTI')]) == (False, True)

# D) First betsopen remains the only promotion boundary.
confirm_start = src.index('    void PragmaticConfirmPendingBurn(')
confirm_end = src.index('    void PragmaticStrategySubtractHand(', confirm_start)
confirm = src[confirm_start:confirm_end]
assert 'st.pendingBurnDistinctCandidates == 1' in confirm
assert '!st.pendingBurnAmbiguous' in confirm
assert confirm.count('PragmaticStrategySubtractCard(st, confirmedCard)') == 1

# E) Proven Edge math and Telegram settlement remain byte-identical to v98.
def extract_function(text, signature):
    i = text.index(signature)
    line_start = text.rfind('\n', 0, i) + 1
    prev_start = text.rfind('\n', 0, line_start - 1) + 1
    if text[prev_start:line_start].strip().startswith('std::optional'):
        i = prev_start
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

strategy = extract_function(src, 'PragmaticStrategyMath(const PragmaticTableRuntime& st) const')
assert hashlib.sha256(strategy.encode()).hexdigest() == 'a21cd3867249c33a87042c3b8b4e621f3716f4d2a9fba223d5404be158bc0579'
settlement = extract_function(src, 'QueueTelegramSignalSettlement(HWND hwnd')
assert hashlib.sha256(settlement.encode()).hexdigest() == '2726f2b51a6a0213761aa66bfcb120ff7e585489eb4b422f7f1be67bd55a3117'

print('v21.2.102 MULTIPLAY tile Burn Probe v3 + safety gates: OK')
