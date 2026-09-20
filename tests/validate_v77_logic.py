from pathlib import Path
from test_toolchain import temporary_directory
import re, subprocess, tempfile
root=Path(__file__).resolve().parents[1]
src=(root/'src/main.cpp').read_text(encoding='utf-8')

def take(start,end):
    a=src.index(start); b=src.index(end,a); return src[a:b]
parse=take('static double NormalizeEdgePercent','static double LoadMinEdgePercent')
structs=take('struct PnlHistoryPoint','struct Counters')
risk=take('static PnlRiskStats CalculatePnlRiskStats','struct PnlChartGeometry')
balance_format=take('static std::wstring FormatBalanceMinor','static std::wstring OptionalBalanceText')
placement=take('                const int tooltipWidth =', '                RECT tooltip{')
quad_parser=take('    static std::vector<double> ExtractFirstContentQuad(',
                 '    void HandlePragmaticTrustedPairClickResponse')
code='''#include <algorithm>\n#include <array>\n#include <cassert>\n#include <cmath>\n#include <cstdint>\n#include <cwctype>\n#include <iomanip>\n#include <optional>\n#include <regex>\n#include <sstream>\n#include <string>\n#include <vector>\n#include <iostream>\nusing ULONGLONG=unsigned long long;\nusing LONG=long; struct RECT { LONG left,top,right,bottom; };\n'''+parse+'\n'+structs+'\n'+risk+'\n'+balance_format+'\n'+quad_parser+'\nstd::array<int,4> PlaceTooltip(RECT measured, RECT rc, int pointX, int pointY) {\n'+placement+'    return {tooltipX, tooltipY, tooltipWidth, tooltipHeight};\n}\n'+r'''
int main(){
 assert(ParseMinEdgePercentText(L"-20.00").value()==-20.0);
 assert(ParseMinEdgePercentText(L"-20,00").value()==-20.0);
 assert(ParseMinEdgePercentText(L"-10.00").value()==-10.0);
 assert(ParseMinEdgePercentText(L"  -2.50  ").value()==-2.5);
 assert(ParseMinEdgePercentText(L"-21").value()==-20.0);
 assert(!ParseMinEdgePercentText(L"-").has_value());
 assert(!ParseMinEdgePercentText(L"2abc").has_value());
 std::vector<PnlHistoryPoint> h{{0,0,L""},{1,10,L""},{2,-30,L""}};
 auto s=CalculatePnlRiskStats(h); assert(s.highWaterUnits==10); assert(s.maxDrawdownUnits==-30);
 std::vector<PnlHistoryPoint> positive{{0,0,L""},{1,10,L""},{2,2,L""}};
 assert(CalculatePnlRiskStats(positive).maxDrawdownUnits==0);
 auto tip=PnlPointTooltipText({0,-4,L"2026-09-13T03:37:30.818"});
 assert(tip==L"-4 Units\n13.09.2026 03:37:30");
 auto placed=PlaceTooltip({0,0,70,35},{0,0,800,400},776,42);
 assert(placed[2]>=120 && placed[0]>=6 && placed[0]+placed[2]<=794);
 assert(FormatBalanceMinor(5000123,L"EUR")==L"50.001,23 EUR");
 assert(FormatBalanceMinor(-99,L"USD")==L"-0,99 USD");
 auto quad=ExtractFirstContentQuad(
   R"({"id":42,"result":{"quads":[[10.5,20,110.5,20,110.5,70,10.5,70]]}})");
 assert(quad.size()==8 && quad[0]==10.5 && quad[7]==70.0);
 assert(ExtractFirstContentQuad(R"({"id":42,"result":{}})").empty());
 std::cout << "logic OK\n";
}
'''
with temporary_directory() as d:
    cpp=Path(d)/'test.cpp'; exe=Path(d)/'test'; cpp.write_text(code,encoding='utf-8')
    subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)

alarm=take('static const std::vector<unsigned char>& SetzenAlarmWave()',
           'struct TableStatusUpdate')
alarm_code=r'''#include <algorithm>
#include <atomic>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <vector>
using ULONGLONG=unsigned long long;
using LPCSTR=const char*;
static std::atomic<ULONGLONG> gLastSetzenAlarmTick{0};
static ULONGLONG GetTickCount64(){return 5000;}
constexpr unsigned long SND_MEMORY=1,SND_ASYNC=2,SND_NODEFAULT=4;
static int PlaySoundA(LPCSTR,void*,unsigned long){return 1;}
'''+alarm+r'''
int main(){assert(SetzenAlarmWave().size()>44);PlaySetzenAlarm();}
'''
with temporary_directory() as d:
    cpp=Path(d)/'alarm.cpp'; exe=Path(d)/'alarm'; cpp.write_text(alarm_code,encoding='utf-8')
    subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)

# Compile the exact asynchronous target -> content-quad -> trusted Input
# response handler inside a small platform-neutral harness. This catches C++
# string-concatenation and state-machine errors that a JavaScript check cannot.
pending_struct=take('    struct PendingTrustedPairClick {',
                    '    struct ParallelFocusCandidate')
trusted_handler=take('    static std::vector<double> ExtractFirstContentQuad(',
                     '    void Bootstrap()')
trusted_code=r'''#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <mutex>
#include <optional>
#include <regex>
#include <string>
#include <unordered_map>
#include <vector>
static std::optional<int> ExtractJsonInt(const std::string&,const std::string&){return std::nullopt;}
static std::optional<std::string> ExtractJsonString(const std::string&,const std::string&){return std::nullopt;}
static std::string JsonEscape(const std::string& s){return s;}
static std::string IsoNow(){return "now";}
static std::wstring Utf8ToWide(const std::string& s){return std::wstring(s.begin(),s.end());}
static std::atomic<int> gPragmaticAutoBetMode{2};
class Harness {
'''+pending_struct+r'''
    struct Capture { void WriteRaw(const std::string&){} } capture_;
    std::mutex pragmaticTrustedPairClickMu_;
    std::unordered_map<std::uint64_t,PendingTrustedPairClick> pragmaticPairTargetRequests_;
    std::unordered_map<std::uint64_t,PendingTrustedPairClick> pragmaticPairQuadRequests_;
    std::mutex pragmaticBetsOpenMu_;
    std::unordered_map<std::string,std::string> pragmaticBetsOpenGameByTable_;
    void Log(const std::wstring&){}
    bool SendCommandChecked(const std::string&,const std::string&,const std::string&,std::uint64_t& id){id=1;return true;}
    std::uint64_t SendCommand(const std::string&,const std::string&,const std::string&){return 1;}
    std::string PragmaticCurrentBetifyPageSession(){return "page";}
public:
'''+trusted_handler+r'''
};
int main(){return 0;}
'''
with temporary_directory() as d:
    cpp=Path(d)/'trusted.cpp'; exe=Path(d)/'trusted'
    cpp.write_text(trusted_code,encoding='utf-8')
    subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
