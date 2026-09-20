"""Run production planners, Evolution lifecycle and Telegram sender with offline stubs."""
from pathlib import Path
import subprocess
from test_toolchain import compile_cpp, temporary_directory

root=Path(__file__).resolve().parents[1]
src=(root/'src/main.cpp').read_text(encoding='utf8')
def take(start,end):
    a=src.index(start)
    return src[a:src.index(end,a)]
def execute(label,code):
    with temporary_directory() as d:
        p=Path(d)/'test.cpp';p.write_text(code,encoding='utf8')
        exe=compile_cpp(p,Path(d)/'test',[root/'src'])
        subprocess.run([str(exe)],check=True,timeout=45)
    print('PASS '+label,flush=True)

headers=r'''
#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <cctype>
#include <cmath>
#include <cwctype>
#include <iostream>
#include <limits>
#include <optional>
#include <regex>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>
#include "confirmed_bet_accounting.h"
#include "configured_edge_model.h"
#include "signal_accounting.h"
#include "strategy_edge_thresholds.h"
using namespace std;
static atomic<int> gPairChipCents{20};
static atomic<double> gCombinedMinEdgeThreshold{.0025},gMinEdgeThreshold{.02};
static atomic<bool> gCombinedEvFilterEnabled{true},gUnitTargetReached{false},gStopLossReached{false};
static atomic<int> gSessionMinEdgeModelPnlHundredths{0},gSessionMinEdgeModelSignals{0};
static atomic<int> gSessionPositiveCombinedModelPnlHundredths{0},gSessionPositiveCombinedModelSignals{0};
static configured_edge_model::Session gSessionConfiguredCombinedModel;
static signal_accounting::Session gSessionSignalAccounting;
struct PragmaticSideBetLimitTier {int fromHand{0};int maxPercentOfMain{0};};
struct PragmaticTableRuntime {
 string name;
 bool strategyReady{true};int shoeHands{60};
 int pairPlayerMaxBetCents{50000},pairBankerMaxBetCents{50000};
 int playerMaxBetCents{500000},bankerMaxBetCents{500000},tieMaxBetCents{50000};
 vector<int> chipAmountsCents{20,100,200,500,2500,10000};
 vector<PragmaticSideBetLimitTier> pairSideBetLimits;
 unordered_map<string,int> strategyRanks;
};
static string IsoNow(){return "fixture";}
static string JsonEscape(const string& text){string out;for(char c:text){if(c=='"'||c=='\\')out+='\\';out+=c;}return out;}
static string WideToUtf8(const wstring& s){return string(s.begin(),s.end());}
static wstring FormatTelegramMoneyMinor(int n,int){return to_wstring(n);}
static bool IsExcludedBaccaratVariantName(const string& n){return n=="Super 6";}
struct Capture {vector<string> records;void WriteRaw(const string& s){records.push_back(s);}};
'''
code=headers+take('static int NormalizePairChipCents','static std::optional<int> ParsePairChip')
code+=take('static std::optional<std::string> ExtractJsonString','static std::string IsoNow')
code+=take('    struct PragmaticStakePlan {','    struct PragmaticTableRuntime {')
code+=take('    static constexpr int kStandardPairLimitFromHand','    static std::string PragmaticPrettyName')
code+=take('struct EvolutionTelegramSignalState {','struct StrategyAccumulator {')
code+='struct Harness {\n'+take('    struct EvolutionModelState {','    #include "evolution_chip_test_methods.h"')+r'''
 atomic<bool> evolutionSessionRecoveryActive_{false};
 unordered_map<string,EvolutionModelState> evolutionModels_;
 unordered_map<string,EvolutionTelegramSignalState> evolutionTelegramSignals_;
 Capture capture_;string signal;bool available=false;
 void PostTableStrategy(const string&,bool a,double,double,const string& s){available=a;signal=s;}
};
static PragmaticTableRuntime fresh(){
 PragmaticTableRuntime st;
 for(const char* r:{"A","2","3","4","5","6","7","8","9","10","J","Q","K"})st.strategyRanks[r]=32;
 return st;
}
static string status(const string& gid,int hands=60,bool allZero=false,const string& phase="BetsOpen",int age=0,bool trusted=true){
 string ranks="{";bool first=true;
 for(const char* r:{"A","2","3","4","5","6","7","8","9","10","J","Q","K"}){
  if(!first)ranks+=",";first=false;ranks+="\""+string(r)+"\":"+to_string(!allZero||string(r)=="10"?32:0);
 }
 ranks+="}";
 return "{\"tableName\":\"Baccarat\",\"gameId\":\""+gid+"\",\"shoeHands\":"+to_string(hands)+
 ",\"remainingRanksJson\":\""+JsonEscape(ranks)+"\",\"shoeTracked\":true,\"shoeTrusted\":"+(trusted?"true":"false")+
 ",\"transportAgeMs\":"+to_string(age)+",\"betting\":\""+phase+"\",\"dealing\":\""+(phase=="Finished"?"Finished":"")+"\"}";
}
static string result(const string& gid,const string& winner){return "{\"gameId\":\""+gid+"\",\"result\":{\"winner\":\""+winner+"\"}}";}
int main(){
 // Production EV, all three candidates, exact payout and total-stake weighting.
 auto st=fresh();auto ev=PragmaticComputeMainBetEv(st);
 assert(abs(ev.tie-(9*ev.tieProbability-1))<1e-12);
 assert(abs(ev.tie-(-.1435963))<.00002);
 auto plan=PragmaticBuildStakePlan(st,.04);
 assert(plan.valid&&plan.mainSide=="Banker"&&plan.mainStakeCents==100);
 bool foundPlayer=false;
 for(const char* removed:{"A","2","3","4","5","6","7","8","9"}){
  auto candidate=fresh();candidate.strategyRanks[removed]=0;
  const auto candidateEv=PragmaticComputeMainBetEv(candidate);
  const auto candidatePlan=PragmaticBuildStakePlan(candidate,.04);
  assert(candidatePlan.valid);
  assert(candidatePlan.selectedMainEv==max({candidateEv.player,candidateEv.banker,candidateEv.tie}));
  foundPlayer=foundPlayer||candidatePlan.mainSide=="Player";
 }
 assert(foundPlayer);
 for(auto& item:st.strategyRanks)item.second=item.first=="10"?32:0;
 ev=PragmaticComputeMainBetEv(st);assert(ev.tieProbability==1&&ev.tie==8);
 plan=PragmaticBuildStakePlan(st,.04);assert(plan.valid&&plan.mainSide=="Tie");
 assert(plan.tieMainEv==8&&plan.totalStakeUnits==7);
 assert(abs(plan.combinedEdge-(.08+40)/7)<1e-12);
 assert(PragmaticModelRoundPnlHundredths(plan,false,false,"tie")==3800);
 assert(PragmaticModelRoundPnlHundredths(plan,true,false,"banker")==500);
 for(const string side:{"Player","Banker","Tie"})for(const string winner:{"player","banker","tie"}){
  const int want=side=="Tie"?(winner=="tie"?4000:-500):winner=="tie"?0:
      side=="Player"?(winner=="player"?500:-500):(winner=="banker"?475:-500);
  assert(confirmed_bet_accounting::MainNetHundredths(side,winner,500)==want);
  assert(confirmed_bet_accounting::MainReturnedHundredths(side,winner,500)==500+want);
 }
 st.shoeHands=59;assert(!PragmaticBuildStakePlan(st,.04).mainRequired);
 st.shoeHands=60;st.tieMaxBetCents=80;assert(!PragmaticBuildStakePlan(st,.04).valid);
 st=fresh();st.chipAmountsCents.clear();gPairChipCents=1000;
 const auto manual=PragmaticBuildStakePlan(st,.04,true);
 assert(manual.valid&&manual.mainStakeCents==5000&&manual.mainChipClicks==0&&manual.pairChipClicks==0);
 assert(!PragmaticBuildStakePlan(st,.04).valid);gPairChipCents=20;
 // Explicit chip-test planner bypasses negative Pair/combined EV, while
 // retaining exact stakes and UI-verifiable chip denominations.
 auto testPlan=PragmaticBuildStakePlan(st,-.20,false,true);
 assert(testPlan.valid&&testPlan.mainRequired&&testPlan.mainStakeCents==100);
 assert(testPlan.mainChipCents==100&&testPlan.mainChipClicks==1);
 assert(testPlan.pairChipDenomCents==20&&testPlan.pairChipClicks==1);
 assert(!testPlan.combinedMinEdgeMet);
 st.pairSideBetLimits={{70,10}};
 testPlan=PragmaticBuildStakePlan(st,-.20,false,true);
 assert(testPlan.valid&&testPlan.mainRequired&&testPlan.mainStakeCents==100);
 st.shoeHands=59;
 assert(!PragmaticBuildStakePlan(st,-.20,false,true).mainRequired);

 // Evolution live filter vs independent, frozen comparison models.
 Harness h;gCombinedMinEdgeThreshold=.005;
 h.EvolutionUpdateStrategy(status("one"),"table",.086,.04);
 assert(h.signal=="NICHT SETZEN: Gesamt-MinEdge"&&h.evolutionModels_["table"].armed);
 assert(h.evolutionTelegramSignals_.empty());
 auto p=h.EvolutionSettleModel(result("one","Banker"),"table",false,false);
 assert(p&&gSessionMinEdgeModelSignals==1&&gSessionMinEdgeModelPnlHundredths==275);
 assert(gSessionConfiguredCombinedModel.Read().signals==0);
 assert(!h.EvolutionSettleModel(result("one","Banker"),"table",false,false));
 h.EvolutionUpdateStrategy(status("one"),"table",.086,.04); // stale open cannot rearm resolved hand.
 assert(!h.evolutionModels_["table"].armed);

 gCombinedEvFilterEnabled=false;gCombinedMinEdgeThreshold=.0025;
 h.EvolutionUpdateStrategy(status("two"),"table",.085,.02);
 assert(h.signal.rfind("SETZEN: ZUERST Banker",0)==0);
 assert(h.evolutionTelegramSignals_["table"].targetGameId=="two");
 assert(h.evolutionModels_["table"].plan.combinedEdge<0);
 gCombinedMinEdgeThreshold=-.1; // Later setting must not change frozen eligibility.
 p=h.EvolutionSettleModel(result("two","Player"),"table",false,false);
 assert(p&&!p->combinedMinEdgeMet);
 assert(gSessionMinEdgeModelSignals==2&&gSessionMinEdgeModelPnlHundredths==-425);
 assert(gSessionConfiguredCombinedModel.Read().signals==0);
 gCombinedMinEdgeThreshold=.0025;gCombinedEvFilterEnabled=true;
 h.EvolutionUpdateStrategy(status("three",60,true),"table",1,11);
 assert(h.signal.rfind("SETZEN: ZUERST Tie",0)==0);
 assert(!h.EvolutionSettleModel(result("old","Tie"),"table",true,true));
 assert(!h.EvolutionSettleModel(result("three","unknown"),"table",true,true));
 p=h.EvolutionSettleModel(result("three","Tie"),"table",true,true);
 assert(p&&gSessionConfiguredCombinedModel.Read().pnlHundredths==6200);
 assert(gSessionConfiguredCombinedModel.Read().signals==1);
 const int prior=gSessionMinEdgeModelSignals;
 Harness preview;
 preview.EvolutionUpdateStrategy(status("finished",60,true,"Finished"),"t",1,11);
 assert(!preview.evolutionModels_["t"].armed); // Never retrospectively bet resolved cards.
 assert(!preview.EvolutionSettleModel(result("finished","Tie"),"t",true,true));
 assert(gSessionMinEdgeModelSignals==prior);
 for(const auto payload:{status("stale",60,true,"BetsOpen",5001),status("untrusted",60,true,"BetsOpen",0,false),status("unknownHands",-1,true)}){
  Harness bad;bad.EvolutionUpdateStrategy(payload,"t",1,11);assert(!bad.available&&bad.signal=="NICHT SETZEN");assert(!bad.evolutionModels_["t"].armed);
 }
 Harness lowPair;lowPair.EvolutionUpdateStrategy(status("low",60,true),"t",.08,.01999);
 assert(lowPair.signal=="NICHT SETZEN"&&!lowPair.evolutionModels_["t"].armed);
 Harness earlier;earlier.EvolutionUpdateStrategy(status("early",59),"t",.086,.04);
 assert(earlier.signal=="SETZEN: PLAYER + BANKER PAIR"&&!earlier.evolutionModels_["t"].plan.mainRequired);
 assert(!h.capture_.records.empty());
 cout<<"Production Tie EV/payouts, 60:20 amounts, Evolution filter ON/OFF, frozen export models and lifecycle OK\n";
}
'''
execute('production Tie and Evolution integration',code)

