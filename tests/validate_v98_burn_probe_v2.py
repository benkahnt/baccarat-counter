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
assert 'Burn Probe v2' in readme

# A) Pre-first-hand diagnostic window must capture ALL table-specific text frames,
# even event types that remain noisy for ordinary diagnostics.
assert 'PragmaticBurnRawWindowMatch' in src
assert 'PragmaticArmBurnProbes' in src
assert 'pragmaticBurnRawProbeUntilByTable_' in src
assert 'PRAGMATIC_BURN_RAW_FRAME' in src
assert 'payloadChars' in src
assert 'cardinc' in src and 'timer' in src and 'dealer' in src
noisy_start = src.index('static bool PragmaticNoisyDiagnosticKey')
noisy_end = src.index('\n    }', noisy_start) + 6
noisy = src[noisy_start:noisy_end]
assert '"cardinc"' in noisy and '"timer"' in noisy and '"dealer"' in noisy
raw_pos = src.index('PRAGMATIC_BURN_RAW_FRAME')
parse_pos = src.index('HandlePragmaticPayload(safe)', raw_pos)
assert raw_pos < parse_pos

# B) Alternative protocol path may stage evidence, but never alter strategy directly.
alt_start = src.index('    void PragmaticMaybeStageAlternateBurnEvidence(')
alt_end = src.index('    void PragmaticStageBurnDomConsensus(', alt_start)
alt = src[alt_start:alt_end]
assert 'topKeyLower == "cardinc" && noGame && noNormalPlace' in alt
assert 'burnCard' in alt and 'burncard' in alt
assert 'PRAGMATIC_BURN_ALT_PROTOCOL_EVIDENCE' in alt
assert 'PragmaticStageBurnCandidate' in alt
assert 'PragmaticStrategySubtractCard' not in alt

# C) DOM probe: only primary Baccarat, high-frequency, exactly one rank+suit candidate.
assert 'PragmaticBurnDomProbeScript' in src
assert 'MaybePragmaticBurnDomProbe' in src
assert 'now - pragmaticBurnDomLastEvalTick_ < 220ULL' in src
assert '__BAC_PRAGMATIC_BURN_DOM__' in src
assert '#rank-' in src and '#suit-' in src
assert 'eligible.length===1?eligible[0].card' in src
assert 'SendCommand("Runtime.evaluate", params, primarySessions.front())' in src
# Mirror suppression: an identical console sample <100 ms must not build consensus.
assert 'nowTick - st.pendingBurnDomLastSampleTick < 100ULL' in src

# Extract raw JS literal, replace placeholders and syntax-check with Node.
fn_start = src.index('    std::string PragmaticBurnDomProbeScript(')
fn_end = src.index('    void MaybePragmaticBurnDomProbe()', fn_start)
fn = src[fn_start:fn_end]
m = re.search(r'R"JS\((.*?)\)JS"', fn, re.S)
assert m, 'Burn DOM JS raw literal not found'
js = m.group(1).replace('__RUN__', 'test-run').replace('__TABLE__', 'test-table')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
    # Runtime.evaluate accepts an expression; wrapping as a statement is syntax-valid.
    f.write(js + ';\n')
    js_path = f.name
subprocess.run(['node', '--check', js_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
Path(js_path).unlink(missing_ok=True)

# D) DOM evidence is deliberately temporal: repeated single card is not yet staged.
# It must subsequently disappear before first betsopen. Multiple cards invalidate it.
handler_start = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_DOM__")')
handler_end = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_DOM_ERROR__")', handler_start)
handler = src[handler_start:handler_end]
assert 'st.pendingBurnDomConsensusSamples >= 2' in handler
assert 'st.pendingBurnDomCommitted = true' in handler
assert 'eligibleCount == 0 && st.pendingBurnDomCommitted' in handler
assert 'PragmaticStageBurnDomConsensus' in handler
assert 'eligibleCount > 1 && st.pendingBurnDomCommitted' in handler
assert 'PRAGMATIC_BURN_DOM_AMBIGUOUS' in handler

# Synthetic temporal state machine checks: only repeat -> disappear qualifies.
def dom_sequence(seq):
    card = ''
    samples = 0
    committed = False
    staged = False
    ambiguous = False
    last_t = None
    t = 0
    for obs in seq:
        t += 220
        if obs == 'MULTI':
            if committed and not staged:
                ambiguous = True
                committed = False
            if not staged:
                card = ''; samples = 0
            last_t = t
            continue
        if obs is None:
            if committed and not staged and card:
                staged = True
            if not staged:
                card = ''; samples = 0
            last_t = t
            continue
        if staged:
            continue
        if card == obs and last_t is not None and 0 <= t-last_t <= 1200:
            samples += 1
        else:
            card = obs; samples = 1; committed = False
        last_t = t
        if samples >= 2 and not committed:
            committed = True
    return staged, ambiguous

assert dom_sequence(['KH', 'KH', None]) == (True, False)
assert dom_sequence(['KH', None]) == (False, False)
assert dom_sequence(['KH', 'QH', None]) == (False, False)
assert dom_sequence(['KH', 'KH', 'MULTI']) == (False, True)
assert dom_sequence(['KH', 'KH', 'KH'])[0] is False

# E) First betsopen remains the single promotion boundary. No staging helper may
# subtract a rank; only final confirmation can do that.
dom_stage_start = src.index('    void PragmaticStageBurnDomConsensus(')
dom_stage_end = src.index('    void PragmaticConfirmPendingBurn(', dom_stage_start)
dom_stage = src[dom_stage_start:dom_stage_end]
assert 'PragmaticStrategySubtractCard' not in dom_stage
confirm_start = src.index('    void PragmaticConfirmPendingBurn(')
confirm_end = src.index('    void PragmaticStrategySubtractHand(', confirm_start)
confirm = src[confirm_start:confirm_end]
assert 'st.pendingBurnDistinctCandidates == 1' in confirm
assert '!st.pendingBurnAmbiguous' in confirm
assert confirm.count('PragmaticStrategySubtractCard(st, confirmedCard)') == 1
bets_start = src.index('        if (PragmaticTopKey(payload, "betsopen")) {')
bets_end = src.index('        if (PragmaticTopKey(payload, "betsclosed")) {', bets_start)
bets = src[bets_start:bets_end]
assert bets.index('PragmaticConfirmPendingBurn') < bets.index('st.awaitingFirstGame = false;')

# F) Proven strategy math and Telegram settlement remain byte-identical.
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

print('v21.2.102 exhaustive burn raw-frame + temporal DOM consensus probe: OK')
