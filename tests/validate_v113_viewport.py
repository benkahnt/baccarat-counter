from pathlib import Path
import subprocess
from test_toolchain import temporary_directory, compile_cpp
root=Path(__file__).resolve().parents[1]
src=(root/'src/main.cpp').read_text(encoding='utf-8')
def section(a,b):
 i=src.index(a);return src[i:src.index(b,i)]
pending=section('    struct PendingBurnScreenshot {','    struct ParallelFocusCandidate')
methods=section('    void MaybeExpirePragmaticBurnScreenshot()','    void HandlePragmaticTrustedPairClickResponse(')
head=r'''#include <cassert>
#include <atomic>
#include <cstdint>
#include <iostream>
#include <mutex>
#include <optional>
#include <regex>
#include <sstream>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>
using ULONGLONG = unsigned long long;
static std::atomic<ULONGLONG> nowTick{100};
ULONGLONG GetTickCount64(){return nowTick.load();}
std::string IsoNow(){return "test";}
std::string JsonEscape(const std::string& s){return s;}
std::optional<int> ExtractJsonInt(const std::string& s,const std::string& k){std::smatch m; if(std::regex_search(s,m,std::regex("\\\""+k+"\\\":(\\d+)")))return std::stoi(m[1]);return {};}
std::optional<std::string> ExtractJsonString(const std::string& s,const std::string& k){std::smatch m;if(std::regex_search(s,m,std::regex("\\\""+k+"\\\":\\\"([^\\\"]*)\\\"")))return m[1];return {};}
struct Capture {std::mutex mu;std::vector<std::string> lines;void WriteRaw(const std::string& s){std::lock_guard<std::mutex> g(mu);lines.push_back(s);}};
class Harness {public:
'''
tail=r'''
Capture capture_;
std::mutex pragmaticBurnScreenshotMu_;
std::unordered_map<uint64_t,PendingBurnScreenshot> pragmaticBurnScreenshotRequests_;
bool pragmaticBurnScreenshotDisabled_{false},sendWorks{true};
std::string pageSession{"test-page"},lastMethod,lastParams;
unsigned calls{0}; uint64_t nextId{0};
std::string PragmaticTopLevelPageSession(){return pageSession;}
bool SendCommandChecked(const std::string& m,const std::string& p,const std::string& sid,uint64_t& id){assert(sid=="test-page");id=++nextId;++calls;lastMethod=m;lastParams=p;return sendWorks;}
uint64_t request(){return PragmaticRequestTopLevelBurnScreenshot("table","Table",1,1,997,568,237,201,false,"tile");}
void reset(){std::lock_guard<std::mutex> g(pragmaticBurnScreenshotMu_);pragmaticBurnScreenshotRequests_.clear();pragmaticBurnScreenshotDisabled_=false;}
};
int main(){
 {Harness h;const auto id=h.request();assert(id>0);assert(h.lastMethod=="Page.captureScreenshot");assert(h.lastParams.find("clip")==std::string::npos);assert(h.lastParams.find("\"captureBeyondViewport\":false")!=std::string::npos);assert(h.pragmaticBurnScreenshotRequests_.at(id).fullViewport);assert(h.request()==0);assert(h.calls==1);h.HandlePragmaticBurnScreenshotResponse("{\"id\":"+std::to_string(id)+",\"data\":\"jpeg\"}");assert(h.pragmaticBurnScreenshotRequests_.empty());assert(h.request()>id);std::cout<<"PASS no clip, no offscreen capture, successful response releases slot\n";}
 {Harness h;h.sendWorks=false;assert(h.request()==0);assert(h.pragmaticBurnScreenshotRequests_.empty());h.sendWorks=true;assert(h.request()>0);std::cout<<"PASS send failure does not reserve slot\n";}
 {Harness h;const auto id=h.request();h.HandlePragmaticBurnScreenshotResponse("{\"id\":"+std::to_string(id)+",\"error\":{\"message\":\"failed\"}}");assert(h.pragmaticBurnScreenshotRequests_.empty());assert(h.request()>id);std::cout<<"PASS CDP error releases slot\n";}
 {Harness h;nowTick=100;const auto id=h.request();nowTick=30099;h.MaybeExpirePragmaticBurnScreenshot();assert(!h.pragmaticBurnScreenshotDisabled_);nowTick=30100;h.MaybeExpirePragmaticBurnScreenshot();assert(h.pragmaticBurnScreenshotDisabled_);assert(h.pragmaticBurnScreenshotRequests_.empty());assert(h.request()==0);h.HandlePragmaticBurnScreenshotResponse("{\"id\":"+std::to_string(id)+",\"data\":\"late\"}");assert(h.request()==0);h.reset();assert(h.request()>id);std::cout<<"PASS lost response disables diagnostics; late response cannot restart; new run clears state\n";}
 {Harness h;std::vector<std::thread> threads;std::atomic<int> sent{0};for(int i=0;i<30;i++)threads.emplace_back([&]{if(h.request())sent++;});for(auto& t:threads)t.join();assert(sent==1);assert(h.calls==1);assert(h.pragmaticBurnScreenshotRequests_.size()==1);std::cout<<"PASS concurrent requests only dispatch one screenshot\n";}
 {Harness h;h.pageSession.clear();assert(h.request()==0);assert(h.calls==0);std::cout<<"PASS absent page session sends no screenshot\n";}
 std::cout<<"6 viewport capture regression groups passed\n";
}
'''
with temporary_directory() as d:
 p=Path(d)/'viewport_capture.cpp'
 p.write_text(head+pending+methods+tail,encoding='utf-8')
 exe=compile_cpp(p,Path(d)/'viewport_capture')
 subprocess.run([str(exe)],check=True)