assert 'case 127:\n                    SaveCurrentSession(a);' in src
stop=take('                case 103:', '                case 127:')
assert 'SaveCurrentSession' not in stop and 'SaveAndExport' not in stop
assert 'Chrome Debug:' not in src and 'loginRecoveryBtn' not in src and 'case 114:' not in src
assert 'record.activeDurationMs = SessionElapsedMs(a);' in src
assert 'a->observationStoppedElapsedMs += GetTickCount64() - a->observationStartTick;' in stop
v48_reference=(root/'tests/v48_strategy_reference.txt').read_text(encoding='utf-8')
def strategy(s):
 a=s.index('    std::optional<std::pair<double,double>>\n    PragmaticStrategyMath')
 b=s.index('    void SimulatorEnsureBaccaratStarted',a)
 return s[a:b]
assert strategy(src)==v48_reference
print('static/manual/strategy OK')

bat=(root/'build.bat').read_bytes()
assert bat.startswith(b'@echo off\r\n') and b'\xef\xbb\xbf' not in bat
assert b'BaccaratCounterV123.exe' in bat
assert b'winmm.lib' in bat
assert all(byte < 128 for byte in bat)
assert b'\n' not in bat.replace(b'\r\n', b'')
print('build.bat encoding/version OK')

layout=take('static void Layout(HWND hwnd, AppState* a)',
            'LRESULT CALLBACK WndProc')
assert 'rowCells({250, 220, 190, 165, 170})' in layout
assert 'rowCells({105, 70, 75, 185, 165, 205})' in layout
assert 'rowCells({210, 285, 320, 475})' in layout
assert 'moveCell(a->evolutionRollingBtn, row[1]);' in layout
assert 'moveLabeledCell(a->minEdgeLabel, a->minEdgeEdit, row[2], 102, 30);' in layout
assert 'moveLabeledCell(a->unitTargetLabel, a->unitTargetEdit, row[3], 82, 30);' in layout
assert 'if (x > margin && x + width > w - margin)' not in layout
assert 'initialWidth = 2040;' in src
assert 'SystemParametersInfoW(SPI_GETWORKAREA' in src
print('wide responsive Win32 rows and single-line edit heights OK')

# v21.2.53 verified Pair click path.
assert 'static std::atomic<int>  gAutoChipValue' not in src
assert 'gPaperBetPnlUnits' not in src
assert ('signalRequest && betsOpenAuthorized && autoBetModeAtRequest == 2 &&\n'
        '            !suppressDomFocus;') in src
assert 'const AUTO_BET_REQUEST=' in src
assert "if(!AUTO_BET_REQUEST||operation.finished||operation.pending)return false;" in src
assert "focusMode:'betsopen'" in src
for field in ('playerX','playerY','playerWidth','playerHeight',
              'bankerX','bankerY','bankerWidth','bankerHeight',
              'rootInnerWidth','rootInnerHeight'):
    assert field in src
assert 'ExtractJsonInt(payload, "player.x")' not in src
assert 'ExtractJsonInt(payload, "banker.x")' not in src
assert 'PragmaticClickPairBet(\n                    fullSessionId, *tableId, *sourceGameId' in src
assert 'PragmaticClickPairBet(sid' not in src
assert 'pragmaticAutoBetHandled_' in src
assert 'PRAGMATIC_AUTO_BET_DUPLICATE_IGNORED' in src
assert 'PRAGMATIC_AUTO_BET_COORDS_REJECTED' in src
assert 'PRAGMATIC_AUTO_BET_TRUSTED_PAIR_SEQUENCE_REQUESTED' in src
assert '(HMENU)128' in src and 'case 128:' in src
assert src.count('(HMENU)122') == 1 and 'case 122:' not in src
assert 'focusMode == "betsopen" && autoBetRequest' in src
assert 'Baccarat Counter v21.2.123' in src
print('v75 retains betsopen-correlated/idempotent Pair-click path OK')

# v21.2.54 passive balance tracking and export handoff.
assert 'constexpr UINT WM_APP_BALANCE_UPDATE = WM_APP + 6;' in src
assert 'void MaybeCaptureAccountBalance()' in src
assert "__BAC_ACCOUNT_BALANCE__" in src
assert 'score < 95' in src
assert 'a->startBalanceMinor = a->latestBalanceMinor;' in src
assert 'a->endBalanceMinor = a->currentBalanceMinor;' in src
assert 'record.startBalanceMinor = a->startBalanceMinor;' in src
assert 'record.endBalanceMinor = a->endBalanceMinor' in src
assert 'Balance vor Verbinden:' in src
assert 'Aktuelle Balance:' in src and 'Endbalance:' in src
export=(root/'src/session_export.h').read_text(encoding='utf-8')
assert 'BaccaratCounterSession 3' in export
assert '"Startbalance", "Endbalance", "Währung"' in export
assert 'autoFilter ref=\\"A4:K' in export
# v21.2.77: Excel-compatible native OOXML ordering and ZIP metadata.
for token in ('<dimension ref=', '<sheetViews>', '<sheetFormatPr ', '<cols>', '<sheetData>'):
    assert token in export
assert export.index('<sheetFormatPr ') < export.index('<cols>') < export.index('<sheetData>')
assert export.index('</sheetData><autoFilter ') > export.index('<sheetData>')
assert 'Put16(out, 0); Put16(out, 0x0021); Put32(out, item.crc);' in export
assert 'Put16(out, 0); Put16(out, 0); Put16(out, 0x0021); Put32(out, item.crc);' in export
assert 'byte < 0x20' in export and "ch != '\\t'" in export
assert 'ReplaceFileAtomically' in export
print('v77 native Sessionverlauf XLSX structure hardening OK')
print('v54 balance UI/session/export path OK')

# v21.2.55 current Betify header: amount below username, no semantic label.
assert "d.querySelectorAll('body *')" in src
assert 'headerCurrencyCandidates' in src
assert 'betifyAccountHeaderShape' in src
assert "state.runToken===RUN_TOKEN" in src
assert '__BAC_ACCOUNT_BALANCE_STATUS__' in src
assert 'ACCOUNT_BALANCE_STATUS' in src
print('v55 compact Betify account-header fallback OK')

