"""v107: structural and regression checks for the two-phase Pragmatic stake path.

This test never opens a casino page and never places a wager. It validates the
production source, syntax-checks the embedded focus JavaScript, and confirms
that math/settlement components are unchanged from v106.
"""
from pathlib import Path
import hashlib
import time
import subprocess
import tempfile
from test_toolchain import temporary_directory

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / 'src' / 'main.cpp').read_text(encoding='utf-8')
build_b = (ROOT / 'build.bat').read_bytes()
readme = (ROOT / 'README.md').read_text(encoding='utf-8')

assert b'BaccaratCounterV123.exe' in build_b
assert b'v21.2.123' in build_b
assert b'\r\n' in build_b and build_b.count(b'\r\n') > 50
assert 'BaccaratCounter/21.2.110' in src
assert 'Baccarat Counter v21.2.123' in src
assert '# Baccarat Counter v21.2.123' in readme

focus_start = src.index('void PragmaticFocusSignalTable')
focus = src[focus_start:]

# A) Accessible nested Pragmatic frames are searched recursively.
for token in [
    'const chipDocuments=(contextEl=null)=>',
    'const walk=(doc,depth=0)=>',
    'if(!doc||depth>5)return;',
    'walk(contextEl&&contextEl.ownerDocument,0)',
    'walk(document,0)',
    'walk(ROOT_DOCUMENT,0)',
    '/\\/desktop\\/(?:launcher|(?:multi)?baccarat)\\//i.test(u)',
]:
    assert token in focus, token

# B) The old blanket rejection of any ID-bearing tile is gone. A candidate
# must instead prove a complete denomination cluster, and a different table
# tile is still rejected.
rack_start = focus.index('const chipRackRoot=(contextEl=null)=>')
rack_end = focus.index('const directChipFallback=(cents,currentTable)=>', rack_start)
rack = focus[rack_start:rack_end]
assert 'if(containsTableId&&found.size<5)continue;' in rack
assert "found.size<3||!found.has('0.2')||!found.has('1')||!found.has('2')" in rack
assert 'if(containsTableId)score+=25000;' in rack
assert "if(/\\bID\\s*:\\s*\\d+/i.test(txt))continue;" not in rack

fallback_start = rack_end
fallback_end = focus.index('const chipTarget=(cents,currentTable)=>', fallback_start)
fallback = focus[fallback_start:fallback_end]
for token in [
    "nearby.size<5||!nearby.has('0.2')||!nearby.has('1')||!nearby.has('2')||!nearby.has('5')",
    "nearby.size>=7&&nearby.has('25')&&nearby.has('100')",
    'if(tile&&!tile.matchesName&&!tile.matchesSource)continue;',
    'const sameContext=c.tile?!!(o.tile&&o.tile.el===c.tile.el):!o.tile;',
    'if(!sameContext)continue;',
    'chipControlMetaByHit.set(c.el,meta)',
]:
    assert token in fallback, token

assert 'mainPrepared:!MAIN_REQUIRED,mainChipPrepared:!MAIN_REQUIRED,' in focus

assert "strong:denoms.length>=7&&!!c.interactive" in focus

# C) Main and pair preparation are independent phases. The pair coordinates
# are resolved only after the accepted main wager has caused any re-render.
prep_start = focus.index('const storePairClickCoords=(best)=>')
pair_coords_marker = focus.index("ROOT_WINDOW.console.log('__BAC_PAIR_CLICK_COORDS__'", prep_start)
prep = focus[prep_start:pair_coords_marker]
for token in [
    "const phase=MAIN_REQUIRED&&!operation.mainPrepared?(operation.mainChipPrepared?'main':'main-chip'):'pair';",
    "const pairChip=phase==='pair'?chipTarget(PAIR_CHIP_DENOM_CENTS,currentTable):null;",
    "const mainChip=phase==='main-chip'?chipTarget(MAIN_CHIP_CENTS,currentTable):null;",
    "const ackKey=[TARGET_ID,SOURCE_GAME,REQUEST_TOKEN,phase,prepAttempt].join('|');",
    "const acks=ROOT_WINDOW.__BCP_STAKE_PREP_ACKS__||Object.create(null);",
    'operation.mainPrepared=true;',
    'operation.stakePrepRequested=false;',
    'ROOT_WINDOW.setTimeout(probeAndMaybeArm,100);',
    'operation.stakePrepared=true;',
]:
    assert token in prep, token
