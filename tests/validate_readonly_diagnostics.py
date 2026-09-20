"""Exercise production diagnostic routing with an in-memory CDP transport."""
from pathlib import Path
import subprocess
from test_toolchain import compile_cpp, temporary_directory

root = Path(__file__).resolve().parents[1]
main = (root / 'src/main.cpp').read_text(encoding='utf-8-sig')
strings = main[main.index('static std::optional<std::string> ExtractJsonString('):main.index('static std::vector<std::string> ExtractJsonStringArray(')]
ints = main[main.index('static std::optional<int> ExtractJsonInt('):main.index('static std::optional<double> ExtractJsonDouble(')]
capture = main[main.index('class CaptureWriter {'):main.index('enum class ProviderMode {')]
code = r'''
#include "readonly_diagnostics.h"
#include <optional>
#include <cassert>
#include <iostream>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <mutex>
using namespace std;
using ULONGLONG=unsigned long long;
using DWORD=unsigned long;
using WINHTTP_WEB_SOCKET_BUFFER_TYPE=int;
const int WINHTTP_WEB_SOCKET_UTF8_MESSAGE_BUFFER_TYPE=1, WINHTTP_WEB_SOCKET_UTF8_FRAGMENT_BUFFER_TYPE=2, WINHTTP_WEB_SOCKET_CLOSE_BUFFER_TYPE=3;
const DWORD ERROR_SUCCESS=0,ERROR_WINHTTP_TIMEOUT=12002;
ULONGLONG tick=1000;
ULONGLONG GetTickCount64(){return tick;}
DWORD WinHttpWebSocketReceive(void*,void*,DWORD,DWORD*,int*){return 1;}
string IsoNow(){return "test-time";}
wstring Utf8ToWide(const string&s){return wstring(s.begin(),s.end());}
string JsonEscape(const string&s){string r;for(char c:s){if(c=='"'||c=='\\')r+='\\';if(c=='\n'){r+="\\n";continue;}if(c=='\r'){r+="\\r";continue;}r+=c;}return r;}
struct SYSTEMTIME {unsigned wYear=2026,wMonth=9,wDay=20,wHour=12,wMinute=0,wSecond=0;};
void GetLocalTime(SYSTEMTIME*){}
CAPTURE_CLASS
HELPERS
struct Harness {
 bool stop_=false; void* hWebSocket_=nullptr; uint64_t seq=0;
 vector<string> sends; vector<wstring> logs;
 uint64_t NextId(){return ++seq;}
 bool SendRaw(const string&s,bool diagnosticRead){assert(diagnosticRead);sends.push_back(s);return true;}
 void Log(const wstring&s){logs.push_back(s);}
 bool HttpGetJsonVersion(string&){return false;}
 bool ConnectBrowserWs(const string&){return false;}
 void CloseHandles(){}
 #include "readonly_diagnostic_methods.h"
};
int main(){
 {ofstream blocker("captures"); blocker<<"not a directory";}
 {CaptureWriter disabled(false); assert(disabled.Path().empty());}
 bool rejected=false;
 try {CaptureWriter enabled;} catch(const filesystem::filesystem_error&) {rejected=true;}
 assert(rejected); // Diagnostic construction avoids the failing legacy relative capture path.
 using namespace readonly_diagnostics;
 assert(IsRoosterUrl("https://www.rooster.bet/de/game/table"));
 assert(IsRoosterUrl("https://ROOSTER.BET/de"));
 for(auto url:{"https://rooster.bet.evil/de","https://evil/?https://rooster.bet","https://rooster.bet@evil/","http://rooster.bet/","https://betify.com/"}) assert(!IsRoosterUrl(url));
 assert(Field(R"({"params":{"sessionId":"child"},"sessionId":"root"})","sessionId")=="\"root\"");
 assert(Field(R"({"params":{"sessionId":"child"}})","sessionId").empty());
 assert(Parts(R"([{"s":"a,\\\"b","v":[1,2]},{"s":"c"}])").size()==2);
 Harness h;
 assert(!h.DiagnosticSend("Input.dispatchMouseEvent","{}","","bad"));
 assert(!h.DiagnosticSend("Page.navigate","{}","","bad"));
 assert(h.sends.empty());
 h.DiagnosticSend("Target.getTargets","{}","","targets");
 h.DiagnosticMessage(R"({"id":1,"result":{"targetInfos":[{"url":"https://betify.com/","targetId":"other","type":"page"},{"url":"https://rooster.bet/de/game/table","targetId":"ours","type":"page"}]}})");
 assert(h.sends.size()==2 && h.sends.back().find("ours")!=string::npos);
 h.DiagnosticMessage(R"({"id":2,"result":{"sessionId":"root"}})");
 h.DiagnosticMessage(R"({"id":4,"result":{"frameTree":{"frame":{"url":"https://www.rooster.bet/de/game/table"}}}})");
 assert(h.diagnosticSessions_.count("root"));
 auto count=h.sends.size();
 h.DiagnosticMessage(R"({"method":"Target.attachedToTarget","sessionId":"other","params":{"sessionId":"unrelated","targetInfo":{"type":"iframe"}}})");
 assert(h.sends.size()==count);
 h.DiagnosticMessage(R"({"method":"Target.attachedToTarget","sessionId":"root","params":{"sessionId":"child","targetInfo":{"type":"iframe"}}})");
 assert(h.diagnosticSessions_.count("child"));
 h.DiagnosticMessage(R"({"method":"Runtime.executionContextCreated","sessionId":"child","params":{"context":{"id":42,"auxData":{"isDefault":true}}}})");
 assert(h.diagnosticContexts_["child"].count(42));
 h.DiagnosticMessage(R"({"method":"Runtime.executionContextCreated","sessionId":"child","params":{"context":{"id":43,"auxData":{"isDefault":false}}}})");
 assert(!h.diagnosticContexts_["child"].count(43));
 h.diagnosticRequests_.clear(); h.DiagnosticPoll();
 assert(h.sends.back().find("Runtime.evaluate")!=string::npos);
 assert(h.sends.back().find("contextId\\\":42") == string::npos); // context ID is a JSON number, not inside an expression
 assert(h.sends.back().find("\"contextId\":42")!=string::npos);
 count=h.sends.size(); h.DiagnosticPoll(); assert(h.sends.size()==count); // no overlapping probes
 h.DiagnosticMessage(R"({"method":"Runtime.executionContextsCleared","sessionId":"child","params":{}})");
 assert(h.diagnosticContexts_["child"].empty());
 h.DiagnosticMessage(R"({"method":"Page.frameNavigated","sessionId":"root","params":{"frame":{"url":"https://betify.com/"}}})");
 assert(h.stop_);
 Harness multi; multi.DiagnosticSend("Target.getTargets","{}","","targets");
 multi.DiagnosticMessage(R"({"id":1,"result":{"targetInfos":[{"type":"page","url":"https://rooster.bet/","targetId":"a"},{"type":"page","url":"https://www.rooster.bet/","targetId":"b"}]}})");
 assert(multi.stop_ && multi.sends.size()==1);
 Harness timeout; timeout.DiagnosticSend("Target.getTargets","{}","","targets"); tick+=16000; timeout.DiagnosticPoll(); assert(timeout.stop_);
 Harness detached; detached.diagnosticRoot_="root";
 detached.DiagnosticMessage(R"({"method":"Target.detachedFromTarget","params":{"sessionId":"root"}})"); assert(detached.stop_);
 cout<<"PASS: exact hosts, scoped child targets, isolated worlds, action rejection, ambiguous tabs, navigation, timeout, detach\n";
}
'''.replace('HELPERS', strings + ints).replace('CAPTURE_CLASS', capture)
with temporary_directory() as temp:
    source = Path(temp) / 'diagnostic_test.cpp'
    source.write_text(code, encoding='utf-8')
    executable = compile_cpp(source, Path(temp) / 'diagnostic_test', [root/'src'])
    subprocess.run([str(executable)], check=True, cwd=temp)

# Integration boundaries must remain in the production entry points.
assert 'if (diagnosticOnly_ && !diagnosticRead) return false;' in main
assert 'capture_(!diagnosticOnly)' in main
start = main[main.index('void Start(std::wstring endpoint'):main.index('void Stop()', main.index('void Start(std::wstring endpoint'))]
assert start.index('if (diagnosticOnly_)') < start.index('SCAN_RUN_START')
branch = main[main.index('case 102:'):main.index('SaveTelegramBotToken(token);',main.index('case 102:'))]
assert 'StrategyMode::LuckyPairs, true)' in branch and 'EnableWindow(a->manualChipTestBtn, FALSE)' in branch
print('PASS: production diagnostic entry and normal-send barrier')
