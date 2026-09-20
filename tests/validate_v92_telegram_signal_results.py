from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root / 'src/main.cpp').read_text(encoding='utf-8')
build = (root / 'build.bat').read_text(encoding='utf-8', errors='replace')
setup = (root / 'TELEGRAM_SETUP.md').read_text(encoding='utf-8')
ini = (root / 'BaccaratCounter.ini.example').read_text(encoding='utf-8')

# v92 package/build identity.
assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'Baccarat Counter v21.2.123' in src
assert 'BaccaratCounterV123.exe' in setup

# Old manual Telegram test button/path is removed.
assert 'QueueTelegramTest' not in src
assert 'TelegramTestResult' not in src
assert 'WM_APP_TELEGRAM_TEST_RESULT' not in src
assert 'L"Telegram testen"' not in src

# New persisted ON/OFF signal-result switch.
assert 'gTelegramSignalEnabled{false}' in src
assert 'LoadTelegramSignalEnabled()' in src
assert 'SaveTelegramSignalEnabled(bool enabled)' in src
assert 'L"SignalEnabled"' in src
assert 'SignalEnabled=0' in ini
assert 'HWND telegramSignalBtn{};' in src
assert 'L"Telegram-Signal: OFF"' in src
assert 'L"Telegram-Signal: ON"' in src
assert 'BS_AUTOCHECKBOX | BS_PUSHLIKE' in src
assert 'case 135:' in src
assert 'SaveTelegramSignalEnabled(enabled);' in src

# Signal results are gated by the dedicated button state and use the existing async sender.
helper_start = src.index('static void QueueTelegramSignalResult')
helper_end = src.index('static std::optional<std::string> ExtractJsonString', helper_start)
helper = src[helper_start:helper_end]
assert 'gTelegramSignalEnabled.load' in helper
assert 'QueueTelegramMessage(hwnd, message, true);' in helper
assert 'if (!cfg.enabled || cfg.botToken.empty())' in src  # Telegram master switch remains intact.

# Pragmatic result push is tied to the emitted SETZEN signal itself, not a confirmed click.
assert 'bool telegramSignalPending{false};' in src
assert 'std::string telegramSignalSourceGameId;' in src
assert 'std::string telegramSignalTargetGameId;' in src
count_start = src.index('void PragmaticCountValidSetzenSignal')
count_end = src.index('void PragmaticRollbackPendingSetzenSignalForShoeEnd', count_start)
count = src[count_start:count_end]
assert 'st.telegramSignalPending = true;' in count
assert 'reason == "hand-complete"' in count
assert 'st.telegramSignalTargetGameId = sourceGameId;' in count

bets_start = src.index('if (PragmaticTopKey(payload, "betsopen"))')
bets_end = src.index('if (PragmaticTopKey(payload, "timer"))', bets_start)
bets = src[bets_start:bets_end]
assert 'st.telegramSignalTargetGameId = *gameId;' in bets

prag_start = src.index('if (PragmaticTopKey(payload, "gameresult"))')
prag_end = src.index('if (PragmaticTopKey(payload, "startshuffling"))', prag_start)
prag = src[prag_start:prag_end]
assert 'st.lastCompletedGameId == *gameId' in prag
assert 'st.telegramSignalTargetGameId == *gameId' in prag
assert 'const bool signalWon = handPnlHundredths > 0;' in prag
assert 'L"✅ Telegram-Signal: GEWINN"' in prag
assert 'L"❌ Telegram-Signal: VERLUST"' in prag
assert 'QueueTelegramSignalSettlement(' in prag
assert prag.index('st.lastCompletedGameId == *gameId') < prag.index('QueueTelegramSignalSettlement(')

# Evolution transport also binds the signal to the following completed hand.
assert 'EvolutionTelegramSignalState' in src
assert 'evolutionTelegramSignals_' in src
assert 'EVOLUTION_TELEGRAM_SIGNAL_SETTLEMENT' in src
assert 'provider_ == ProviderMode::Evolution' in src

# Existing target/stoploss Telegram paths remain independent from SignalEnabled.
for message in ('Unit-Ziel erreicht', 'Stoploss-Vorwarnung', 'Stoploss erreicht'):
    assert message in src
assert 'Unit-Ziel/Stoploss bleiben unabhängig davon.' in src

print('v21.2.92 Telegram signal result ON/OFF: OK')
