from pathlib import Path
import subprocess
from test_toolchain import compile_cpp,temporary_directory
r=Path(__file__).resolve().parents[1]
generator=(r/'tests/validate_v111_tie_evolution_telegram.py').read_text(encoding='utf-8')
ns={'__file__':str(r/'tests/validate_v111_tie_evolution_telegram.py')}
exec(generator[:generator.index("execute('production Tie and Evolution integration'")],ns)
code=ns['code'];code=code[:code.index('int main(){')]
code=code.replace('using namespace std;', '''using namespace std;
#include <unordered_set>
using ULONGLONG=unsigned long long;
static ULONGLONG GetTickCount64(){return 100000;}
static atomic<int> gPragmaticAutoBetMode{2};
enum class ProviderMode{Evolution,PragmaticPlay};''',1)
methods=(r/'src/evolution_chip_test_methods.h').read_text().split('// Included inside CdpMonitor')[0]
members=r'''
 ProviderMode provider_=ProviderMode::Evolution;bool startupPrepareOnly_=false;
 atomic<bool> evolutionSessionExpiredPending_{false};ULONGLONG evolutionWidgetRecoveryTick_=0;
 struct ManualChipTestRequest {string tableId;ULONGLONG requestedTick;uint64_t shoeGeneration;bool waitLogged;bool evolutionSignal=false;string targetGameId,mainSide;int mainCents=500,pairCents=100;};
 mutex pragmaticManualChipTestMu_;optional<ManualChipTestRequest> pragmaticManualChipTestPending_;
 unordered_set<string> evolutionSignalAttempted_;
'''
code=code.replace('struct Harness {','struct Harness {\n'+members+methods,1)
code+=r'''
string packet(const string& gid,double edge){auto s=status(gid);s.pop_back();return s+",\"luckyPairEdge\":"+to_string(edge)+"}";}
int main(){
 gPairChipCents=100;gMinEdgeThreshold=.02;gCombinedMinEdgeThreshold=.0025;gCombinedEvFilterEnabled=true;
 Harness h;auto p=packet("one",.06);h.EvolutionUpdateStrategy(p,"t",.09,.06);
 gPragmaticAutoBetMode=0;h.MaybeQueueEvolutionSignal(p,"t");assert(!h.pragmaticManualChipTestPending_);
 gPragmaticAutoBetMode=2;gCombinedMinEdgeThreshold=.20;h.MaybeQueueEvolutionSignal(p,"t");assert(!h.pragmaticManualChipTestPending_);
 gCombinedMinEdgeThreshold=.0025;h.MaybeQueueEvolutionSignal(p,"t");assert(h.pragmaticManualChipTestPending_);
 auto request=*h.pragmaticManualChipTestPending_;assert(request.mainCents==500&&request.pairCents==100&&request.targetGameId=="one"&&request.evolutionSignal);
 h.pragmaticManualChipTestPending_.reset();h.MaybeQueueEvolutionSignal(p,"t");assert(!h.pragmaticManualChipTestPending_);
 p=packet("two",.06);h.EvolutionUpdateStrategy(p,"t",.09,.06);h.evolutionWidgetRecoveryTick_=1;h.MaybeQueueEvolutionSignal(p,"t");assert(!h.pragmaticManualChipTestPending_);
 h.evolutionWidgetRecoveryTick_=0;h.evolutionModels_["t"].shoe.strategyReady=false;h.MaybeQueueEvolutionSignal(p,"t");assert(!h.pragmaticManualChipTestPending_);
 gSessionSignalAccounting.Reset();request.mainSide="Banker";h.evolutionWagerCandidates_["t|one"]=request;
 const string accepted=R"({"tableId":"t","gameId":"one","Player":0,"Banker":500,"Tie":0,"PlayerPair":100,"BankerPair":100})";
 h.RecordEvolutionAcceptedWager(accepted);h.RecordEvolutionAcceptedWager(accepted);
 assert(gSessionSignalAccounting.Read().ActualTotal()==-700);
 h.SettleEvolutionAcceptedWager(result("wrong","Banker"),"t",false,false);assert(gSessionSignalAccounting.Read().ActualTotal()==-700);
 const auto settled=h.SettleEvolutionAcceptedWager(result("one","Banker"),"t",false,false);assert(gSessionSignalAccounting.Read().ActualTotal()==275);
 assert(settled && settled->Total()==275 && settled->pairPnlHundredths==-200 && settled->mainPnlHundredths==475);
 assert(settled->bet.mainCents==500 && settled->bet.playerPairCents==100 && settled->bet.bankerPairCents==100);
 assert(!h.SettleEvolutionAcceptedWager(result("one","Banker"),"t",false,false));assert(gSessionSignalAccounting.Read().ActualTotal()==275);
 request.mainSide="Tie";h.evolutionWagerCandidates_["t|tie"]=request;
 h.RecordEvolutionAcceptedWager(R"({"tableId":"t","gameId":"tie","Player":0,"Banker":0,"Tie":500,"PlayerPair":100,"BankerPair":100})");
 h.SettleEvolutionAcceptedWager(result("tie","Tie"),"t",true,true);assert(gSessionSignalAccounting.Read().ActualTotal()==275+6200);
 gSessionSignalAccounting.Reset();request.mainSide="Player";h.evolutionWagerCandidates_["t|partial"]=request;
 h.RecordEvolutionAcceptedWager(R"({"tableId":"t","gameId":"partial","Player":500,"Banker":0,"Tie":0,"PlayerPair":0,"BankerPair":0})");
 assert(gSessionSignalAccounting.Read().ActualTotal()==-500);
 h.SettleEvolutionAcceptedWager(result("partial","Player"),"t",true,true);assert(gSessionSignalAccounting.Read().ActualTotal()==500);
 h.evolutionWagerCandidates_["t|cancel"]=request;
 h.RecordEvolutionAcceptedWager(R"({"tableId":"t","gameId":"cancel","Player":500,"Banker":0,"Tie":0,"PlayerPair":100,"BankerPair":0})");
 assert(gSessionSignalAccounting.Read().ActualTotal()==-100);
 h.RecordEvolutionAcceptedWager(R"({"tableId":"t","gameId":"cancel","Player":0,"Banker":0,"Tie":0,"PlayerPair":0,"BankerPair":0})");
 assert(gSessionSignalAccounting.Read().ActualTotal()==500);
 cout<<"PASS production signal mode, edge filters, one request per round, recovery/untrusted guards, confirmed Banker/Tie/partial settlement, cancellation and deduplication\n";
}
'''
with temporary_directory() as d:
 p=Path(d)/'placement.cpp';p.write_text(code,encoding='utf-8');exe=compile_cpp(p,Path(d)/'placement',[r/'src']);subprocess.run([str(exe)],check=True,timeout=45)