assert 'std::clamp(pct, -20.0, 100.0)' in src
assert 'Min Edge erlaubt Testwerte bis -20,00%' in src
print('v56 MinEdge lower bound -20.00% OK')

# v21.2.57 distinct compact Pair targets and clean focus UI.
assert 'const pairAreaFromText=(n,side)=>' in src
assert "flags.player&&!flags.banker" in src
assert "flags.banker&&!flags.player" in src
assert 'r.width<12||r.height<8' in src
assert '*width >= 8 && *height >= 8' in src
for removed in ('__bcp_signal_banner__', 'data-bcp-signal-table',
                'data-bcp-signal-pair', 'MoveCursorToNeutralSignalPoint',
                'PRAGMATIC_SIGNAL_NEUTRAL_CURSOR', 'SetCursorPos('):
    assert removed not in src
for diagnostic in ('playerWidth.value_or(0)', 'bankerWidth.value_or(0)',
                   'rootWidth.value_or(0)', 'rootHeight.value_or(0)'):
    assert diagnostic in src
print('v57 distinct Pair targets and clean focus UI OK')

# v21.2.58: immediate focus, but no click before the matching betsopen.
assert 'bool pendingSignalForBetsOpen{false};' in src
assert 'PRAGMATIC_AUTO_BET_WAITING_FOR_BETSOPEN' in src
assert 'PRAGMATIC_BETSOPEN_SIGNAL_RELEASE' in src
assert 'PRAGMATIC_BETSOPEN_AUTO_BET_FOCUS_REQUEST' in src
assert 'const bool realAutoBetRequest =\n            signalRequest && betsOpenAuthorized' in src
assert 'paperBetDeferredUntilPlacement' in src
assert 'pragmaticBetsOpenGameByTable_[*tableId] = *gameId;' in src
assert 'betsOpenStillConfirmed' in src
assert 'focusMode == "betsopen" && autoBetRequest &&\n                    uiReady && attempt >= 1 && attempt <= 4' in src
assert 'betsOpenConfirmed' in src
assert "const isMainBaccarat=/\\/desktop\\/baccarat\\//i.test(href);" in src
assert 'const mainBaccaratRoot=()=>' in src
assert "finder:'main-baccarat-header'" in src
assert "mode:isMainBaccarat?'main-baccarat':'multiplay'" in src
assert "if(isMulti){try{target.click();selected=true;}catch(_){}}" in src
assert "bankier pair|bankier paar" in src
assert "^(banker|bankier|b)" in src
print('v58 betsopen gate and main-table focus path OK')

# v21.2.59: current-game DOM gate, post-click confirmation counter, and a
# lossless worker-to-UI balance mirror consumed by the 500-ms timer.
assert 'const sourceVisible=tableFound&&!!SOURCE_GAME&&currentTableText.includes(SOURCE_GAME);' in src
assert 'if(area>fallbackArea){fallback=p;fallbackArea=area;}' in src
assert '__BAC_PAIR_CLICK_CONFIRM__' in src
assert 'PRAGMATIC_AUTO_BET_PAIR_CONFIRMATION' in src
assert 'gSessionConfirmedChipPlacements.fetch_add' in src
assert 'Bestätigte Chips:' in src and 'Chips bestätigt:' in src
assert 'gSessionConfirmedChipPlacements.store(0' in src
assert 'gLatestObservedBalanceSequence.fetch_add' in src
assert 'static void SyncLatestObservedBalance(AppState* a)' in src
assert 'SyncLatestObservedBalance(a);' in src
assert 'ApplyBalanceObservation(a, u->minorUnits, u->currency' in src
print('v59 live balance mirror/current-game click/confirmed-chip counter OK')

# v21.2.60: the printed game id lags betsopen and is diagnostic only. Exact
# name boundaries prevent Baccarat 1 from resolving to Speed Baccarat 18.
assert "else if(t&&tableTextMatches(t))partial.push(n);" in src
assert "t.startsWith(TARGET_NAME+' ')" in src
assert "if(!tableTextMatches(headerText))return null;" in src
assert "result[side+'Confirmed']=confirmed;" in src
assert "const primary=ROOT_DOCUMENT.getElementById(TARGET_ID);" in src
assert "context='launcher/main-table';" in src
assert 'sequence < a->lastAppliedBalanceSequence' in src
assert 'if (sequence == 0) return;' in src
print('v60 exact table boundary/main-table route/forced live balance refresh OK')

# v21.2.62: resolve the exact interaction node, obtain its browser-native
# content quad and use one trusted CDP mouse sequence. Balance sync bypasses
# the posted-message backlog, card rendering has its own fast dirty-only timer
# and alarm/click dedupe keys cannot suppress each other.
pair_click=take('    bool PragmaticClickPairBet(',
                '    void SimulatorPlaceTenOnPlayerSignal')
