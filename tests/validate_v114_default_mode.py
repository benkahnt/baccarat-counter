"""Verify the startup/Reset UI contract and existing Tie signal rendering."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root / 'src/main.cpp').read_text(encoding='utf-8-sig')
build = (root / 'build.bat').read_text(encoding='utf-8')
assert 'BaccaratCounterV123.exe' in build
assert 'static std::atomic<int>  gPragmaticAutoBetMode{2};' in src

startup = src[src.index('a->pragmaticAutoBetBtn = CreateWindowW('):
              src.index('const bool combinedFilter = LoadCombinedEvFilterEnabled();')]
assert 'L"BUTTON", L"Auto-Bet Pair: KLICK"' in startup
assert 'SendMessageW(a->pragmaticAutoBetBtn, BM_SETCHECK, BST_CHECKED, 0)' in startup

reset = src[src.index('static void ResetSessionData('):
            src.index('static std::wstring FormatStrategyPercent(')]
assert 'gPragmaticAutoBetMode.store(' not in reset
assert 'SetWindowTextW(a->pragmaticAutoBetBtn' not in reset
assert 'gSessionPnlUnits.store(0' in reset  # Reset still resets accounting.

mode = src[src.index('case 128: {'):src.index('case 128: {')+3200]
assert 'mode = (mode + 1) % 3;' in mode
assert 'L"Auto-Bet Pair: AUS"' in mode
assert 'L"Auto-Bet Pair: Paper"' in mode
assert 'L"Auto-Bet Pair: KLICK"' in mode

focus = src[src.index('case 113: {'):src.index('case 119: {')]
assert 'gPragmaticAutoBetMode.store(0' in focus  # Tischfokus AUS remains a safety interlock.

assert 'if(!/Sitzung\\s+wird\\s+gleich\\s+beendet/i.test(pageText))return;' in src
assert "if(label!=='Weiterspielen')return false;" in src
assert 'gPragmaticSessionKeepAlive' not in src
assert 'keepAliveCheck' not in src
assert 'Auto Weiterspielen' not in src
assert 'const bool keepAliveEnabled =\n            !pragmaticMultiplayConflict_' in src

telegram = src[src.index('if (complete && st.telegramSignalPending &&'):
               src.index('PRAGMATIC_TELEGRAM_SIGNAL_SETTLEMENT',
                         src.index('if (complete && st.telegramSignalPending &&'))]
assert 'telegram += L"\\nHauptwette ";' in telegram
assert 'st.telegramSignalMainSide' in telegram
assert 'st.telegramSignalMainSide == "Tie" && result == "tie"' in telegram
assert 'telegram += L"\\nHauptwette (Paper): "' in telegram

print('PASS startup KLICK, Reset keeps manual choice, Tischfokus interlock, exact keepalive warning, Tie in Telegram')
