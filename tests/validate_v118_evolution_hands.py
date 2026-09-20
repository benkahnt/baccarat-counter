from pathlib import Path
import subprocess
from test_toolchain import compile_cpp, temporary_directory
root=Path(__file__).resolve().parents[1]
s=(root/'src/main.cpp').read_text(encoding='utf-8-sig')
a=s.index('    static int EvolutionDisplayedHands(')
fn=s[a:s.index('    void EvolutionUpdateStrategy(',a)]
start=s.index('if (auto value = extractConsoleValue("__BAC_TRANSPORT_TABLE_STATUS__"))')
assert 'EvolutionDisplayedHands(payload)' in s[start:s.index('if (auto value = extractConsoleValue("__BAC_TRANSPORT_HAND_COMPLETE__"))',start)]
strategy=s[s.index('    void EvolutionUpdateStrategy('):s.index('    void EvolutionSettleModel(',s.index('    void EvolutionUpdateStrategy('))] if '    void EvolutionSettleModel(' in s else ''
assert 'shoe.shoeHands = ExtractJsonInt(payload, "shoeHands").value_or(-1)' in s
assert 'st.shoeHands=officialCardsOut===0?0:null' in s
assert 'providerCounts.total' in s and 'st.providerOutcomeCounts=null' in s
# Compile the actual native display mapping with a minimal field reader.
code=r'''
#include <optional>
#include <string>
#include <map>
#include <cassert>
using namespace std;
static map<string,int> fields;
static optional<int> ExtractJsonInt(const string&,const string& k){auto i=fields.find(k);return i==fields.end()?nullopt:optional<int>{i->second};}
'''+fn+r'''
int main(){
 fields={{"providerPlayerWins",13},{"providerBankerWins",8},{"providerTieWins",7},{"providerCountAgeMs",0},{"shoeHands",0}};
 assert(EvolutionDisplayedHands("")==28);
 fields["providerPlayerWins"]=16;fields["providerBankerWins"]=16;fields["providerTieWins"]=2;assert(EvolutionDisplayedHands("")==34);
 fields["providerCountAgeMs"]=5001;assert(EvolutionDisplayedHands("")==34);
 fields.erase("shoeHands");assert(EvolutionDisplayedHands("")==34);
 fields["providerCountAgeMs"]=0;fields.erase("providerTieWins");assert(EvolutionDisplayedHands("")==-1);
 fields["providerTieWins"]=0;fields["providerPlayerWins"]=0;fields["providerBankerWins"]=0;assert(EvolutionDisplayedHands("")==0);
 fields["providerPlayerWins"]=-1;assert(EvolutionDisplayedHands("")==-1);
 fields["providerPlayerWins"]=104;fields["providerBankerWins"]=1;assert(EvolutionDisplayedHands("")==-1);
}
'''
with temporary_directory() as d:
 p=Path(d)/'hands.cpp';p.write_text(code,encoding='utf-8')
 exe=compile_cpp(p,Path(d)/'hands');subprocess.run([str(exe)],check=True,timeout=30)
# Parse the complete injected Evolution script so integration syntax is checked.
start=s.index('    std::string CardScanScript() {');end=s.index('    static std::wstring LowerWindowText(',start)
part=s[start:end];import re
chunks=re.findall(r'R"JS\((.*?)\)JS"',part,re.S)
assert len(chunks)==2
with temporary_directory() as d:
 p=Path(d)/'scan.js';p.write_text(chunks[0]+'"offline"'+chunks[1],encoding='utf-8')
 subprocess.run(['node','--check',str(p)],check=True,timeout=30)
print('PASS Evolution P+B+T display, missing/stale/zero counts, preserved tracked shoe state, scan integration syntax')
