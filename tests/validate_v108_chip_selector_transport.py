"""Execute the exact native opener handler with local command-transport stubs."""
from pathlib import Path
from test_toolchain import temporary_directory, compile_cpp
import subprocess

root=Path(__file__).resolve().parents[1]
src=(root/'src/main.cpp').read_text(encoding='utf-8')
start=src.index('        if (auto value = extractConsoleValue("__BAC_CHIP_SELECTOR_OPEN_COORDS__"))')
end=src.index('        if (auto value = extractConsoleValue("__BAC_STAKE_PREP_COORDS__"))',start)
handler=src[start:end]
code=r'''
#include <atomic>
#include <cassert>
#include <cstdint>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_set>
using namespace std;
static atomic<int> gPragmaticAutoBetMode{2};
static map<string,string> strings;
static map<string,int> ints;
static string IsoNow(){return "now";}
static string JsonEscape(const string& s){return s;}
static optional<string> ExtractJsonString(const string&,const string& k){auto i=strings.find(k);return i==strings.end()?nullopt:optional<string>(i->second);}
static optional<int> ExtractJsonInt(const string&,const string& k){auto i=ints.find(k);return i==ints.end()?nullopt:optional<int>(i->second);}
struct Capture {void WriteRaw(const string&) {}};
struct Harness {
 string scanRunToken_{"run"};
 mutex pragmaticBetsOpenMu_;
 map<string,string> pragmaticBetsOpenGameByTable_{{"table","game"}};
 unordered_set<string> pragmaticChipSelectorOpenKeys_;
 Capture capture_;
 int commands=0;
 bool manualChipTest=false;
 bool PragmaticAutoBetRequestActive(const string& table,const string& game){
  return table=="table"&&game=="game"&&
    (manualChipTest||gPragmaticAutoBetMode==2);
 }
 optional<string> extractConsoleValue(const string&){return "__BAC_CHIP_SELECTOR_OPEN_COORDS__{}";}
 bool SendCommandChecked(const string& method,const string&,const string& session,uint64_t&){assert(method=="Input.dispatchMouseEvent");assert(session=="full-session");++commands;return true;}
 void run(){const string sid="short",fullSessionId="full-session";
''' + handler + r'''
 }
};
static void reset(){
 gPragmaticAutoBetMode=2;
 strings={{"runToken","run"},{"tableid","table"},{"sourceGameId","game"},{"focusInvocation","focus"},{"phase","pair"},{"href","https://client.pragmaticplaylive.net/desktop/multibaccarat/"}};
 ints={{"x",1100},{"y",680},{"width",44},{"height",44},{"rootInnerWidth",1280},{"rootInnerHeight",760}};
}
int main(){
 reset();Harness ok;ok.run();assert(ok.commands==3);ok.run();assert(ok.commands==3);
 strings["phase"]="main-chip";ok.run();assert(ok.commands==6);ok.run();assert(ok.commands==6);
 strings["phase"]="main";ok.run();assert(ok.commands==9);
 reset();Harness stale;strings["sourceGameId"]="old";stale.run();assert(stale.commands==0);
 reset();Harness run;strings["runToken"]="old";run.run();assert(run.commands==0);
 reset();Harness paper;gPragmaticAutoBetMode=1;paper.run();assert(paper.commands==0);
 reset();Harness manual;gPragmaticAutoBetMode=0;manual.manualChipTest=true;manual.run();assert(manual.commands==3);
 reset();Harness phase;strings["phase"]="unknown";phase.run();assert(phase.commands==0);
 reset();Harness main;strings["href"]="https://client.pragmaticplaylive.net/desktop/baccarat/";main.run();assert(main.commands==0);
 reset();Harness offscreen;ints["x"]=1280;offscreen.run();assert(offscreen.commands==0);
 reset();Harness large;ints["width"]=255;large.run();assert(large.commands==0);
 reset();Harness closed;closed.pragmaticBetsOpenGameByTable_.clear();closed.run();assert(closed.commands==0);
}
'''
with temporary_directory() as d:
    cpp=Path(d)/'selector_handler.cpp';cpp.write_text(code,encoding='utf-8')
    exe=compile_cpp(cpp,Path(d)/'selector_handler')
    subprocess.run([str(exe)],check=True)
print('Native selector opener: accepted current request; duplicates, stale requests, paper mode and invalid coordinates rejected.')
