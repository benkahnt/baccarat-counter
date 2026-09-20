"""Exercise the production one-shot worker decision with offline table fixtures."""
from pathlib import Path
import subprocess
from test_toolchain import compile_cpp, temporary_directory

root = Path(__file__).resolve().parents[1]
source = (root / 'src/main.cpp').read_text(encoding='utf-8-sig')
start = source.index('    void MaybeStartManualChipTest() {')
end = source.index('    void PragmaticFinishActiveAutoBet(', start)
method = source[start:end]

assert 'case 138: {' in source
ui = source[source.index('case 138: {'):source.index('case 128: {')]
assert 'ListView_GetNextItem' in ui and 'overviewOrder[selected]' in ui
assert 'RequestManualChipTest(WideToUtf8(tableId))' in ui
focus = source[source.index('void PragmaticFocusSignalTable('):source.index('void PragmaticStartNextQueuedAutoBet()')]
assert '((signalRequest && autoBetModeAtRequest == 2) || manualChipTest)' in focus
assert "focusMode:AUTO_BET_REQUEST?'betsopen'" in focus

harness = r'''
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <regex>
#include <sstream>
#include "strategy_edge_thresholds.h"
#include "confirmed_bet_accounting.h"
#include <atomic>
#include <cassert>
#include <cstdint>
#include <map>
#include <mutex>
#include <optional>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using namespace std;
using ULONGLONG=unsigned long long;
static ULONGLONG nowTick=1000;
static ULONGLONG GetTickCount64(){return nowTick;}
static atomic<int> gPairChipCents{20};
static atomic<double> gCombinedMinEdgeThreshold{.0025};
static atomic<bool> gUnitTargetReached{false},gStopLossReached{false};
static string IsoNow(){return "fixture";}
static string JsonEscape(const string& s){return s;}
static wstring Utf8ToWide(const string& s){return wstring(s.begin(),s.end());}
static wstring FormatTelegramMoneyMinor(int n,int){return to_wstring(n);}
enum class ProviderMode{PragmaticPlay,Evolution};
struct PragmaticSideBetLimitTier {int fromHand{0};int maxPercentOfMain{0};};
PRODUCTION_STAKE_PLAN
using Plan=PragmaticStakePlan;
struct Table{
 string name="Selected",currentGame="g1",pendingPlacementGameId,realMainBetGameId;
 bool shoeTracked=true,shoeTrusted=true,strategyReady=true,shuffling=false;
 int shoeHands=60,summaryTotalGames=-1;
 int pairPlayerMaxBetCents=50000,pairBankerMaxBetCents=50000;
 int playerMaxBetCents=500000,bankerMaxBetCents=500000,tieMaxBetCents=50000;
 vector<int> chipAmountsCents{20,100,200,500,2500,10000};
 vector<PragmaticSideBetLimitTier> pairSideBetLimits;
 uint64_t shoeGeneration=1;
 unordered_map<string,int> strategyRanks{{"10",32}};
 Plan pendingStakePlan;
 double pendingPlacementProbability=0,pendingPlacementEdge=0;
 int pendingPlacementConfirmedPairMask=0;
};
using PragmaticTableRuntime=Table;
PRODUCTION_REQUEST_STRUCT
struct QueuedPragmaticAutoBet{string tableId,tableName,sourceGameId;double probability,edge;ULONGLONG enqueuedTick,startedTick;bool manualChipTest;};
enum class StrategyMode{LuckyPairs};
PRODUCTION_PLANNER
struct Ev{double playerWinProbability=.44,bankerWinProbability=.46,tieProbability=.10;};
struct Capture{vector<string> lines;void WriteRaw(const string& s){lines.push_back(s);}};
struct Harness{
 ProviderMode provider_=ProviderMode::PragmaticPlay;
 mutex pragmaticManualChipTestMu_;
 optional<ManualChipTestRequest> pragmaticManualChipTestPending_;
 unordered_set<string> pragmaticManualChipTestGames_;
 unordered_map<string,Table> pragmaticTables_{{"t",Table{}}};
 unordered_set<string> pragmaticInactiveTableIds_,pragmaticExcludedTableIds_;
 unordered_set<string> pragmaticMainTableIds_{"t"},pragmaticVisibleFilterNames_;
 bool pragmaticFilterSeen_=false,queueBusy=false,betsOpen=false,planValid=true;
 atomic<int> pragmaticRecoveryStage_{0};
 atomic<bool> pragmaticMultiplayConflict_{false};
 Capture capture_;
 vector<wstring> logs;
 bool queued=false,forceMain=false;
 int focuses=0,foregrounds=0;
 StrategyMode strategy_=StrategyMode::LuckyPairs;
 string planningSide;
 Table plannedState;
 void PragmaticPrepareChromeForAutoBetInput(const QueuedPragmaticAutoBet& r){assert(r.tableId=="t");++foregrounds;}
 void PragmaticFocusSignalTable(const string& t,Table&,const string&,double,double,
     bool manual,bool priority,bool open,bool announce,bool suppress,bool chipTest){
  assert(t=="t"&&manual&&!priority&&!open&&!announce&&!suppress&&!chipTest);++focuses;
 }
 double plannedEdge=999;
 string queuedTable,queuedGame;
 void Log(const wstring& s){logs.push_back(s);}
 bool PragmaticNativeBetsOpen(const string& t,const string& g){return betsOpen&&t=="t"&&g=="g1";}
 bool PragmaticAutoBetQueueBusy(){return queueBusy;}
 PRODUCTION_STRATEGY_MATH
 Plan PragmaticBuildStakePlan(const Table& st,double edge,bool manual,bool force){
  assert(!manual);plannedEdge=edge;forceMain=force;plannedState=st;
  auto p=::PragmaticBuildStakePlan(st,edge,manual,force);p.valid=p.valid&&planValid;planningSide=p.mainSide;return p;
 }
 void PragmaticQueueAutoBet(const string& t,Table&,const string& g,double,double,bool manual){
  assert(manual);queued=true;queuedTable=t;queuedGame=g;
 }
'''
harness += method
harness += r'''
 void request(){pragmaticManualChipTestPending_=ManualChipTestRequest{"t",nowTick,0,false};}
};
int main(){
 nowTick=1000;Harness ready;ready.betsOpen=true;ready.request();ready.MaybeStartManualChipTest();
 assert(ready.queued&&ready.forceMain&&ready.planningSide=="Tie");
 assert(ready.queuedTable=="t"&&ready.queuedGame=="g1");
 assert(ready.pragmaticTables_["t"].pendingPlacementGameId=="g1");
 assert(!ready.pragmaticManualChipTestPending_);
 assert(ready.capture_.lines[1].find("pairMinEdgeBypassed")!=string::npos);
 ready.request();ready.MaybeStartManualChipTest();assert(!ready.pragmaticManualChipTestPending_);
 nowTick=1000;Harness wait;wait.request();wait.MaybeStartManualChipTest();
 assert(!wait.queued&&wait.pragmaticManualChipTestPending_->waitLogged&&wait.focuses==1&&wait.foregrounds==1);
 wait.MaybeStartManualChipTest();assert(wait.focuses==1);
 nowTick=1300;wait.betsOpen=true;wait.MaybeStartManualChipTest();assert(wait.queued);
 nowTick=1000;Harness early;early.pragmaticTables_["t"].shoeHands=59;early.betsOpen=true;
 early.request();early.MaybeStartManualChipTest();assert(!early.queued&&!early.pragmaticManualChipTestPending_);
 Harness unstable;unstable.pragmaticTables_["t"].summaryTotalGames=62;unstable.pragmaticTables_["t"].shoeTrusted=false;unstable.betsOpen=true;
 unstable.request();unstable.MaybeStartManualChipTest();assert(unstable.queued&&unstable.planningSide=="Banker");
 assert(!unstable.pragmaticTables_["t"].shoeTrusted);
 Harness changed;changed.request();changed.MaybeStartManualChipTest();
 changed.pragmaticTables_["t"].shoeGeneration=2;changed.betsOpen=true;
 changed.MaybeStartManualChipTest();assert(!changed.queued&&!changed.pragmaticManualChipTestPending_);
 Harness busy;busy.queueBusy=true;busy.betsOpen=true;busy.request();busy.MaybeStartManualChipTest();
 assert(!busy.queued&&busy.pragmaticManualChipTestPending_&&busy.focuses==0);
 Harness existing;existing.betsOpen=true;existing.pragmaticTables_["t"].realMainBetGameId="g1";
 existing.request();existing.MaybeStartManualChipTest();assert(!existing.queued);
 Harness invalid;invalid.betsOpen=true;invalid.planValid=false;
 invalid.request();invalid.MaybeStartManualChipTest();assert(!invalid.queued);
 Harness stopped;stopped.betsOpen=true;gStopLossReached=true;
 stopped.request();stopped.MaybeStartManualChipTest();assert(!stopped.queued);gStopLossReached=false;
 // Replay cpp_capture_20260917_114955: provider 62, local 0, generation 0.
 Harness mid;auto& ms=mid.pragmaticTables_["t"];
 ms.shoeHands=0;ms.summaryTotalGames=62;ms.shoeGeneration=0;
 ms.shoeTracked=false;ms.shoeTrusted=false;ms.strategyReady=false;ms.strategyRanks.clear();
 mid.request();mid.MaybeStartManualChipTest();assert(mid.focuses==1&&!mid.queued);
 assert(mid.pragmaticManualChipTestPending_->initialized);
 mid.betsOpen=true;mid.MaybeStartManualChipTest();
 assert(mid.queued&&mid.planningSide=="Banker"&&mid.plannedEdge<0);
 assert(mid.plannedState.shoeHands==62&&mid.plannedState.strategyRanks.size()==13);
 assert(ms.pendingStakePlan.mainStakeCents==100&&ms.pendingStakePlan.pairChipCents==20);
 assert(ms.shoeHands==0&&ms.strategyRanks.empty()&&!ms.strategyReady&&!ms.shoeTracked);
 bool assumption=false;for(const auto& line:mid.capture_.lines)assumption|=line.find("standard-eight-deck-test-assumption")!=string::npos;
 assert(assumption);
 Harness zero;zero.pragmaticTables_["t"]=ms;zero.pragmaticTables_["t"].pendingPlacementGameId.clear();
 zero.request();zero.MaybeStartManualChipTest();zero.pragmaticTables_["t"].shoeGeneration=1;
 zero.betsOpen=true;zero.MaybeStartManualChipTest();assert(!zero.queued&&!zero.pragmaticManualChipTestPending_);
 Harness reset;reset.pragmaticTables_["t"]=ms;reset.pragmaticTables_["t"].pendingPlacementGameId.clear();
 reset.request();reset.MaybeStartManualChipTest();reset.pragmaticTables_["t"].summaryTotalGames=0;
 reset.betsOpen=true;reset.MaybeStartManualChipTest();assert(!reset.queued&&!reset.pragmaticManualChipTestPending_);
 Harness unknown;unknown.pragmaticTables_["t"].shoeTracked=false;unknown.betsOpen=true;
 unknown.request();unknown.MaybeStartManualChipTest();assert(!unknown.queued);
 Harness providerEarly;providerEarly.pragmaticTables_["t"].summaryTotalGames=59;providerEarly.betsOpen=true;
 providerEarly.request();providerEarly.MaybeStartManualChipTest();assert(!providerEarly.queued);
 Harness incoherent;incoherent.pragmaticTables_["t"].summaryTotalGames=62;incoherent.betsOpen=true;
 incoherent.request();incoherent.MaybeStartManualChipTest();assert(incoherent.queued&&incoherent.planningSide=="Banker");
 Harness expired;expired.request();nowTick=92001;expired.MaybeStartManualChipTest();
 assert(!expired.queued&&!expired.pragmaticManualChipTestPending_);
}
'''

