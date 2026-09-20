"""Exercise production native betting-window acknowledgement without CDP/network."""
from pathlib import Path
from test_toolchain import temporary_directory, compile_cpp
import subprocess

root=Path(__file__).resolve().parents[1]
src=(root/'src/main.cpp').read_text(encoding='utf8')
def take(a,b):
 i=src.index(a);return src[i:src.index(b,i)]
code=r'''
#include <atomic>
#include <cassert>
#include <map>
#include <mutex>
#include <optional>
#include <string>
using namespace std;
static atomic<int> gPragmaticAutoBetMode{2};
static atomic<bool> gUnitTargetReached{false},gStopLossReached{false};
static map<string,string> values;
static optional<string> ExtractJsonString(const string&,const string& key){auto i=values.find(key);return i==values.end()?nullopt:optional<string>(i->second);}
static string JsonEscape(const string& s){return s;}
struct Harness {
 string scanRunToken_{"run"},expression;
 mutex pragmaticBetsOpenMu_,pragmaticAutoBetQueueMu_;
 map<string,string> pragmaticBetsOpenGameByTable_{{"table","game"}};
 bool pragmaticAutoBetQueueActive_=true;
 struct Request {string tableId="table",sourceGameId="game";bool manualChipTest=false;} pragmaticAutoBetActive_;
 optional<string> extractConsoleValue(const string&){return "__BAC_BET_WINDOW_PROBE__{}";}
 void SendCommand(const string& method,const string& text,const string& session){assert(method=="Runtime.evaluate"&&session=="fixture");expression=text;}
'''
code+=take('    bool PragmaticNativeBetsOpen(', '    void PragmaticFinalizePlacementAccounting(')
code+=take('    bool PragmaticAutoBetRequestActive(', '    void PragmaticQueueAutoBet(')
code+='void run(){const string fullSessionId="fixture";\n'
code+=take('        if (auto value = extractConsoleValue("__BAC_BET_WINDOW_PROBE__"))', '        if (auto value = extractConsoleValue("__BAC_PAIR_RETRY_FINISHED__"))')
code+=r'''
 }
 bool allowed(){run();return expression.find("allowed:true")!=string::npos;}
};
static void reset(){values={{"runToken","run"},{"tableid","table"},{"sourceGameId","game"},{"focusInvocation","3"},{"probeToken","1"}};gPragmaticAutoBetMode=2;gUnitTargetReached=false;gStopLossReached=false;}
int main(){
 reset();Harness open;assert(open.allowed());
 reset();Harness closed;closed.pragmaticBetsOpenGameByTable_.clear();assert(!closed.allowed());assert(closed.expression.find("allowed:false")!=string::npos);
 reset();Harness newRound;newRound.pragmaticBetsOpenGameByTable_["table"]="next";assert(!newRound.allowed());
 reset();Harness other;values["tableid"]="other";assert(!other.allowed());
 reset();Harness stale;values["runToken"]="old";assert(!stale.allowed()&&stale.expression.empty());
 reset();Harness finished;finished.pragmaticAutoBetQueueActive_=false;assert(!finished.allowed());
 reset();Harness queue;queue.pragmaticAutoBetActive_.sourceGameId="next";assert(!queue.allowed());
 reset();Harness paper;gPragmaticAutoBetMode=1;assert(!paper.allowed());
 reset();Harness manualOff;gPragmaticAutoBetMode=0;manualOff.pragmaticAutoBetActive_.manualChipTest=true;assert(manualOff.allowed());
 reset();Harness manualClosed;gPragmaticAutoBetMode=0;manualClosed.pragmaticAutoBetActive_.manualChipTest=true;manualClosed.pragmaticBetsOpenGameByTable_.clear();assert(!manualClosed.allowed());
 reset();Harness manualStopped;gPragmaticAutoBetMode=0;manualStopped.pragmaticAutoBetActive_.manualChipTest=true;gStopLossReached=true;assert(!manualStopped.allowed());
 reset();Harness stopped;gStopLossReached=true;assert(!stopped.allowed());
 reset();Harness target;gUnitTargetReached=true;assert(!target.allowed());
}
'''
with temporary_directory() as d:
 p=Path(d)/'bet_window.cpp';p.write_text(code,encoding='utf8')
 exe=compile_cpp(p,Path(d)/'bet_window')
 subprocess.run([str(exe)],check=True)
print('13 native gating cases passed: exact round, closed/new round, manual test in OFF mode, wrong table/run/queue and stops')