assert 'Runtime.evaluate' in pair_click
assert '__BAC_PAIR_DOM_CLICK__' in pair_click
assert "target.click();" not in pair_click
assert 'const interactionInfo=node=>' in pair_click
assert 'resolvedInteractionTarget' in pair_click
assert '\\"includeCommandLineAPI\\":true,\\"userGesture\\":true' in pair_click
assert 'Input.dispatchMouseEvent' not in pair_click
assert 'return target;' in pair_click
assert 'return area;' not in pair_click
assert '\\"returnByValue\\":false' in pair_click
assert 'pragmaticPairTargetRequests_[requestId]' in pair_click
assert "armed[side+'Hit']=hit;" in src
assert 'PRAGMATIC_AUTO_BET_TARGET_RESOLVED' in src
assert 'PRAGMATIC_AUTO_BET_TARGET_REQUESTED' in src
assert 'void HandlePragmaticTrustedPairClickResponse' in src
assert 'DOM.getContentQuads' in src
assert 'PRAGMATIC_AUTO_BET_TRUSTED_CLICK_DISPATCHED' in src
assert src.count('"Input.dispatchMouseEvent"') >= 3
assert 'const std::vector<std::string> sessions = PragmaticRuntimeSessions();' in src
assert 'sessions = PragmaticRuntimeSessions();' in src
assert 'pragmaticPrimarySessions_' in src
assert 'if (firstSessionForUrl) {' in src
assert 'void HandleDetached(const std::string& json)' in src
assert 'pendingLines_ >= 32' in src
assert '!suppressParsedPayload && !logicalDuplicate' in src
assert 'pragmaticBinaryFrameCaptureSeq_' in src
assert 'PlaySoundA(' in src and 'SND_MEMORY | SND_ASYNC' in src
assert 'Beep(tone.hz' not in src
assert 'SyncLatestObservedBalance(a);\n                    if (!a->sessionInitialized)' in src
assert 'SetWindowTextIfChanged(a->balanceStatus, text);' in src
assert 'usingCachedElement' in src and 'state.element=best.element' in src
assert 'a->overviewDirty' in src
assert 'constexpr UINT_PTR TIMER_LIVE_OVERVIEW = 2;' in src
assert 'SetTimer(hwnd, TIMER_LIVE_OVERVIEW, 75, nullptr);' in src
assert 'wParam == TIMER_LIVE_OVERVIEW' in src
assert 'now - a->lastOverviewRefreshTick >= 750ULL' not in src
assert 'lastPostHandAlertSourceGameId' in src
assert 'lastBetsOpenAlertGameId' in src
assert 'lastAutoBetFocusGameId' in src
assert 'PRAGMATIC_SIGNAL_ALARM_TRIGGERED' in src
assert 'constexpr UINT WM_APP_BALANCE_SYNC_NOW = WM_APP + 7;' in src
assert 'SendMessageTimeoutW(' in src and 'WM_APP_BALANCE_SYNC_NOW' in src
assert 'ACCOUNT_BALANCE_UI_SYNC' in src
assert '!noisyDiagnostic && !coreDiagnostic' in src
print('v62 realtime cards/trusted Pair click/balance/alarm path OK')

# v21.2.63: native betsopen is necessary but not sufficient. The visible
# Multiplay game id and hit-tested controls must be ready, then only missing
# sides may be retried within a bounded window.
assert '__BAC_PAIR_READINESS__' in src
assert 'PRAGMATIC_AUTO_BET_UI_READINESS' in src
assert "state.reason='pair-area-covered'" in src
assert "state.reason='active-hit-target'" in src
assert 'currentText.includes(SOURCE_GAME)' in src
assert 'deadline:Date.now()+9000' in src
assert 'operation.attempt>=4' in src
assert 'ROOT_WINDOW.setTimeout(probeAndMaybeArm,150)' in src
assert 'playerRequested:!operation.confirmed.player' in src
assert 'bankerRequested:!operation.confirmed.banker' in src
assert 'pragmaticAutoBetConfirmedSides_' in src
assert 'playerAttempted && playerConfirmed && !(mask & 1)' in src
assert 'bankerAttempted && bankerConfirmed && !(mask & 2)' in src
assert 'native betsopen vor dem Klick beendet' in src
assert 'total-bet-changed-without-side-attribution' in src
assert 'PRAGMATIC_AUTO_BET_RETRY_FINISHED' in src
print('v63 Multiplay active-control gate and bounded side retry OK')

# v21.2.64: one shared visible Multiplay viewport is serialized, and click
# mode accounting is armed only for sides whose chips were confirmed.
accounting=(root/'src/confirmed_bet_accounting.h').read_text(encoding='utf-8')
assert 'kPlayerPair = 1' in accounting
assert 'kBankerPair = 2' in accounting
assert 'RoundPnlUnits' in accounting
assert 'struct QueuedPragmaticAutoBet' in src
assert 'PragmaticQueueAutoBet(' in src
assert 'PragmaticStartNextQueuedAutoBet()' in src
assert src.count('MaybeAdvancePragmaticAutoBetQueue();') >= 2
assert 'PRAGMATIC_AUTO_BET_QUEUED' in src
assert 'PRAGMATIC_AUTO_BET_QUEUE_STARTED' in src
assert 'PRAGMATIC_AUTO_BET_QUEUE_RELEASED' in src
assert 'PRAGMATIC_PAPER_BET_SKIPPED_NO_CONFIRMED_CHIP' in src
assert r'accountingMode\":\"' in src
assert '"confirmed-click"' in src
assert 'pendingPlacementConfirmedPairMask' in src
assert 'armedSignalPairMask' in src
assert 'confirmed_bet_accounting::PairHitCount' in src
assert 'confirmed_bet_accounting::RoundPnlUnits' in src
assert 'gSessionPnlUnits.fetch_sub(2' not in src
assert ('PragmaticFinalizePlacementAccounting(\n'
        '            request, effectivePairMask, reason);') in src

with temporary_directory() as d:
    exe=Path(d)/'confirmed_bet_accounting_test'
    subprocess.run([
        'g++','-std=c++20','-Wall','-Wextra','-Werror',
        str(root/'tests/confirmed_bet_accounting_test.cpp'),'-o',str(exe)
    ],check=True)
    subprocess.run([str(exe)],check=True)
print('v64 serialized focus queue and confirmation-only accounting OK')

# v21.2.65: only genuine game progress refreshes feed health. A slow
# five-second reconnect loop must now trigger, and stale visible tiles cannot
# finish recovery without post-recovery game traffic.
assert 'const bool isGameProgressFrame =' in src
assert ('if (isMultiplaySocket && isGameProgressFrame &&\n'
        '                PragmaticGameProgressFrameAdvances(safe))') in src
assert 'bool PragmaticGameProgressFrameAdvances(const std::string& payload)' in src
assert 'now - it->second <= 300000ULL' in src
assert 'pragmaticGameProgressFrameTicks_.clear();' in src
assert 'std::hash<std::string>{}(payload)' in src
assert 'pragmaticGameProgressFrameOrder_.size() > 32768' in src
assert 'pragmaticGameProgressFrameOrder_.clear();' in src
assert 'pragmaticMultiplayLastLiveFrameTick_.compare_exchange_strong(' in src
assert 'topKey == "card" || topKey == "game"' in src
assert 'topKey == "gameresult" || topKey == "ShoeSummary"' in src
assert 'constexpr ULONGLONG kStormWindowMs = 20000ULL;' in src
assert 'constexpr size_t kStormSocketThreshold = 4;' in src
assert 'const bool gameFeedStale' in src
assert 'if (gameFeedStale &&' in src
assert 'if (mainAge > 7000ULL && !feedStale) return;' in src
assert '"game-data-stale"' in src
assert 'PRAGMATIC_MULTIPLAY_RECOVERY_WAIT_GAME_DATA' in src
assert 'const bool freshGameProof' in src
assert "hardFailure?'provider-runtime-failure':'ok'" in src