assert prep.index('operation.mainPrepared=true;') < prep.index('operation.stakePrepared=true;')
assert "'main-dispatch-failed':'main-bet-not-confirmed'" in prep
assert "finishRetry('pair-chip-dispatch-failed')" in prep
assert "finishRetry('pair-chip-selection-unconfirmed')" in prep
# Pair betting remains strictly after denomination confirmation.
assert prep.index('pairChipSelectionConfirmed') < prep.index('operation.stakePrepared=true;')
assert prep.index('operation.stakePrepared=true;') < pair_coords_marker - prep_start

# D) C++ dispatch correlates phase+attempt, dispatches only that phase, and
# acknowledges native input to the same JavaScript runtime.
handler_start = src.index('if (auto value = extractConsoleValue("__BAC_STAKE_PREP_COORDS__"))')
handler_end = src.index('if (auto value = extractConsoleValue("__BAC_STAKE_PREP_CONFIRM__"))', handler_start)
handler = src[handler_start:handler_end]
for token in [
    'const std::string phase = ExtractJsonString(payload, "phase").value_or("");',
    'const int stakePrepAttempt = ExtractJsonInt(payload, "stakePrepAttempt").value_or(0);',
    '(phase == "main-chip" || phase == "main" || phase == "pair")',
    'const bool mainCorrelation = phase == "main"',
    'const bool pairCorrelation = phase == "pair"',
    'if (phase == "main-chip") {',
    '"select-main-chip-"',
    '"select-pair-chip-"',
    '__BCP_STAKE_PREP_ACKS__',
    '"Runtime.evaluate"',
    'ackQueued',
]:
    assert token in handler, token
# The pair chip is no longer appended to the main sequence using stale coords.
assert 'if (allSent && (!mainRequired || mainChipCents != pairChipDenomCents))' not in handler

confirm_start = handler_end
confirm_end = src.index('if (auto value = extractConsoleValue("__BAC_STAKE_PREP_CHIP_VERIFY__"))', confirm_start)
confirm = src[confirm_start:confirm_end]
assert 'if (phase == "main" && mainRequired && mainAcceptedCents > 0' in confirm

