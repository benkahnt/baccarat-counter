"""Offline checks using the production validator and rejection method."""
from pathlib import Path
import json
import subprocess
import sys
from test_toolchain import compile_cpp, temporary_directory

root = Path(__file__).resolve().parents[1]
source = (root/'src/main.cpp').read_text(encoding='utf-8-sig')
start = source.index('    void PragmaticRejectInconsistentResult(')
method = source[start:source.index('    void PragmaticResetGame(', start)]
code = r'''
#include "pragmatic_hand_integrity.h"
#include <atomic>
#include <cassert>
#include <fstream>
#include <iostream>
#include <map>
#include <mutex>
#include <sstream>
using namespace std;
string IsoNow(){return "offline";}
string JsonEscape(const string& s){return s;}
wstring Utf8ToWide(const string& s){return wstring(s.begin(),s.end());}
struct PragmaticStakePlan{bool valid=false;};
struct PragmaticTableRuntime {
 string name="fixture",realMainBetGameId,armedSignalGameId,pendingPlacementGameId;
 string pendingSignalSourceGameId,comparisonGameId,lastRejectedResultGameId,phase;
 string telegramSignalTargetGameId;
 int telegramSignalAutoBetMode=2,telegramSignalConfirmedPairMask=0;
 bool realMainBetSettled=false,armedSignalIsActual=false,resultAccountingUncertain=false;
 bool shoeTrusted=true,pendingEndTrusted=true,strategyReady=true,pendingSignalForBetsOpen=true,telegramSignalPending=true;
 int realMainBetStakeCents=0,armedSignalPairMask=0,pendingPlacementConfirmedPairMask=0;
 PragmaticStakePlan pendingStakePlan,comparisonStakePlan;
 vector<string> playerCards{"KC","5D","8H"},bankerCards{"8H","2S","5D"};
};
struct Harness {
 mutex pragmaticBetsOpenMu_;
 map<string,string> pragmaticBetsOpenGameByTable_{{"table","game"}};
 struct {atomic<int> pragmaticHandsIncomplete{0};} counters_;
 struct {vector<string> lines;void WriteRaw(string s){lines.push_back(s);}} capture_;
 void Log(const wstring&){}
 string PragmaticJsonCards(const vector<string>&){return "[]";}
 void PragmaticClearPendingPlacement(PragmaticTableRuntime& s){s.pendingPlacementGameId.clear();s.pendingPlacementConfirmedPairMask=0;}
 METHOD
};
vector<string> split(string s){vector<string> out;istringstream in(s);while(getline(in,s,','))out.push_back(s);return out;}
int main(int argc,char** argv){
 using namespace pragmatic_hand_integrity;
 auto bad=Check({"KC","5D","8H"},{"8H","2S","5D"},"player");
 assert(!bad.valid&&bad.playerPoints==3&&bad.bankerPoints==5&&bad.reason=="cards-winner-mismatch");
 assert(Check({"4H","4D"},{"7C","7S"},"player").valid);
 assert(Check({"AH","9D"},{"KC","QS"},"tie").valid);
 assert(Check({"10H","AD"},{"2C","QS"},"banker").valid);
 assert(!Check({"AH","2D","3S","4C"},{"2C","QS"},"player").valid);
 assert(!Check({"KH","KD","KH","5S"},{"JD","AC","JD","9D"},"banker").valid);
 assert(!Check({"?H","AD"},{"2C","QS"},"banker").valid);
 assert(!Check({"10H","AD"},{"2C","QS"},"").valid);
 assert(!Check({"10H"},{"2C","QS"},"banker").valid);
 Harness h;PragmaticTableRuntime s;s.pendingStakePlan.valid=true;s.comparisonGameId="game";
 h.PragmaticRejectInconsistentResult("table",s,"game","player",bad);
 assert(!s.shoeTrusted&&!s.pendingEndTrusted&&!s.strategyReady&&!s.pendingSignalForBetsOpen);
 assert(!s.pendingStakePlan.valid&&s.comparisonGameId.empty()&&!s.telegramSignalPending);
 assert(h.pragmaticBetsOpenGameByTable_.empty()&&!s.resultAccountingUncertain);
 h.PragmaticRejectInconsistentResult("table",s,"game","player",bad);
 assert(h.capture_.lines.size()==1&&h.counters_.pragmaticHandsIncomplete==1);
 Harness real;PragmaticTableRuntime funded;
 funded.realMainBetGameId="game";funded.realMainBetStakeCents=100;
 funded.armedSignalGameId="game";funded.armedSignalPairMask=3;funded.armedSignalIsActual=true;
 real.PragmaticRejectInconsistentResult("table",funded,"game","player",bad);
 assert(funded.resultAccountingUncertain&&funded.realMainBetStakeCents==100);
 assert(funded.armedSignalPairMask==3&&funded.armedSignalGameId=="game"&&funded.telegramSignalPending);
 funded.shoeTrusted=true;funded.strategyReady=true;
 real.PragmaticRejectInconsistentResult("table",funded,"later","player",bad);
 assert(funded.resultAccountingUncertain&&!funded.shoeTrusted);
 Harness partial;PragmaticTableRuntime pending;pending.pendingPlacementGameId="game";pending.pendingPlacementConfirmedPairMask=1;
 partial.PragmaticRejectInconsistentResult("table",pending,"game","player",bad);
 assert(pending.resultAccountingUncertain&&pending.pendingPlacementConfirmedPairMask==1);
 Harness overflow;PragmaticTableRuntime cleared;
 cleared.telegramSignalTargetGameId="game";cleared.telegramSignalConfirmedPairMask=3;
 overflow.PragmaticRejectInconsistentResult("table",cleared,"game","player",bad);
 assert(cleared.resultAccountingUncertain&&cleared.telegramSignalConfirmedPairMask==3);
 if(argc>1){ifstream input(argv[1]);string p,b,w;int expected,count=0,rejected=0;
  while(input>>p>>b>>w>>expected){auto r=Check(split(p),split(b),w);assert(r.valid==bool(expected));++count;if(!r.valid)++rejected;}
  cout<<"PASS capture replay: "<<count<<" hands, "<<rejected<<" rejected\n";
 }
 cout<<"PASS score/count validation, invalidation, funded-state preservation, duplicate diagnostics\n";
}
'''.replace('METHOD',method)