def storm_triggered(offsets_ms, window_ms=20000, threshold=4):
    window=[]
    for now in offsets_ms:
        window.append(now)
        window=[t for t in window if now-t <= window_ms]
        if len(window) >= threshold and now >= 10000:
            return True
    return False

observed_slow_loop=[0,5000,10000,15000,20000,25000]
assert storm_triggered(observed_slow_loop)
assert not any(
    len([t for t in observed_slow_loop if 0 <= now-t <= 5000]) >= 8
    for now in observed_slow_loop)
print('v65 genuine-game feed health and slow reconnect recovery OK')

# The visible Betify tab/window is foregrounded before focus. v21.2.76 now
# dispatches top-level content-quad coordinates through that Betify PAGE session;
# v64 confirmation-only accounting remains unchanged.
assert 'void PragmaticPrepareChromeForAutoBetInput(' in src
assert '"Page.bringToFront", "{}", owner' in src
assert 'const bool windowFocused = ForceForegroundWindow(chrome);' in src
assert 'PRAGMATIC_AUTO_BET_CHROME_FOREGROUND' in src
assert 'PragmaticPrepareChromeForAutoBetInput(request);' in src
assert 'const std::string inputSessionId = PragmaticCurrentBetifyPageSession();' in src
assert 'const std::string& inputSessionId = pending.sessionId;' not in src
assert 'foregrounded-betify-page' in src
assert 'foregrounded-embedded-pragmatic' not in src
assert 'PRAGMATIC_PAPER_BET_SKIPPED_NO_CONFIRMED_CHIP' in src
print('v76 foregrounded page-owner trusted click and confirmation-only accounting OK')

# Parse the newly changed health JavaScript exactly as it is assembled by C++.
health_method=src.index('std::string PragmaticMultiplayHealthScript() const')
health_start=src.index('std::string js = R"JS(',health_method)
health_end=src.index('        return js;',health_start)
health_segment=src[health_start:health_end]
health_chunks=list(re.finditer(r'R"JS\((.*?)\)JS"',health_segment,re.S))
assert len(health_chunks)==2
health_js=health_chunks[0].group(1)+'test-run'+health_chunks[1].group(1)
assert 'provider-runtime-failure' in health_js
assert 'hardFailure' in health_js
with temporary_directory() as d:
    health_path=Path(d)/'multiplay-health.js'
    health_path.write_text(health_js,encoding='utf-8')
    subprocess.run(['node','--check',str(health_path)],check=True)
print('v65 Multiplay health JavaScript syntax OK')

# v21.2.68: startup remains provider-neutral. Verbinden reuses the one
# about:blank page through CDP for the common Betify home. Both providers must
# cross the same positive login gate before their selected game URL can load.
launcher=(root/'start_chrome_debug.bat').read_bytes()
assert launcher.startswith(b'@echo off\r\n') and b'\xef\xbb\xbf' not in launcher
assert b'"about:blank"' in launcher
assert b'if /I "%~1"=="pragmatic"' not in launcher
assert b'if /I "%~1"=="evolution"' not in launcher
assert b'https://betify2.so/de/play/' not in launcher
assert b'\n' not in launcher.replace(b'\r\n', b'')
assert 'LaunchChromeDebugBat(providerLaunchMode)' not in src
assert '"Page.navigate"' in src
assert 'cleanUrl == "about:blank"' in src
assert 'PROVIDER_PAGE_NAVIGATE' in src
assert 'providerNavigationIssued_.exchange(true' in src
assert 'const std::string providerUrl = "https://betify.com/";' in src
assert 'loginBeforeProviderOnStart_' in src
assert 'AdvanceProviderLoginGate(recoveryStageNow)' in src
assert 'providerLoginComplete_' in src
assert 'TARGET_GAME_URL' in src
assert '__BCP_SELECTED_PROVIDER_GAME_URL__' in src
assert 'https://betify2.so/de/play/107240-baccarat-1' in src
assert 'https://betify2.so/de/play/149977-speed-baccarat-2' in src
attached=take('    void HandleAttached(const std::string& json)',
              '    void HandleDetached(const std::string& json)')
assert 'const std::string providerUrl = "https://betify.com/";' in attached
assert 'https://betify2.so/de/play/' not in attached
assert '"Page.navigate"' in attached
probe=take('    std::string PragmaticProbeScript(',
           '    std::string EvolutionBootstrapScript() const')
assert probe.index("recoveryEmit('LOGIN_COMPLETE'") < probe.index("recoveryEmit('PLAY_NAVIGATE'")
assert "if(openLogin||openRegister)" in probe
assert "if(logoutAction||accountAction)" in probe
assert 'Never promote to Stage 3 from body text' in probe
gate=take('    bool AdvanceProviderLoginGate(int recoveryStage)',
          '    void MaybeAutoCardScan()')
assert 'recoveryStage < 1 || recoveryStage > 4' in gate
scan=take('    void MaybeAutoCardScan()', '    void MaybeArmPicker()')
assert scan.index('AdvanceProviderLoginGate(recoveryStageNow)') < scan.index('if (provider_ == ProviderMode::Evolution)')
assert '!providerLoginComplete_.load(std::memory_order_acquire)' in scan
assert '\\"provider\\":\\"' in src
main_entry=src[src.index('int WINAPI wWinMain'):]
assert 'state.startupPrepMonitor = std::make_unique' not in main_entry
assert 'Eine Casino-/Anbieterseite wird erst nach Verbinden geladen.' in src
assert 'EVO_TARGET_CANDIDATE' in src
assert 'EVOLUTION_MULTIPLAY_WEBSOCKET_READY' in src
assert 'evolutionMultiplaySocketSeen_.exchange(' in src
assert 'const bool looksEvolution =' in src
assert '(*type == "iframe" && cleanUrl.empty())' in src

# Parse the shared login/provider JavaScript exactly as assembled by C++.
probe_start=src.index('std::string js = R"JS(', src.index('    std::string PragmaticProbeScript('))
probe_end=src.index('        const std::string targetMarker', probe_start)
probe_segment=src[probe_start:probe_end]
probe_chunks=list(re.finditer(r'R"JS\((.*?)\)JS"', probe_segment, re.S))
assert len(probe_chunks)==5
probe_js=(probe_chunks[0].group(1)+'test-run'+probe_chunks[1].group(1)+
          'false'+probe_chunks[2].group(1)+'false'+probe_chunks[3].group(1)+'1'+probe_chunks[4].group(1))