def take(start, end):
    a = source.index(start)
    return source[a:source.index(end, a)]
harness = harness.replace('PRODUCTION_STAKE_PLAN', take('    struct PragmaticStakePlan {', '    struct PragmaticTableRuntime {'))
harness = harness.replace('PRODUCTION_REQUEST_STRUCT', take('    struct ManualChipTestRequest {', '    static bool PragmaticTopKey'))
harness = harness.replace('PRODUCTION_PLANNER', take('static int NormalizePairChipCents', 'static std::optional<int> ParsePairChip') +
    take('    static constexpr int kStandardPairLimitFromHand', '    static std::string PragmaticPrettyName'))
harness = harness.replace('PRODUCTION_STRATEGY_MATH', take('    std::optional<std::pair<double,double>>\n    PragmaticStrategyMath', '    static bool StrategyMeetsThreshold'))

with temporary_directory() as tmp:
    path = Path(tmp) / 'manual_chip_test.cpp'
    path.write_text(harness, encoding='utf-8')
    exe = compile_cpp(path, Path(tmp) / 'manual_chip_test', [root / 'src'])
    subprocess.run([str(exe)], check=True, timeout=30)
print('PASS manual chip test: production worker/math/planner, mid-shoe capture replay, standard-deck assumption, immutable live state, early focus, provider count, generation-zero reset, stop/duplicate gates')