# Detached worker is controlled deterministically: never call Telegram/network.
# Stub std::thread executes on detach so the real lambda checks are exercised.
telegram=r'''
#include <atomic>
#include <cassert>
#include <functional>
#include <iostream>
#include <string>
#include <regex>
#include <vector>
using namespace std;
static atomic<bool> gTelegramSignalEnabled{false};
static bool disableBeforeWorker=false,disableInResolve=false,master=true;
static int sends=0,resolves=0;
namespace std {class thread {function<void()> work;public:template<class F>thread(F f):work(f){}void detach(){if(disableBeforeWorker)gTelegramSignalEnabled=false;work();}};}
using HWND=int;
struct TelegramConfig {bool enabled=true;string botToken="fixture";};
static TelegramConfig LoadTelegramConfig(){return {master,"fixture"};}
static void PostTelegramLog(HWND,const wstring&){}
static string ResolveTelegramChatId(TelegramConfig&){++resolves;if(disableInResolve)gTelegramSignalEnabled=false;return "fixture-chat";}
static string apiResponse=R"({"ok":true,"result":{"message_id":123}})";
static vector<string> delivery;
static void SaveTelegramDelivery(HWND,const wstring&,const string& status,const string& id=""){delivery.push_back(status+"|"+id);}
static bool TelegramApiPost(const string&,const wchar_t*,const string&,string& response){++sends;response=apiResponse;return true;}
static string JsonEscape(const string& s){return s;}
static string WideToUtf8(const wstring& s){return string(s.begin(),s.end());}
static string IsoNow(){return "fixture";}
enum class ProviderMode{Evolution,PragmaticPlay};
struct Capture{int logs=0;void WriteRaw(const string&){++logs;}};
'''+take('static void QueueTelegramMessage','static std::wstring TelegramCurrencyLabel')+'struct Harness {\n'+take('    void MaybeQueueTelegramPragmaticSessionStart','    std::string PragmaticStatus')+r'''
 bool startupPrepareOnly_=false;ProviderMode provider_=ProviderMode::PragmaticPlay;
 atomic<bool> pragmaticMultiplayEverReady_{true},pragmaticMultiplayRealGameFrameSeen_{true},telegramPragmaticSessionStartSent_{false};
 Capture capture_;HWND hwnd_=0;
};
int main(){
 Harness off;off.MaybeQueueTelegramPragmaticSessionStart("ready");assert(sends==0&&resolves==0&&!off.telegramPragmaticSessionStartSent_);
 gTelegramSignalEnabled=true;Harness on;on.MaybeQueueTelegramPragmaticSessionStart("ready");assert(sends==1&&resolves==1);on.MaybeQueueTelegramPragmaticSessionStart("again");assert(sends==1);
 Harness notReady;notReady.pragmaticMultiplayRealGameFrameSeen_=false;notReady.MaybeQueueTelegramPragmaticSessionStart("no-frame");assert(sends==1);
 disableBeforeWorker=true;Harness queued;queued.MaybeQueueTelegramPragmaticSessionStart("ready");assert(sends==1&&resolves==1);
 disableBeforeWorker=false;gTelegramSignalEnabled=true;disableInResolve=true;Harness during;during.MaybeQueueTelegramPragmaticSessionStart("ready");assert(sends==1&&resolves==2);
 disableInResolve=false;QueueTelegramSignalResult(0,L"off-result");assert(sends==1);
 QueueTelegramMessage(0,L"existing target/stoploss notification");assert(sends==2);
 assert(delivery.back()=="api-accepted|123");
 master=false;gTelegramSignalEnabled=true;Harness disabled;disabled.MaybeQueueTelegramPragmaticSessionStart("ready");assert(sends==2);
 QueueTelegramMessage(0,L"configuration disabled");assert(sends==2);
 assert(delivery.back()=="not-sent-configuration|");
 master=true;apiResponse=R"({"ok":false,"description":"fixture failure"})";QueueTelegramMessage(0,L"failure");assert(delivery.back()=="delivery-unconfirmed|");
 apiResponse=R"({"ok":true,"result":{}})";QueueTelegramMessage(0,L"missing message ID");assert(delivery.back()=="delivery-unconfirmed|");
 cout<<"Telegram OFF/ON, worker cancellation, master switch, readiness and deduplication OK (offline stubs)\n";
}
'''
execute('production Telegram start and worker',telegram)