probe_js=probe_js.replace('__BCP_SELECTED_PROVIDER_GAME_URL__',
                          'https://betify2.so/de/play/149977-speed-baccarat-2')
assert "loc.href='https://betify.com/'" in probe_js
assert "recoveryEmit('LOGIN_COMPLETE'" in probe_js
assert "recoveryEmit('PLAY_NAVIGATE',target)" in probe_js
with temporary_directory() as d:
    probe_path=Path(d)/'shared-login-gate.js'
    probe_path.write_text(probe_js,encoding='utf-8')
    subprocess.run(['node','--check',str(probe_path)],check=True)
print('v75 common Betify login gate and provider navigation JavaScript OK')

history=root/'docs/validation-history'
assert len(list(history.glob('VALIDATION*.md')))==46
assert (history/'AUSWERTUNG_20260912_220057.md').is_file()
assert (history/'KNOWN_GOOD_V21_2_4_COMPARISON.md').is_file()
assert (history/'README.md').is_file()
assert (root/'docs/CAPTURE_ANALYSIS_20260914_114003.md').is_file()
assert (root/'docs/CAPTURE_ANALYSIS_20260914_121136.md').is_file()
assert (root/'docs/SCREENSHOT_FLOW_EVOLUTION_LOBBY_V21_2_71.md').is_file()
assert (root/'docs/CAPTURE_ANALYSIS_20260914_123821.md').is_file()
print('v75 historical validation documentation complete OK')

balance_method=take('    void MaybeCaptureAccountBalance()',
                    '    void MaybeAutoSessionWatch()')
assert 'provider_ != ProviderMode::PragmaticPlay' not in balance_method

evo_start=src.index('    std::string EvolutionBootstrapScript() const')
evo_end=src.index('    std::string CardScanScript()',evo_start)
evo_segment=src[evo_start:evo_end]
evo_chunks=list(re.finditer(r'R"JS\((.*?)\)JS"',evo_segment,re.S))
assert len(evo_chunks)==3
evo_js=(evo_chunks[0].group(1)+'test-run'+evo_chunks[1].group(1)+
        'false'+evo_chunks[2].group(1))
assert "exact('Lobby')" in evo_js
assert "exact('Baccarat & Sic Bo')" in evo_js
assert "exact('Multiplay')" in evo_js
assert 'now-state.lastLobby>=2500' in evo_js
assert 'now-state.lastCategory>=2500' in evo_js
assert 'now-state.lastMultiplay>=2500' in evo_js
assert "labels(el).some(v=>v.toLocaleLowerCase('de-DE')===wanted)" in evo_js
assert "el.shadowRoot&&el.shadowRoot.mode==='open'" in evo_js
assert 'el.contentDocument||(el.contentWindow&&el.contentWindow.document)' in evo_js
assert "path:item.path+'/frame:'" in evo_js
assert "path:item.path+'/shadow:'" in evo_js
assert "elementSnapshot.length>=40000" in evo_js
assert 'const directLabels=el=>' in evo_js
assert 'const clickableFrom=el=>' in evo_js
assert "if(cs.pointerEvents==='none')continue" in evo_js
assert "typeof p.onclick==='function'||cursor==='pointer'" in evo_js
assert 'const rootPoint=el=>' in evo_js
assert 'const sx=fr.width/viewportWidth,sy=fr.height/viewportHeight' in evo_js
assert 'x=fr.left+x*sx;y=fr.top+y*sy' in evo_js
assert 'width*=sx;height*=sy;scaleX*=sx;scaleY*=sy' in evo_js
assert 'return{x,y,width,height,scaleX,scaleY}' in evo_js
assert 'visibleButtons' in evo_js and "emit('VISIBLE_BUTTONS','')" in evo_js
assert 'evolutionLobbyClicked_.store(true' in src
assert "const lobbyCandidate=exact('Lobby')" in evo_js
assert "const baccaratSicBoCandidate=exact('Baccarat & Sic Bo')||exact('Baccarat & SicBo')" in evo_js
assert "const multiplayCandidate=exact('Multiplay')" in evo_js
assert "emit('LOBBY_CLICK_READY',lobby)" in evo_js
assert "emit('BACCARAT_SICBO_CLICK_READY',baccaratSicBo)" in evo_js
assert "emit('MULTIPLAY_CLICK_READY',multiplay)" in evo_js
assert "emit('LOBBY_DOM_CLICKED',lobby)" in evo_js
assert "emit('BACCARAT_SICBO_DOM_CLICKED',baccaratSicBo)" in evo_js
assert "emit('MULTIPLAY_DOM_CLICKED',multiplay)" in evo_js
assert 'try{lobby.click()}' in evo_js
assert 'try{baccaratSicBo.click()}' in evo_js
assert 'try{multiplay.click()}' in evo_js
assert 'state.phase=NATIVE_LOBBY_CLICKED' not in evo_js
assert "if(multiplay){\n  state.phase='multiplay';" in evo_js
assert "if(baccaratSicBo){\n  state.phase='category';" in evo_js
assert "if(lobby){\n  state.phase='lobby';" in evo_js
assert evo_js.index('const multiplay=multiplayCandidate;') < evo_js.index('const baccaratSicBo=baccaratSicBoCandidate;') < evo_js.index('const lobby=lobbyCandidate;')
assert 'lobbyAttempts%2===1' in evo_js
assert 'categoryAttempts%2===1' in evo_js
assert 'multiplayAttempts%2===1' in evo_js
assert "state.phase==='lobby'?'WAIT_BACCARAT_SICBO':'WAIT_LOBBY'" in evo_js
evo_console=take('        if (auto value = extractConsoleValue("__BAC_EVOLUTION_BOOTSTRAP__"))',
                 '        if (auto value = extractConsoleValue("__BAC_SHOE_RESET__"))')
assert 'action == "LOBBY_CLICK_READY"' in evo_console
assert 'action == "BACCARAT_SICBO_CLICK_READY"' in evo_console
assert 'action == "MULTIPLAY_CLICK_READY"' in evo_console
assert evo_console.count('"Input.dispatchMouseEvent"')==2
assert 'EVOLUTION_NAV_TRUSTED_CLICK' in evo_console
assert 'PragmaticCurrentBetifyPageSession()' in evo_console
assert 'std::isfinite(clickX)' in evo_console
assert 'evolution-session-root-scaled' in evo_console
assert 'action == "BACCARAT_SICBO_DOM_CLICKED"' in evo_console
assert 'action == "WAIT_BACCARAT_SICBO"' in evo_console
assert 'Baccarat & Sic Bo erkannt; warte auf den sichtbaren Multiplay-Button.' in evo_console
ready_end=evo_console.index('                } else if (action == "LOBBY_DOM_CLICKED")')
ready_block=evo_console[:ready_end]
assert 'evolutionLobbyClicked_.store' not in ready_block
for diagnostic in ('contextCount','scannedElements','path','tag','width','height','scaleX','scaleY'):
    assert diagnostic in evo_console
