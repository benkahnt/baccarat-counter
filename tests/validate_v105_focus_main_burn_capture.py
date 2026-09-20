from pathlib import Path
import hashlib
import subprocess

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

# A) Main-screen Baccarat may omit chip_amounts in the mirrored runtime.
# Only the explicit 0.20-EUR Pair amount may pass through to live UI
# verification; all other composition failures remain hard failures.
plan_start = src.index('static PragmaticStakePlan PragmaticBuildStakePlan(')
plan_end = src.index('auto tier = PragmaticActivePairLimit(st);', plan_start)
plan = src[plan_start:plan_end]
for token in [
    'if (plan.pairChipCents == 20 && st.chipAmountsCents.empty())',
    'plan.pairChipDenomCents = 20;',
    'plan.pairChipClicks = 1;',
    'plan.reason = "pair-amount-composition-unavailable";',
]:
    assert token in plan, token

# B) Queue latency: the visible main table receives priority and Pair-only
# readiness can no longer block later signals for nine seconds.
queue_start = src.index('void PragmaticQueueAutoBet(')
queue_end = src.index('void PragmaticFinishActiveAutoBet', queue_start)
queue = src[queue_start:queue_end]
assert 'const bool preferMainTable' in queue
assert 'pragmaticMainTableIds_.find(tableId)' in queue
assert 'pragmaticAutoBetQueue_.push_front' in queue
assert 'pragmaticAutoBetQueue_.push_back' in queue
assert 'mainTablePriority' in queue

focus_start = src.index('void PragmaticFocusSignalTable')
focus = src[focus_start:]
assert 'operation.deadline=Math.min(operation.hardDeadline,now+budget)' in focus
assert 'uiWaitDeadline:Date.now()+20000' in focus
assert "finishRetry('readiness-window-expired')" in focus
assert 'nine-second-readiness-window-expired' not in focus
assert '>= 32000ULL' in src

# C) Chip controls are searched across the active game document, launcher
# portal and accessible Baccarat/MTB iframes. Coordinates are translated from
# the control's own window to the launcher root.
for token in [
    'const chipDocuments=(contextEl=null)=>',
    'const walk=(doc,depth=0)=>',
    'if(!doc||depth>5)return;',
    'walk(contextEl&&contextEl.ownerDocument,0)',
    'walk(document,0)',
    'walk(ROOT_DOCUMENT,0)',
    r"/\/desktop\/(?:launcher|(?:multi)?baccarat)\//i.test(u)",
    'for(const doc of chipDocuments(contextEl))',
    'for(const doc of chipDocuments(currentTable))',
    'const toRootViewportPoint=(x,y,startWindow=null)=>',
    'el.ownerDocument.defaultView',
    'chipRackDiag:lastChipRackDiag',
]:
    assert token in focus, token

# Pair fields remain gated behind explicit denomination verification.
verify_pos = focus.index('pairChipSelectionConfirmed')
stake_ready_pos = focus.index('operation.stakePrepared=true;', verify_pos)
pair_coords_pos = focus.index('__BAC_PAIR_CLICK_COORDS__', stake_ready_pos)
assert verify_pos < stake_ready_pos < pair_coords_pos
assert "finishRetry('pair-chip-selection-unconfirmed')" in focus

# D) Burn capture is sent through a top-level page CDP session. Main-table
# and MULTIPLAY screenshots use the whole visible viewport without a CDP clip;
# tile coordinates are metadata only and both paths stay diagnostic-only.
helper_start = src.index('std::string PragmaticTopLevelPageSession()')
helper_end = src.index('void HandlePragmaticBurnScreenshotResponse(', helper_start)
helper = src[helper_start:helper_end]
for token in [
    'PragmaticRequestTopLevelBurnScreenshot(',
    'const std::string pageSession = PragmaticTopLevelPageSession();',
    'SendCommandChecked("Page.captureScreenshot", params, pageSession, requestId)',
    'top-level-page-session-missing',
]:
    assert token in helper, token
assert 'PragmaticStrategySubtractCard' not in helper
assert r'\"captureBeyondViewport\":false' in helper
assert r'\"clip\"' not in helper
assert 'requested-tile-metadata-only' in helper
assert 'pragmaticBurnScreenshotRequests_.empty()' in helper
assert 'now - entry.second.requestedTick >= 30000' in helper

main_burn_start = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_DOM__")')
main_burn_end = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM__")', main_burn_start)
main_burn = src[main_burn_start:main_burn_end]
assert 'probeSample == 1 || probeSample == 5' in main_burn
assert 'probeSample == 10 || probeSample == 15' in main_burn
assert '"main-baccarat-viewport"' in main_burn
assert 'true,' in main_burn
assert 'PragmaticStrategySubtractCard' not in main_burn

multi_burn_start = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM__")')
multi_burn_end = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_BURN_MULTI_DOM_ERROR__")', multi_burn_start)
multi_burn = src[multi_burn_start:multi_burn_end]
assert 'rootInViewport' in multi_burn
assert '"multiplay-visible-tile"' in multi_burn
assert 'PragmaticRequestTopLevelBurnScreenshot(' in multi_burn
assert 'PragmaticStrategySubtractCard' not in multi_burn

# Main-screen video receives a longer contiguous diagnostic capture, while
# other tables retain the small diagnostic budget.
assert 'const int maxFrames =' in src
assert 'pragmaticMainTableIds_.find(burnVideoTableId)' in src
assert '? 24 : 3;' in src
assert 'if (count < maxFrames)' in src

# Strategy can still consume a Burn card only through the unique-candidate gate.
confirm_start = src.index('void PragmaticConfirmPendingBurn(')
confirm_end = src.index('void PragmaticStrategySubtractHand(', confirm_start)
confirm = src[confirm_start:confirm_end]
assert 'st.pendingBurnDistinctCandidates == 1' in confirm
assert '!st.pendingBurnAmbiguous' in confirm
assert confirm.count('PragmaticStrategySubtractCard(st, confirmedCard)') == 1

# E) Embedded focus/Balance JavaScript still parses.
subprocess.run([__import__('sys').executable, str(ROOT / 'tests' / 'validate_focus_js.py')], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
subprocess.run([__import__('sys').executable, str(ROOT / 'tests' / 'validate_balance_js.py')], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# F) Sensitive mathematical and settlement/click transports remain unchanged.
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
    actual = hashlib.sha256(body.encode()).hexdigest()
    assert actual == expected, (signature, actual)

# v103 Excel logical-session de-duplication stays present.
subprocess.run([__import__('sys').executable, str(ROOT / 'tests' / 'validate_v103_session_excel_dedupe.py')], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print('v21.2.105 focus/main-screen stake + top-level Burn capture: OK')
