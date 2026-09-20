from pathlib import Path
import subprocess
from test_toolchain import compile_cpp, temporary_directory
root=Path(__file__).resolve().parents[1]
source=(root/'src/main.cpp').read_text(encoding='utf-8-sig')
start=source.index('    void MaybeRecoverPragmaticMultiplayReadiness() {')
method=source[start:source.index('    std::string EvolutionSessionWatchScript()',start)]
code=r'''
#include "connection_health.h"
#include <atomic>
#include <cassert>
#include <chrono>
#include <map>
#include <set>
#include <string>
#include <vector>
#include <iostream>
using namespace std;
using ULONGLONG=unsigned long long;
static ULONGLONG clockTick=1000;
ULONGLONG GetTickCount64(){return clockTick;}
string IsoNow(){return "offline";}
enum class ProviderMode{PragmaticPlay,Evolution};
struct Harness {
 ProviderMode provider_=ProviderMode::PragmaticPlay;
 bool startupPrepareOnly_=false;
 atomic<bool> pragmaticMultiplayEverReady_{false},pragmaticMultiplayRealGameFrameSeen_{true};
 atomic<bool> pragmaticReadinessRecoveryActive_{false},pragmaticMultiplayConflict_{false};
 atomic<bool> pragmaticRecoveryAutomatic_{false},pragmaticReadinessNeedsCardProof_{false};
 atomic<int> pragmaticRecoveryStage_{0};
 atomic<ULONGLONG> pragmaticRecoveryStartedTick_{0},pragmaticConflictLastReloadTick_{0},pragmaticConflictReloadPendingTick_{0};
 atomic<ULONGLONG> pragmaticMultiplayLastReadyTick_{0},pragmaticMultiplayLastMainReadyTick_{0};
 atomic<ULONGLONG> pragmaticMultiplayLastLiveFrameTick_{1000},pragmaticMultiplayLastCardFrameTick_{1000};
 atomic<ULONGLONG> pragmaticMultiplayLastReadinessRecoveryTick_{0};
 struct Counts {atomic<int> pragmaticRecoveryStage{0};atomic<bool> pragmaticRecoveryAutomatic{false};}counters_;
 struct State{int shoeHands=10;};map<string,State> pragmaticTables_;
 set<string> pragmaticMainTableIds_,pragmaticExcludedTableIds_;
 chrono::steady_clock::time_point lastCardScan_;
 struct Capture{vector<string> lines;void WriteRaw(string s){lines.push_back(s);}}capture_;
 int invalidations=0,sessionInvalidations=0;vector<string> commands;
 void Log(const wstring&){}
 string PragmaticCurrentBetifyPageSession(){return "owner";}
 void PragmaticSetMultiplayConflict(const string&){pragmaticMultiplayConflict_=true;}
 void PragmaticInvalidateForSessionLoss(const char*){sessionInvalidations++;}
 void PragmaticInvalidateForMultiplayFeedStall(const char*){invalidations++;}
 void SendCommand(const char* cmd,const char*,const string&){commands.push_back(cmd);}
 bool CardProof(ULONGLONG started){const ULONGLONG nowTick=clockTick;CARD_PROOF return freshCardProof;}
 PRODUCTION
};
int main(){
 Harness absent;absent.pragmaticMultiplayRealGameFrameSeen_=false;clockTick=90000;
 absent.MaybeRecoverPragmaticMultiplayReadiness();assert(absent.invalidations==0);
 Harness unarmed;unarmed.startupPrepareOnly_=true;unarmed.MaybeRecoverPragmaticMultiplayReadiness();assert(unarmed.invalidations==0);
 Harness missingUi;clockTick=12999;missingUi.MaybeRecoverPragmaticMultiplayReadiness();assert(missingUi.invalidations==0);
 clockTick=13000;missingUi.MaybeRecoverPragmaticMultiplayReadiness();
 assert(missingUi.invalidations==1&&missingUi.pragmaticRecoveryStage_==5);
 assert(missingUi.commands.empty());assert(missingUi.capture_.lines.back().find("game-data-stale")!=string::npos);
 cout<<"PASS outage at 12 s without any DOM readiness; healthy/startup boundaries\n";
 clockTick=27999;missingUi.MaybeRecoverPragmaticMultiplayReadiness();assert(missingUi.commands.empty());
 clockTick=28000;missingUi.MaybeRecoverPragmaticMultiplayReadiness();
 assert(missingUi.commands.size()==1&&missingUi.commands[0]=="Page.reload");assert(missingUi.sessionInvalidations==1);
 cout<<"PASS controlled recovery escalates once after 15 s\n";
 Harness timers;for(int i=0;i<5;i++)timers.pragmaticTables_[to_string(i)]={};
 clockTick=45999;timers.pragmaticMultiplayLastLiveFrameTick_=clockTick;
 timers.MaybeRecoverPragmaticMultiplayReadiness();assert(timers.invalidations==0);
 clockTick=46000;timers.pragmaticMultiplayLastLiveFrameTick_=clockTick;
 timers.MaybeRecoverPragmaticMultiplayReadiness();assert(timers.invalidations==1&&timers.pragmaticReadinessNeedsCardProof_);
 assert(timers.capture_.lines.back().find("card-data-stale")!=string::npos);
 cout<<"PASS continued timer/status traffic does not conceal missing cards at 45 s\n";
 Harness few;for(int i=0;i<4;i++)few.pragmaticTables_[to_string(i)]={};
 few.pragmaticMultiplayLastLiveFrameTick_=clockTick;few.MaybeRecoverPragmaticMultiplayReadiness();assert(few.invalidations==0);
 Harness fresh;fresh.pragmaticMultiplayLastLiveFrameTick_=clockTick;fresh.pragmaticMultiplayLastCardFrameTick_=clockTick;
 fresh.MaybeRecoverPragmaticMultiplayReadiness();assert(fresh.invalidations==0);
 Harness cooldown;cooldown.pragmaticMultiplayLastReadinessRecoveryTick_=clockTick-29999;
 cooldown.MaybeRecoverPragmaticMultiplayReadiness();assert(cooldown.invalidations==0);
 Harness conflict;conflict.pragmaticMultiplayConflict_=true;conflict.MaybeRecoverPragmaticMultiplayReadiness();assert(conflict.invalidations==0);
 cout<<"PASS small table count, healthy traffic, cooldown and recovery ownership\n";
 assert(!connection_health::Evaluate(100,0,0,200,200,5).Recover());
 assert(!connection_health::Evaluate(50000,0,0,0,0,5).Recover());
 assert(connection_health::Evaluate(50000,1000,49000,49000,49000,5).domStale);
 cout<<"PASS missing observations, clock boundary and separate UI failure\n";
 Harness proof;proof.pragmaticReadinessNeedsCardProof_=true;
 clockTick=50000;proof.pragmaticMultiplayLastCardFrameTick_=0;assert(!proof.CardProof(46000));
 proof.pragmaticMultiplayLastCardFrameTick_=45000;assert(!proof.CardProof(46000));
 proof.pragmaticMultiplayLastCardFrameTick_=48000;assert(proof.CardProof(46000));
 proof.pragmaticMultiplayLastCardFrameTick_=46000;assert(!proof.CardProof(46000));
 proof.pragmaticReadinessNeedsCardProof_=false;assert(proof.CardProof(46000));
 cout<<"PASS card-loss recovery requires a new, recent card/result instead of timer traffic\n";
}
'''.replace('PRODUCTION',method)
proof_start=source.index('                        const ULONGLONG cardTick = pragmaticMultiplayLastCardFrameTick_')
code=code.replace('CARD_PROOF',source[proof_start:source.index('                        if (!freshGameProof || !freshCardProof)',proof_start)])
with temporary_directory() as d:
    p=Path(d)/'health.cpp';p.write_text(code,encoding='utf-8')
    exe=compile_cpp(p,Path(d)/'health',[root/'src'])
    subprocess.run([str(exe)],check=True,timeout=30)
    # Stub only the OS call to exercise the actual RAII lifetime without changing
    # the test machine's sleep settings.
    (Path(d)/'windows.h').write_text('''#pragma once
using EXECUTION_STATE=unsigned long;
constexpr EXECUTION_STATE ES_CONTINUOUS=0x80000000,ES_SYSTEM_REQUIRED=1;
EXECUTION_STATE SetThreadExecutionState(EXECUTION_STATE);
''')
    p=Path(d)/'power.cpp';p.write_text(r'''
#include "monitor_awake.h"
#include <vector>
#include <cassert>
std::vector<EXECUTION_STATE> calls;bool fail=false;
EXECUTION_STATE SetThreadExecutionState(EXECUTION_STATE s){calls.push_back(s);return fail?0:ES_CONTINUOUS;}
int main(){
 {MonitorAwake off(false);assert(!off.Held());}assert(calls.empty());
 {MonitorAwake guard(true);assert(guard.Held());}
 assert(calls.size()==2&&calls[0]==(ES_CONTINUOUS|ES_SYSTEM_REQUIRED)&&calls[1]==ES_CONTINUOUS);
 calls.clear();try{MonitorAwake guard(true);throw 1;}catch(int){}assert(calls.size()==2);
 calls.clear();fail=true;{MonitorAwake guard(true);assert(!guard.Held());}assert(calls.size()==1);
}
''')
    exe=compile_cpp(p,Path(d)/'power',[Path(d),root/'src'])
    subprocess.run([str(exe)],check=True,timeout=30)
print('PASS sleep guard release on normal/exception exit, disabled startup and OS failure')
assert source.count('pragmaticMultiplayLastCardFrameTick_.store(0')==2
assert 'if (!freshGameProof || !freshCardProof)' in source
assert 'HandleGameSocketFailure(json);' in source
close=source[source.index('    void HandleGameSocketFailure('):source.index('    void HandleFrameEvent(')]
assert 'Network.webSocketClosed' in close and 'Network.webSocketFrameError' in close
assert 'RedactSensitiveText' in close and 'InvalidateFor' not in close and 'Page.reload' not in close
flags=(root/'start_chrome_debug.bat').read_text()
for flag in ['disable-background-timer-throttling','disable-renderer-backgrounding','disable-backgrounding-occluded-windows']:
    assert flag in flags
assert flags.count('%MONITOR_FLAGS%')==2
print('PASS runtime integration, card recovery proof, socket diagnostics and dedicated Chrome flags')
