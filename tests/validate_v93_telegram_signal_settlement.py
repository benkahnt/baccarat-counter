from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root / 'src/main.cpp').read_text(encoding='utf-8')
build = (root / 'build.bat').read_text(encoding='utf-8', errors='replace')
setup = (root / 'TELEGRAM_SETUP.md').read_text(encoding='utf-8')
readme = (root / 'README.md').read_text(encoding='utf-8')
ini = (root / 'BaccaratCounter.ini.example').read_text(encoding='utf-8')

# Release identity.
assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'Baccarat Counter v21.2.123' in src
assert 'BaccaratCounterV123.exe' in setup
assert 'Baccarat Counter v21.2.123' in readme

# The manual test button remains removed; the persisted signal gate remains.
assert 'L"Telegram testen"' not in src
assert 'gTelegramSignalEnabled{false}' in src
assert 'SignalEnabled=0' in ini
assert 'L"Telegram-Signal: OFF"' in src
assert 'L"Telegram-Signal: ON"' in src
assert 'SaveTelegramSignalEnabled(enabled);' in src

# Post-result sender waits for a newer balance observation and appends the current balance.
helper_start = src.index('static void QueueTelegramSignalSettlement')
helper_end = src.index('static std::optional<std::string> ExtractJsonString', helper_start)
helper = src[helper_start:helper_end]
assert 'seq > balanceSequenceAtResult' in helper
assert 'std::this_thread::sleep_for(std::chrono::milliseconds(100))' in helper
assert 'Kontostand: ' in helper
assert 'gLatestObservedBalanceMinor.load' in helper
assert 'QueueTelegramSignalResult(hwnd, message);' in helper
assert 'gTelegramSignalEnabled.load' in helper
assert 'Zuletzt abgelesener Kontostand:' in helper
assert 'Kein bestätigter Abschlusssaldo' in helper
assert 'gLatestObservedBalanceTick.load' in helper

# Signal tracking retains the target hand and exact placement facts until settlement.
for token in (
    'int telegramSignalPairChipCents{0};',
    'int telegramSignalPairChipDenomCents{0};',
    'int telegramSignalPairChipClicks{0};',
    'int telegramSignalConfirmedPairMask{0};',
    'bool telegramSignalMainRequired{false};',
    'int telegramSignalMainPlannedCents{0};',
    'int telegramSignalMainAcceptedCents{0};',
    'int telegramSignalMainStakeUnitsX100{0};',
):
    assert token in src

finalize_start = src.index('void PragmaticFinalizePlacementAccounting')
finalize_end = src.index('void PragmaticStartNextQueuedAutoBet', finalize_start)
finalize = src[finalize_start:finalize_end]
assert 'st.telegramSignalConfirmedPairMask = pairMask;' in finalize
assert 'st.telegramSignalPairChipCents = st.pendingStakePlan.pairChipCents;' in finalize

stake_confirm_start = src.index('if (auto value = extractConsoleValue("__BAC_STAKE_PREP_CONFIRM__"))')
stake_confirm_end = src.index('if (auto value = extractConsoleValue("__BAC_STAKE_PREP_ERROR__"))', stake_confirm_start)
stake_confirm = src[stake_confirm_start:stake_confirm_end]
assert 'st.telegramSignalMainAcceptedCents = mainAcceptedCents;' in stake_confirm
assert 'st.telegramSignalMainStakeUnitsX100 =' in stake_confirm

# Pragmatic settlement occurs only from the completed, deduplicated result path.
prag_start = src.index('if (PragmaticTopKey(payload, "gameresult"))')
prag_end = src.index('if (PragmaticTopKey(payload, "startshuffling"))', prag_start)
prag = src[prag_start:prag_end]
assert 'st.lastCompletedGameId == *gameId' in prag
assert 'complete && st.telegramSignalPending' in prag
assert 'st.telegramSignalTargetGameId == *gameId' in prag
assert prag.index('st.lastCompletedGameId == *gameId') < prag.index('QueueTelegramSignalSettlement(')

# Message contains hand winner, each Pair result, exact placements and P/L.
for token in (
    'L"\\nHand: PLAYER gewonnen"',
    'L"\\nHand: BANKER gewonnen"',
    'L"\\nHand: TIE / Unentschieden"',
    'L"\\nPlayer Pair: GEWONNEN ✅"',
    'L"\\nBanker Pair: GEWONNEN ✅"',
    'L"\\n\\nChips erfolgreich platziert: "',
    'L"Player Pair gesetzt"',
    'L"Banker Pair gesetzt"',
    'L"\\nHand-P/L (tatsächlich): "',
    'L"\\nSession-P/L (Ist, bestätigt): "',
    'L"\\nSession-P/L (Paper): "',
    'L"\\nHand-P/L (Paper, inkl. Hauptwette): "',
):
    assert token in prag
assert 'FormatTelegramStakeCents(totalPlacedCents, currencyCode)' in prag
assert 'st.telegramSignalPairChipClicks' in prag
assert 'st.telegramSignalPairChipDenomCents' in prag
assert 'L"Telegram-Signal: NICHT PLATZIERT"' in prag
assert 'totalPlacedCents == 0' in prag
assert 'L"Telegram-Signal: AUSGEGLICHEN"' in prag
assert 'if (signalPaperPnlHundredths)' in prag
assert 'FormatUnitHundredths(*signalPaperPnlHundredths)' in prag
assert 'L"\\nHauptwette (Paper): "' in prag

