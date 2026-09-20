"""Replay production model settlement with failed clicks; no CDP or casino IO."""
from pathlib import Path
import json
import subprocess
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from test_toolchain import compile_cpp, temporary_directory

ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'src/main.cpp').read_text(encoding='utf-8-sig')

def take(start,end):
    at=SRC.index(start)
    return SRC[at:SRC.index(end,at)]

# The test compiles the actual production settlement branch and stake result
# calculator, not a second implementation of either decision or payout.
code=r'''
#include <atomic>
#include <cassert>
#include <cmath>
#include <mutex>
#include <optional>
#include <string>
#include <thread>
#include "confirmed_bet_accounting.h"
#include "configured_edge_model.h"
#include "signal_accounting.h"
#include "session_export.h"
using namespace std;
static atomic<int> gSessionMinEdgeModelPnlHundredths{0},gSessionPositiveCombinedModelPnlHundredths{0};
static atomic<int> gSessionMinEdgeModelSignals{0},gSessionPositiveCombinedModelSignals{0};
static configured_edge_model::Session gSessionConfiguredCombinedModel;
static signal_accounting::Session gSessionSignalAccounting;
static string IsoNow(){return "fixture";}
static string JsonEscape(const string& s){return s;}
struct Harness {
'''
code+=take('    struct PragmaticStakePlan {','    struct PragmaticTableRuntime {')
code+=take('    static int PragmaticModelRoundPnlHundredths(', '    static std::string PragmaticPrettyName(')
code+=r'''
 struct State {string name="Fixture",comparisonGameId;PragmaticStakePlan comparisonStakePlan;
 double comparisonPairEdge=0;bool comparisonLivePolicyAllowed=false;} st;
 struct Capture {void WriteRaw(const string& s) {ofstream("capture.jsonl",ios::app)<<s<<'\n';}} capture_;
 void arm(const string& game,PragmaticStakePlan input,bool filterEnabled) {
   const optional<string> gameId=game;
   const auto& plan=input;
   const bool combinedFilterBlocked=filterEnabled && (!plan.valid || !plan.combinedMinEdgeMet);
   optional<pair<double,double>> preDealStrategy=pair<double,double>{.09,.08};
'''
arm=SRC.index('                if (plan.valid && st.comparisonGameId != *gameId) {')
code+=SRC[arm:SRC.index('                    capture_.WriteRaw(',arm)]+'\n}\n}\n'
code+=r'''
 optional<int> settle(const string& game,const string& result,bool playerPair=false,bool bankerPair=false,bool complete=true) {
   const optional<string> tableId="fixture",gameId=game;
   optional<int> signalPaperPnlHundredths;
'''
code+=take('            if (complete && st.comparisonGameId == *gameId &&','            if (complete && st.realMainBetGameId == *gameId &&')
code+='return signalPaperPnlHundredths;\n}\n};\n'
code+=r'''
static Harness::PragmaticStakePlan plan(const string& side,bool accepted=true) {
 Harness::PragmaticStakePlan p;
 p.valid=true;p.mainRequired=true;p.pairChipCents=20;p.mainStakeCents=100;p.mainSide=side;
 p.combinedMinEdge=.0025;p.combinedMinEdgeMet=accepted;p.combinedEvPositive=true;
 return p;
}
int main() {
 Harness h;
 const char* sides[]={"Player","Player","Player","Player","Banker","Banker","Player","Player","Banker","Player","Banker","Player","Player"};
 const char* results[]={"player","player","banker","player","banker","banker","banker","player","banker","banker","banker","tie","player"};
 const int expected[]={300,300,-700,300,275,275,-700,300,275,-700,275,-200,300};
 for(int i=0;i<13;++i) {
   const auto game=to_string(i);auto p=plan(sides[i]);h.arm(game,p,true);
   // A later setting/plan edit cannot change the frozen policy for this hand.
   p.combinedMinEdgeMet=false;
   assert(h.settle(game,results[i]).value()==expected[i]);
   assert(!h.settle(game,results[i]));
 }
 auto a=gSessionSignalAccounting.Read();
 assert(a.paperSignals==13 && a.paperPairHundredths==-2600 && a.paperMainHundredths==2900);
 assert(a.PaperTotal()==300 && a.ActualTotal()==0);
 assert(gSessionConfiguredCombinedModel.Read().pnlHundredths==300);
 assert(gSessionConfiguredCombinedModel.Read().signals==13);

 // A blocked live signal remains in the baseline comparison, not active Paper.
 h.arm("blocked",plan("Player",false),true);
 assert(!h.settle("blocked","banker"));
 assert(gSessionSignalAccounting.Read().paperSignals==13);
 assert(gSessionMinEdgeModelSignals==14);
 // Filter OFF admits that same negative-overall opportunity to active Paper.
 h.arm("off",plan("Player",false),false);
 assert(h.settle("off","banker")==-700);
 assert(gSessionSignalAccounting.Read().paperSignals==14);
 assert(gSessionConfiguredCombinedModel.Read().signals==13);
 // Incomplete or mismatched rounds must not invent results.
 h.arm("awaited",plan("Tie"),true);
 assert(!h.settle("other","tie"));assert(!h.settle("awaited","tie",false,false,false));
 assert(h.settle("awaited","tie")==3800);
 assert(gSessionSignalAccounting.Read().ActualTotal()==0);
 h.arm("tie-loss",plan("Tie"),true);assert(h.settle("tie-loss","player")==-700);
 // Real partial placement is an independent actual debit and return.
 gSessionSignalAccounting.RecordActualDelta("real",-100,-500);
 gSessionSignalAccounting.RecordActualDelta("real",1200,
     confirmed_bet_accounting::MainReturnedHundredths("Banker","banker",500));
 assert(gSessionSignalAccounting.Read().ActualTotal()==1575);
 assert(gSessionSignalAccounting.ReadTable("fixture").ActualTotal()==0);
 assert(gSessionSignalAccounting.ReadTable("real").paperSignals==0);
 gSessionSignalAccounting.Reset();assert(gSessionSignalAccounting.Read().paperSignals==0);
 thread writer([]{for(int i=0;i<1000;++i)gSessionSignalAccounting.RecordPaper("thread",to_string(i),-200,300);});
 for(int i=0;i<1000;++i){a=gSessionSignalAccounting.Read();assert(a.PaperTotal()==300*a.paperSignals);}
 writer.join();assert(gSessionSignalAccounting.Read().paperSignals==1000);

 // Save the exact capture fixture. Unknown values in older sessions stay blank.
 session_export::Record r;r.id="capture13";r.label="13 Signale ohne Chip";
 r.activePaperSignals=13;r.activePaperPairHundredths=-2600;r.activePaperMainHundredths=2900;r.confirmedActualHundredths=0;
 wstring error;
 assert(session_export::WriteRecordFile("records",r,error));
 auto read=session_export::ReadRecordFile("records/capture13.session");
 assert(read && read->activePaperSignals==13 && read->confirmedActualHundredths==0);
 assert(read->activePaperPairHundredths==-2600 && read->activePaperMainHundredths==2900);
 {
   ifstream input("records/capture13.session");vector<string> lines;string line;
   while(getline(input,line))lines.push_back(line);
   assert(lines.size()>4);lines.resize(lines.size()-4);
   lines[0]="BaccaratCounterSession 6";
   {ofstream oldFile("records/v6.session");for(const auto& item:lines)oldFile<<item<<'\n';}
   const auto v6=session_export::ReadRecordFile("records/v6.session");
   assert(v6 && !v6->activePaperSignals && !v6->confirmedActualHundredths);
   lines[0]="BaccaratCounterSession 7";
   {ofstream broken("records/truncated-v7.session");for(const auto& item:lines)broken<<item<<'\n';}
   assert(!session_export::ReadRecordFile("records/truncated-v7.session"));
 }
 session_export::Record old;old.id="legacy";old.label="legacy";
 assert(session_export::WriteWorkbook("records/check.xlsx",{r,old},error));
}
'''