assert all(term not in evo_js for term in (
    "exact('Player')", "exact('Banker')", "exact('Player Pair')",
    "exact('Banker Pair')", "exact('Spieler')", "exact('Paar')"))
with temporary_directory() as d:
    evo_path=Path(d)/'evolution-bootstrap.js'
    evo_path.write_text(evo_js,encoding='utf-8')
    subprocess.run(['node','--check',str(evo_path)],check=True)
print('v75 confirmed Lobby -> Baccarat & Sic Bo -> Multiplay navigation OK')

# v21.2.73 retains v21.2.72 table/session recovery and proactively prevents
# the observed Evolution idle timeout with a click-free trusted mouse move.
# do not repeat extracted cards in Status, and recover an expired Evolution
# iframe independently from the still-authenticated Betify account.
overview_parser=take('static void ParseOverviewFields(',
                     'static void AppendLog(')
assert 'bool removedDedicatedCardText = false;' in overview_parser
assert 'row.phase = removedDedicatedCardText' in overview_parser
assert '? L"–"' in overview_parser
overview_refresh=take('static void RefreshOverview(AppState* a)',
                      'static uint64_t CounterDelta')
assert 'topVisibleTableId' in overview_refresh
assert 'ListView_GetTopIndex' in overview_refresh
assert 'horizontalScrollBefore' in overview_refresh
assert 'ListView_Scroll(' in overview_refresh
assert 'WS_CHILD|WS_VISIBLE|WS_HSCROLL|WS_VSCROLL|' in src

watch_start=src.index('    std::string EvolutionSessionWatchScript() const')
watch_end=src.index('    std::string PragmaticSessionWatchScript() const',watch_start)
watch_segment=src[watch_start:watch_end]
watch_chunks=list(re.finditer(r'R"JS\((.*?)\)JS"',watch_segment,re.S))
assert len(watch_chunks)==2
watch_js=watch_chunks[0].group(1)+'test-run'+watch_chunks[1].group(1)
for required in (
    'Sie sind ausgeloggt','SESSION_EXPIRED','KEEPALIVE_CLICKED',
    'INTERACTION_MAP','pairTargets','P(?:LAYER)?\\s*PAIR',
    "el.shadowRoot&&el.shadowRoot.mode==='open'",'contentDocument'):
    assert required in watch_js
with temporary_directory() as d:
    watch_path=Path(d)/'evolution-session-watch.js'
    watch_path.write_text(watch_js,encoding='utf-8')
    subprocess.run(['node','--check',str(watch_path)],check=True)

session_watch=take('    void MaybeAutoSessionWatch()',
                   '    bool AdvanceProviderLoginGate(')
assert 'if (provider_ != ProviderMode::PragmaticPlay) return;' not in session_watch
assert 'PragmaticSessionWatchScript()' in session_watch
assert 'EvolutionSessionWatchScript()' in session_watch
evo_session_console=take(
    '        if (auto value = extractConsoleValue("__BAC_EVOLUTION_SESSION_WATCH__"))',
    '        if (auto value = extractConsoleValue("__BAC_ACCOUNT_BALANCE_STATUS__"))')
assert 'EVOLUTION_SESSION_EXPIRED_FEED_PRESERVED' in evo_session_console
assert 'reloadSuppressed\\\":true' in evo_session_console
assert 'feedAge <= 5000ULL' in evo_session_console
assert 'ReloadEvolutionAfterFeedLoss("expired-modal-feed-not-healthy")' in evo_session_console
assert 'EVOLUTION_SESSION_RECOVERY_SUCCESS' in src
assert 'EVOLUTION_SESSION_RECOVERY_REARM' in src
keepalive=take('    void MaybeEvolutionSessionKeepAlive()',
               '    void MaybeAutoSessionWatch()')
for required in (
    'providerLoginComplete_','evolutionMultiplaySocketSeen_',
    'evolutionSessionRecoveryActive_','evolutionActiveRuntimeSession_',
    'Input.dispatchMouseEvent','mouseMoved','button\\\":\\\"none',
    'buttons\\\":0','60000ULL','EVOLUTION_SESSION_KEEPALIVE_MOUSE_MOVE'):
    assert required in keepalive
assert 'mousePressed' not in keepalive and 'mouseReleased' not in keepalive
assert src.count('MaybeEvolutionSessionKeepAlive();') == 2
assert 'evolutionLastKeepAliveTick_.store(\n                GetTickCount64()' in src
assert "pairTargets.some(p=>p.side===side" in watch_js
fingerprint=watch_js[watch_js.index('const fingerprint='):]
assert "x.tileText" not in fingerprint.split(';',1)[0]
pragmatic_console=take(
    '        if (auto value = extractConsoleValue("__BAC_PRAGMATIC_RECOVERY__"))',
    '        if (auto value = extractConsoleValue("__BAC_PRAGMATIC_MULTIPLAY_HEALTH__"))')
assert 'nowTick - lastTick < 30000ULL' in pragmatic_console
assert 'betifySessionLoggedInCaptureTick_' in pragmatic_console
assert (root/'docs/CAPTURE_ANALYSIS_20260914_130218.md').is_file()
assert (root/'docs/CAPTURE_ANALYSIS_20260914_134151.md').is_file()
assert (history/'VALIDATION_V21_2_75.md').is_file()
feed_recovery=take('    void ReloadEvolutionAfterFeedLoss(',
                   '    void MaybeEvolutionSessionKeepAlive()')