with temporary_directory() as directory:
    directory=Path(directory)
    cpp=directory/'integrity.cpp';cpp.write_text(code,encoding='utf-8')
    exe=compile_cpp(cpp,directory/'integrity',[root/'src'])
    args=[str(exe)]
    if len(sys.argv)>1:
        fixture=directory/'capture.txt';rows=[]
        with open(sys.argv[1],encoding='utf-8',errors='replace') as capture:
            for line in capture:
                o=json.loads(line)
                if o.get('kind') not in ['PRAGMATIC_HAND_COMPLETE','PRAGMATIC_HAND_INCOMPLETE']:continue
                expected=0 if o['gameId'] in ['17514361115','17514021715'] else 1
                rows.append(' '.join([','.join(o['playerCards']),','.join(o['bankerCards']),o.get('result','player'),str(expected)]))
        fixture.write_text('\n'.join(rows),encoding='utf-8');args.append(str(fixture))
    subprocess.run(args,check=True,timeout=30)
    accounting=compile_cpp(root/'tests/confirmed_bet_accounting_test.cpp',directory/'accounting',[root/'src'])
    subprocess.run([str(accounting)],check=True,timeout=30)
    print('PASS existing confirmed-bet accounting regression')

handler=source[source.index('        if (PragmaticTopKey(payload, "gameresult"))'):source.index('        if (PragmaticTopKey(payload, "SideBetsLimits")')]
gate=handler.index('pragmatic_hand_integrity::Check(')
for marker in ['PragmaticFinishActiveAutoBet(', 'PragmaticModelRoundPnlHundredths(', 'MainReturnedHundredths(', 'PragmaticStrategySubtractHand(']:
    assert gate<handler.index(marker), marker
assert 'PragmaticRejectInconsistentResult(*tableId' in handler
assert 'pc >= 2 && pc <= 3 && bc >= 2 && bc <= 3' in handler
assert '(ppKnown && pp != playerPair)' in handler and '(bpKnown && bp != bankerPair)' in handler
strategy=source[source.index('    PragmaticStrategyMath('):source.index('    PragmaticStrategyMath(')+500]
assert 'st.resultAccountingUncertain' in strategy
shoe=source[source.index('    void PragmaticEmitShoeStart('):source.index('    void PragmaticEmitShoeStart(')+6500]
assert 'resultAccountingUncertain = false' not in shoe
print('PASS integration: validation before settlement/counting; uncertain accounting blocks strategy across shoes')