# Wiring assertions cover the native UI/transport boundaries not compiled above.
assert 'remainingRanksJson:st.remainingRanks?JSON.stringify(st.remainingRanks):null' in src
assert 'if(st.shoeTracked&&Number.isInteger(st.shoeHands))++st.shoeHands;' in src
assert 'st.shoeHands=officialCardsOut===0?0:null;' in src
assert src.count('evolutionModels_.erase(*tid);')==2
assert 'EvolutionUpdateStrategy(payload, *tableId, lpProbability, lpEdge);' in src
assert 'EvolutionSettleModel(payload, *tableId, playerPair, bankerPair);' in src
assert 'Model comparison is available for Pragmatic and Evolution.' in src
assert src.count('EnableWindow(a->combinedMinEdgeEdit, TRUE);')==4
assert 'EnableWindow(a->combinedEvFilterBtn, TRUE);' in src
assert '(mainSide == "Player" || mainSide == "Banker" || mainSide == "Tie")' in src
assert 'operation.mainPrepared=true;' in src
assert "if(!nativeDispatchOk||!mainConfirmed){finishRetry(" in src
assert 'const bool signalWon = handPnlHundredths > 0;' in src
assert 'const bool mainPush = result == "tie" && st.telegramSignalMainSide != "Tie";' in src
print('PASS provider UI, transport snapshot, main-first confirmation and export wiring')