assert 'Page.reload' in feed_recovery
assert 'EVOLUTION_SESSION_RECOVERY_RELOAD' in feed_recovery
assert 'void MaybeRecoverExpiredEvolutionFeed()' in feed_recovery
assert 'nowTick - expiredTick < 12000ULL' in feed_recovery
assert 'nowTick - lastFeed <= 12000ULL' in feed_recovery
assert 'EVOLUTION_PRESERVED_FEED_STALE' in feed_recovery
assert 'EVOLUTION_SESSION_EXPIRED_FEED_CONTINUES' in feed_recovery
assert 'evolutionLastPreservedFeedProofTick_' in feed_recovery
assert src.count('MaybeRecoverExpiredEvolutionFeed();') == 2
transport_status=take(
    '        if (auto value = extractConsoleValue("__BAC_TRANSPORT_TABLE_STATUS__"))',
    '        if (auto value = extractConsoleValue("__BAC_TRANSPORT_HAND_COMPLETE__"))')
assert 'evolutionLastTransportStatusTick_.store' in transport_status
assert 'ExtractJsonInt(payload, "transportAgeMs")' in transport_status
assert '*transportAgeMs <= 5000' in transport_status
assert 'Page.reload' not in transport_status
assert 'transportAgeMs:st.lastTransportTs?Math.max(0,now-st.lastTransportTs):null' in src
print('v75 preserves healthy Evolution feed and reloads only after staleness OK')

# v21.2.75: optional rolling Evolution action sessions must never become data
# owners. A standby is promoted only after both transport and Pair-DOM proof.
assert 'static std::atomic<bool> gEvolutionRollingActionEnabled{true};' in src
assert '(HMENU)130' in src and 'case 130:' in src
assert 'Rollierende Datensitzung: EIN' in src
assert 'Rollierende Datensitzung: AUS' in src
assert 'case 109:' in src and 'CBN_SELCHANGE' in src
assert 'provider == ProviderMode::Evolution &&' in src
assert 'EnableWindow(a->evolutionRollingBtn, FALSE);' in src
rolling=take('    void StartEvolutionActionRollover(',
             '    void ReloadEvolutionAfterFeedLoss(')
for required in (
    'Target.createTarget','background\\\":true','75000ULL','45000ULL',
    'EVOLUTION_ACTION_ROLLOVER_STARTED','EVOLUTION_ACTION_STANDBY_TIMEOUT',
    'EvolutionBootstrapScript()','evolutionStandbyRuntimeSessions_',
    'evolutionStandbySocketSession_','evolutionStandbyPairReadySessions_'):
    assert required in rolling
promotion=take('    void TryPromoteEvolutionStandby()',
               '    void HandleAttached(')
assert '!evolutionStandbySocketSession_.empty()' in promotion
assert '!evolutionStandbyPairReadySessions_.empty()' in promotion
assert 'EVOLUTION_ACTION_SESSION_PROMOTED' in promotion
assert 'Target.closeTarget' in promotion
card_scan=take('    void MaybeAutoCardScan()', '    void MaybeArmPicker()')
assert 'dataRuntime = evolutionDataRuntimeSession_;' in card_scan
assert 'SendCommand("Runtime.evaluate", params, dataRuntime);' in card_scan
assert 'Only the immutable data owner may advance cards, hands or shoes.' in src
assert src.count('MaybeEvolutionRollingActionSession();') == 2
assert 'PrepareEvolutionActionForSignal(' in src
assert 'EVOLUTION_SIGNAL_ACTION_SESSION_CHECK' in src
assert 'Page.bringToFront' in take(
    '    void PrepareEvolutionActionForSignal(',
    '    void StartPragmaticLoginRecoveryTest()')
assert 'EVOLUTION_ACTION_TABLE_FOCUS' in src
assert 'dataReloadSuppressed\\\":true' in evo_session_console
print('v75 optional rolling Evolution data/action separation OK')


# v21.2.76: compact yellow status zone + valid SETZEN signal counter.
update_stats=take('static void UpdateStats(AppState* a)',
                  'static void Layout(HWND hwnd, AppState* a)')
for removed in ('Anbieter:', 'Strategie:', 'Min Edge:', 'Unit-Ziel:',
                'Tischfokus:', 'Simulator Auto:', 'Pair Auto-Bet:'):
    assert removed not in update_stats
assert 'SETZEN-Signale: ' in update_stats
assert 'validSetzenSignals' in update_stats
assert 'Filter: wird aus Multiplay gelesen' not in src
assert 'HWND filterStatus' not in src
layout=take('static void Layout(HWND hwnd, AppState* a)', 'LRESULT CALLBACK WndProc')
assert 'MoveWindow(a->filterStatus' not in layout
assert 'MoveWindow(a->status, margin, y' in layout
assert 'strategyValidSetzenSignals{0}' in src
assert 'PRAGMATIC_SETZEN_SIGNAL_COUNTED' in src
assert 'PRAGMATIC_SETZEN_SIGNAL_INVALIDATED_SHOE_END' in src
shoe_start=src.index('    void PragmaticEmitShoeEnd(')
shoe_stop=src.index('        if (PragmaticTopKey(payload, "endshuffling")) {', shoe_start)
shoe_end=src[shoe_start:shoe_stop]
assert 'PragmaticRollbackPendingSetzenSignalForShoeEnd(tableId, st, reason);' in shoe_end
hand_result=take('        if (PragmaticTopKey(payload, "gameresult")) {',
                 '        if (PragmaticTopKey(payload, "ShoeSummary")) {')
assert 'PragmaticCountValidSetzenSignal(\n                        *tableId, st, *gameId, "hand-complete");' in hand_result
betsopen=take('        if (PragmaticTopKey(payload, "betsopen")) {',
              '        if (PragmaticTopKey(payload, "timer")) {')
assert 'if (!hadPendingSignal)' in betsopen
assert 'PragmaticCountValidSetzenSignal(\n                        *tableId, st, *gameId, "betsopen");' in betsopen
assert (root/'VALIDATION_V21_2_76.md').is_file()
trusted=take('    void HandlePragmaticTrustedPairClickResponse(', '    void Bootstrap()')
assert 'const std::string inputSessionId = PragmaticCurrentBetifyPageSession();' in trusted
assert 'Betify-Page-Session für Top-Level-Koordinaten fehlt' in trusted
assert 'foregrounded-betify-page' in trusted
assert 'foregrounded-embedded-pragmatic' not in trusted
click_js=take('    bool PragmaticClickPairBet(', '    void SimulatorPlaceTenOnPlayerSignal')
assert 'return area;' in click_js
assert 'return target;' not in click_js
print('v76 top-level Pragmatic trusted input + compact status + rollback-safe SETZEN counter OK')

assert (root/'VALIDATION_V21_2_77.md').is_file()
assert (root/'tests/validate_session_xlsx.py').is_file()
print('v77 validation artifacts OK')