with temporary_directory() as folder:
    work=Path(folder)
    source=work/'production_paper.cpp';source.write_text(code,encoding='utf-8')
    exe=compile_cpp(source,work/'production_paper',[ROOT/'src'])
    subprocess.run([str(exe)],cwd=work,check=True)
    captured=[json.loads(line) for line in (work/'capture.jsonl').read_text().splitlines()]
    active=[row for row in captured if row['kind']=='PRAGMATIC_ACTIVE_PAPER_RESULT']
    assert len(active)==16
    assert all(row['activePolicyAllowed'] and not row['placementRequired'] for row in active)
    assert sum(row['paperTotalHundredths'] for row in active[:13])==300
    assert active[12]['sessionPaperSignals']==13
    assert active[12]['sessionPaperPairHundredths']==-2600
    assert active[12]['sessionPaperMainHundredths']==2900
    assert active[12]['sessionPaperTotalHundredths']==300
    assert active[12]['sessionActualHundredthsAtModelResult']==0
    assert all(row['paperTotalHundredths']==row['paperPairHundredths']+row['paperMainHundredths'] for row in active)
    with ZipFile(work/'records/check.xlsx') as z:
        ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        cells={c.get('r'):c for c in sheet.findall('.//s:c',ns)}
        for ref,value in {'W5':-26,'X5':29,'Y5':13,'Z5':0,'AA5':3}.items():
            assert float(cells[ref].find('s:v',ns).text)==value,(ref,value)
        assert cells['AA5'].find('s:f',ns).text=='W5+X5'
        assert all(ref not in cells for ref in ('W6','X6','Y6','Z6','AA6'))
        assert sheet.find('s:dimension',ns).get('ref')=='A1:AA6'
        assert sheet.find('s:autoFilter',ns).get('ref')=='A4:AA6'

# Placement bookkeeping is the only source of actual debits/returns. UI and
# Telegram explicitly distinguish it from the already validated Paper result.
assert 'st.armedSignalIsActual = accountingMode == "confirmed-click"' in SRC
assert 'if (st.armedSignalIsActual)\n                    gSessionSignalAccounting.RecordActualDelta(*tableId, 1200 * roundHits, 0)' in SRC
assert 'gSessionSignalAccounting.RecordActualDelta(*tableId, 0, returnedHundredths)' in SRC
assert '*tableId, 0, -st.realMainBetStakeUnitsX100' in SRC
assert 'L"Telegram-Signal: NICHT PLATZIERT"' in SRC
assert 'L"\\nHand-P/L (Paper, inkl. Hauptwette): "' in SRC
assert 'L"Ist P/L",L"Paper Hände",L"Paper P/L gesamt"' in SRC
assert 'a->lastDisplayedSignalAccountingRevision != gSessionSignalAccounting.Read().revision' in SRC
assert 'model.livePolicyAllowed = allowed;' in SRC
assert 'gSessionSignalAccounting.RecordPaper(tableId, gid, pairPnl, pnl)' in SRC
print('PASS: 13 production settlements +3u, Ist0, frozen ON/OFF policies, blocked baseline, Tie8:1, partial actual, missing/duplicate round, reset/concurrency, saved export/formula, Paper/Ist UI+Telegram')
