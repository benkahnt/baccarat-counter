from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root / 'src/main.cpp').read_text(encoding='utf-8')
build = (root / 'build.bat').read_text(encoding='utf-8', errors='replace')
setup = (root / 'TELEGRAM_SETUP.md').read_text(encoding='utf-8')

# Visible UI button and command wiring.
assert 'HWND telegramTestBtn{};' in src
assert 'L"BUTTON", L"Telegram testen"' in src
assert '(HMENU)135' in src
assert 'moveCell(a->telegramTestBtn, row[5]);' in src
assert 'case 135:' in src
assert 'QueueTelegramTest(hwnd)' in src
assert 'L"Telegram-Test läuft..."' in src

# Test is asynchronous and guarded against duplicate clicks.
assert 'gTelegramTestInFlight{false}' in src
assert 'compare_exchange_strong' in src
assert 'static bool QueueTelegramTest(HWND hwnd)' in src
telegram_test = src[src.index('static bool QueueTelegramTest(HWND hwnd)'):src.index('static std::optional<std::string> ExtractJsonString', src.index('static bool QueueTelegramTest(HWND hwnd)'))]
assert 'std::thread([hwnd]' in telegram_test
assert '}).detach();' in telegram_test

# Token, chat-id resolution and real send are all exercised by the manual test.
assert 'L"getMe", "{}"' in telegram_test
assert 'ResolveTelegramChatId(cfg)' in telegram_test
assert 'L"sendMessage"' in telegram_test
assert 'Telegram-Test erfolgreich' in telegram_test
assert 'cfg.enabled' in telegram_test  # only used for the final explanatory text
assert 'if (!cfg.enabled || cfg.botToken.empty())' in src  # automatic alarms still require Enabled=1

# UI receives a concrete result and restores the button.
assert 'WM_APP_TELEGRAM_TEST_RESULT' in src
assert 'struct TelegramTestResult' in src
assert 'case WM_APP_TELEGRAM_TEST_RESULT:' in src
assert 'MessageBoxW(hwnd, u->detail.c_str()' in src
assert 'SetWindowTextW(a->telegramTestBtn, L"Telegram testen")' in src

# Existing automatic target/stoploss pushes remain present.
for message in ('Unit-Ziel erreicht', 'Stoploss-Vorwarnung', 'Stoploss erreicht'):
    assert message in src

# v91 package/build identity and documentation.
assert 'BaccaratCounterV91.exe' in build
assert 'v21.2.91' in build
assert 'Baccarat Counter v21.2.91' in src
assert 'BaccaratCounterV91.exe' in setup
assert 'manuelle Test funktioniert auch bei `Enabled=0`' in setup
print('v21.2.91 Telegram test button + existing Telegram alarms: OK')