# E) Execute the exact production C++ dispatch handler. Test transport records
# native command coordinates; no browser or live page is touched.
handler_cpp = r'''#include <atomic>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <thread>
#include <unordered_set>
#include <vector>
using namespace std;
static atomic<int> gPragmaticAutoBetMode{2};
static atomic<bool> gUnitTargetReached{false},gStopLossReached{false};
static map<string,string> strings;
static map<string,int> ints;
static map<string,bool> bools;
static string IsoNow(){return "now";}
static string JsonEscape(const string& s){return s;}
static optional<string> ExtractJsonString(const string&,const string& k){auto i=strings.find(k);return i==strings.end()?nullopt:optional<string>(i->second);}
static optional<int> ExtractJsonInt(const string&,const string& k){auto i=ints.find(k);return i==ints.end()?nullopt:optional<int>(i->second);}
static optional<bool> ExtractJsonBool(const string&,const string& k){auto i=bools.find(k);return i==bools.end()?nullopt:optional<bool>(i->second);}
struct Capture {vector<string> logs;void WriteRaw(const string& s){logs.push_back(s);}};
struct Harness {
 string scanRunToken_{"run"};
 mutex pragmaticBetsOpenMu_;
 map<string,string> pragmaticBetsOpenGameByTable_{{"table","game"}};
 unordered_set<string> pragmaticStakePrepHandledKeys_;
 Capture capture_;
 vector<pair<string,string>> commands;
 bool active=true,manualChipTest=false,nativeOpen=true,closeAfterRelease=false,transportOk=true;
 string fullSession="session";
 bool PragmaticNativeBetsOpen(const string& table,const string& game){return nativeOpen&&pragmaticBetsOpenGameByTable_[table]==game;}
 bool PragmaticAutoBetRequestActive(const string& table,const string& game){
  return active&&table=="table"&&game=="game"&&
    (manualChipTest||gPragmaticAutoBetMode==2);
 }
 optional<string> extractConsoleValue(const string&){return "__BAC_STAKE_PREP_COORDS__{}";}
 bool SendCommandChecked(const string& method,const string& payload,const string& session,uint64_t& id){assert(session=="session");commands.push_back({method,payload});id=commands.size();if(closeAfterRelease&&payload.find("mouseReleased")!=string::npos)nativeOpen=false;return transportOk;}
 void run(){const string sid="s",fullSessionId=fullSession;
''' + handler + r'''
 }
};
static void reset(const string& phase="main"){
 gPragmaticAutoBetMode=2;gUnitTargetReached=false;gStopLossReached=false;
 strings={{"runToken","run"},{"tableid","table"},{"sourceGameId","game"},{"focusInvocation","focus"},{"phase",phase},{"mainSide","Banker"}};
 ints={{"stakePrepAttempt",1},{"pairChipCents",20},{"pairChipDenomCents",20},{"pairChipClicks",1},{"pairChipX",300},{"pairChipY",400},{"mainStakeCents",100},{"mainChipCents",100},{"mainChipClicks",1},{"mainChipX",10},{"mainChipY",20},{"mainX",100},{"mainY",200},{"rootInnerWidth",1280},{"rootInnerHeight",760}};
 bools={{"mainRequired",true},{"mainChipSelectionConfirmed",true}};
}
static void clickOnly(const Harness& h,int x,int y){
 assert(h.commands.size()==4);
 for(int i=0;i<3;i++){assert(h.commands[i].first=="Input.dispatchMouseEvent");assert(h.commands[i].second.find("\"x\":"+to_string(x)+",")!=string::npos);assert(h.commands[i].second.find("\"y\":"+to_string(y)+",")!=string::npos);}
 assert(h.commands[3].first=="Runtime.evaluate");assert(h.commands[3].second.find("sendOk:true")!=string::npos);
}
int main(){
 reset("main-chip");Harness chip;ints["mainX"]=-1;ints["mainY"]=-1;chip.run();clickOnly(chip,10,20);chip.run();assert(chip.commands.size()==4);
 reset();Harness main;ints["mainChipX"]=-1;ints["mainChipY"]=-1;main.run();clickOnly(main,100,200);main.run();assert(main.commands.size()==4);
 reset("pair");Harness pair;bools["mainRequired"]=false;pair.run();clickOnly(pair,300,400);pair.run();assert(pair.commands.size()==4);
 reset();Harness missing;bools.erase("mainChipSelectionConfirmed");missing.run();assert(missing.commands.empty());
 reset();Harness unconfirmed;bools["mainChipSelectionConfirmed"]=false;unconfirmed.run();assert(unconfirmed.commands.empty());
 reset();Harness oldGame;strings["sourceGameId"]="old";oldGame.run();assert(oldGame.commands.empty());
 reset();Harness oldRun;strings["runToken"]="old";oldRun.run();assert(oldRun.commands.empty());
 reset();Harness inactive;inactive.active=false;inactive.run();assert(inactive.commands.empty());
 reset();Harness closed;closed.pragmaticBetsOpenGameByTable_.clear();closed.run();assert(closed.commands.empty());
 reset();Harness session;session.fullSession="";session.run();assert(session.commands.empty());
 reset();Harness paper;gPragmaticAutoBetMode=1;paper.run();assert(paper.commands.empty());
 reset();Harness manual;gPragmaticAutoBetMode=0;manual.manualChipTest=true;manual.run();clickOnly(manual,100,200);
 reset();Harness invalid;ints["mainX"]=1280;invalid.run();assert(invalid.commands.empty());
 reset();Harness composition;ints["mainChipClicks"]=2;composition.run();assert(composition.commands.empty());
 reset();Harness unknown;strings["phase"]="unknown";unknown.run();assert(unknown.commands.empty());
 reset();Harness expired;expired.nativeOpen=false;expired.run();assert(expired.commands.size()==1&&expired.commands[0].first=="Runtime.evaluate");assert(expired.commands[0].second.find("sendOk:false")!=string::npos);
 reset();Harness stop;gStopLossReached=true;stop.run();assert(stop.commands.size()==1&&stop.commands[0].first=="Runtime.evaluate");
 reset();Harness partial;ints["mainChipClicks"]=2;ints["mainStakeCents"]=200;partial.closeAfterRelease=true;partial.run();assert(partial.commands.size()==4);assert(partial.commands.back().second.find("sendOk:false")!=string::npos);partial.run();assert(partial.commands.size()==4);
 reset("main-chip");Harness uncertain;uncertain.transportOk=false;uncertain.run();assert(uncertain.commands.size()==4);assert(uncertain.commands.back().second.find("sendOk:false")!=string::npos);uncertain.run();assert(uncertain.commands.size()==4);
}
'''
with temporary_directory() as d:
    cpp = ROOT / '.validation/v115_chip_cluster_handler.cpp'
    cpp.write_text(handler_cpp, encoding='utf-8')
    from test_toolchain import compile_cpp
    exe = compile_cpp(cpp, ROOT / '.validation/v115_chip_cluster_check_2')
    assert exe.is_file() and exe.stat().st_size > 10000, exe
    # Under a crowded Windows desktop, launching a just-linked test binary
    # can transiently return ERROR_NO_SYSTEM_RESOURCES while the file is
    # still being scanned. A retry still requires the binary to pass.
    for attempt in range(6):
        try:
            subprocess.run([str(exe)], check=True)
            break
        except OSError as exc:
            if getattr(exc, 'winerror', None) != 1450 or attempt == 5:
                raise
            time.sleep(2)