# Actual click-mode P/L uses only confirmed Pair sides plus accepted main wager.
assert 'confirmed_bet_accounting::RoundPnlUnits(' in prag
assert 'st.telegramSignalConfirmedPairMask' in prag
assert 'st.telegramSignalMainAcceptedCents > 0' in prag
assert 'confirmed_bet_accounting::MainNetHundredths(' in prag
accounting = (root/'src/confirmed_bet_accounting.h').read_text(encoding='utf8')
assert 'stakeUnitsHundredths * 0.95' in accounting  # Banker commission.
assert '8 * stakeUnitsHundredths' in accounting  # Tie 8:1 net, not a push.
assert 'result == "tie" && st.telegramSignalMainSide != "Tie"' in prag
assert 'const int handPnlHundredths =' in prag

# Main placement line reports accepted amount and whether that Player/Banker bet won/lost/pushed.
assert 'L" – PUSH"' in prag
assert 'L" – GEWONNEN ✅"' in prag
assert 'L" – verloren ❌"' in prag
assert 'st.telegramSignalMainAcceptedCents !=' in prag
assert 'L" (geplant "' in prag

# Evolution still waits for the completed following hand and is explicit about unavailable real-chip confirmation.
evo_start = src.index('if (auto value = extractConsoleValue("__BAC_TRANSPORT_HAND_COMPLETE__"))')
evo_end = src.index('if (auto value = extractConsoleValue("__BAC_TRANSPORT_HAND_INCOMPLETE__"))', evo_start)
evo = src[evo_start:evo_end]
assert 'EVOLUTION_TELEGRAM_SIGNAL_SETTLEMENT' in evo
assert 'ExtractJsonString(payload, "winner")' in evo
assert 'Player Pair: GEWONNEN' in evo
assert 'Banker Pair: GEWONNEN' in evo
assert 'Chips erfolgreich platziert: nicht bestätigt (Evolution)' in evo
assert 'QueueTelegramSignalSettlement(' in evo

# Documentation covers the new semantics.
for phrase in (
    'Hand-P/L (tatsächlich)',
    'Player Pair',
    'Banker Pair',
    'Kontostand',
    'tatsächlich akzeptiertem Betrag',
):
    assert phrase in setup

print('v21.2.94 Telegram post-hand settlement summary: OK')

# Replay the audited stale-balance timing using the actual formatting/worker.
# No network, file writes or real Telegram calls are made by this harness.
from test_toolchain import compile_cpp, temporary_directory
import subprocess
code = r'''
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <functional>
#include <iomanip>
#include <sstream>
#include <string>
using ULONGLONG=unsigned long long;
using HWND=int;
static ULONGLONG clockTick=10000;
static ULONGLONG GetTickCount64(){return clockTick;}
namespace std {class thread {function<void()> work;public:template<class F>thread(F f):work(f){}void detach(){work();}};
namespace this_thread {static void sleep_for(chrono::milliseconds d){clockTick+=d.count();}};}
static std::atomic<bool> gTelegramSignalEnabled{true};
static std::atomic<std::uint64_t> gLatestObservedBalanceSequence{1};
static std::atomic<std::int64_t> gLatestObservedBalanceMinor{18315};
static std::atomic<int> gLatestObservedBalanceCurrencyCode{1};
static std::atomic<ULONGLONG> gLatestObservedBalanceTick{7000};
static std::wstring delivered;
static void QueueTelegramSignalResult(HWND,const std::wstring& s){delivered=s;}
''' + src[src.index('static std::wstring TelegramCurrencyLabel'):helper_end] + r'''
int main(){
 QueueTelegramSignalSettlement(0,L"Hand-P/L: +2,75 Units",1);
 assert(delivered.find(L"183,15 EUR")!=std::wstring::npos);
 assert(delivered.find(L"Zuletzt abgelesener Kontostand")!=std::wstring::npos);
 assert(delivered.find(L"vor 7 s")!=std::wstring::npos);
 assert(delivered.find(L"Kein bestätigter Abschlusssaldo")!=std::wstring::npos);
 gLatestObservedBalanceMinor=18510;gLatestObservedBalanceSequence=2;gLatestObservedBalanceTick=clockTick;
 QueueTelegramSignalSettlement(0,L"Hand-P/L: +2,75 Units",1);
 assert(delivered.find(L"185,10 EUR")!=std::wstring::npos);
 assert(delivered.find(L"vor 0 s")!=std::wstring::npos);
 delivered.clear();gTelegramSignalEnabled=false;QueueTelegramSignalSettlement(0,L"OFF",2);assert(delivered.empty());
}
'''
with temporary_directory() as directory:
    p=Path(directory)/'telegram_balance.cpp'; p.write_text(code,encoding='utf-8')
    exe=compile_cpp(p,Path(directory)/'telegram_balance',[root/'src'])
    subprocess.run([str(exe)],check=True,timeout=20)
print('v123 stale/fresh balance snapshots remain labelled; Telegram OFF stays silent: OK')
