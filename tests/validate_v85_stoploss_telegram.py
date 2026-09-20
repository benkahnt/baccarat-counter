from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root / 'src/main.cpp').read_text(encoding='utf-8')
build = (root / 'build.bat').read_text(encoding='utf-8', errors='replace')

# UI + persisted settings.
assert 'HWND stopLossLabel{};' in src
assert 'HWND stopLossEdit{};' in src
assert 'L"STATIC", L"Stoploss:"' in src
assert 'gStopLossUnits{-50}' in src
assert 'L"Strategy", L"StopLoss", L"-50"' in src
assert 'StopLossWarningUnits' in src
assert 'NormalizeStopLossUnits(stopLossUnits) + 10' in src
assert 'moveLabeledCell(a->stopLossLabel, a->stopLossEdit' in src

# Limits are evaluated on completed results and suppress further signalling.
assert 'MaybeSendStopLossWarning(sessionPnlHundredths);' in src
assert 'sessionPnlHundredths <= stopLossUnits * 100' in src
assert 'ArmStopLossStop(' in src
assert 'WM_APP_STOP_LOSS_REACHED' in src
assert 'STOP_LOSS_REACHED' in src
assert 'STOP_LOSS_WARNING' in src
assert src.count('!gStopLossReached.load(std::memory_order_acquire)') >= 4

# Telegram stays local/configurable, asynchronous and token is never hard-coded.
assert 'L"Telegram", L"Enabled", L"0"' in src
assert 'L"Telegram", L"BotToken", L""' in src
assert 'L"Telegram", L"ChatId", L""' in src
assert 'api.telegram.org' in src
assert 'ResolveTelegramChatId' in src
assert 'getUpdates' in src
assert 'sendMessage' in src
assert 'QueueTelegramMessage' in src
assert '}).detach();' in src
assert 'Unit-Ziel erreicht' in src
assert 'Stoploss-Vorwarnung' in src
assert 'Stoploss erreicht' in src

# Proven Pragmatic click path and v84 all-tables code stay present.
pair_start = src.index('    void HandlePragmaticTrustedPairClickResponse(')
pair_end = src.index('    void Bootstrap()', pair_start)
pair = src[pair_start:pair_end]
assert 'const std::string& inputSessionId = pending.sessionId;' in pair
assert 'foregrounded-embedded-pragmatic' in pair
assert 'foregrounded-betify-page' not in pair
assert 'launcher-root-viewport' in src

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
print('v21.2.85 Stoploss + Telegram + existing Pragmatic click regressions: OK')