# F) Embedded production JavaScript still parses.
subprocess.run([__import__('sys').executable, str(ROOT / 'tests' / 'validate_focus_js.py')], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
subprocess.run([__import__('sys').executable, str(ROOT / 'tests' / 'validate_balance_js.py')], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# G) Math, stake planning, Telegram settlement, final pair-field transport and
# confirmed-Burn composition gate are byte-identical to v106.
def extract_function(text: str, signature: str) -> str:
    i = text.index(signature)
    b = text.index('{', i)
    depth = 0
    state = 'normal'
    esc = False
    j = b
    while j < len(text):
        c = text[j]
        n = text[j + 1] if j + 1 < len(text) else ''
        if state == 'line':
            if c == '\n': state = 'normal'
        elif state == 'block':
            if c == '*' and n == '/': state = 'normal'; j += 1
        elif state == 'str':
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': state = 'normal'
        elif state == 'char':
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == "'": state = 'normal'
        else:
            if c == '/' and n == '/': state = 'line'; j += 1
            elif c == '/' and n == '*': state = 'block'; j += 1
            elif c == '"': state = 'str'
            elif c == "'": state = 'char'
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: return text[i:j + 1]
        j += 1
    raise AssertionError(f'unbalanced function: {signature}')

expected = {
    'PragmaticStrategyMath(const PragmaticTableRuntime& st) const': 'c9be49425035bb2b84569b8c803c92d690024314ede223982e43441e78a2c9bf',
    # v111 deliberately changes the planner: executed by v106/v111 production
    # tests for Tie EV, both providers, payouts and threshold boundaries.
    'QueueTelegramSignalSettlement(HWND hwnd': '2726f2b51a6a0213761aa66bfcb120ff7e585489eb4b422f7f1be67bd55a3117',
    'bool PragmaticClickPairBet(': '298a181b6081de73354c78aeee9f26fa34ed47473ac9de48ef5757baadc93b05',
    'void PragmaticConfirmPendingBurn(': '2728a1821ad46b4c5008dd979b2ff6a12c906e9657e106271b7a17e04871d37f',
}
for signature, digest in expected.items():
    got = hashlib.sha256(extract_function(src, signature).encode()).hexdigest()
    assert got == digest, (signature, got)

print('v21.2.107 chip denomination cluster + two-phase stake path: OK')
