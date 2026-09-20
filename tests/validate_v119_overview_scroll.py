"""Run the production refresh against a native Windows report ListView."""
from pathlib import Path
import subprocess
from test_toolchain import compile_cpp, temporary_directory

root = Path(__file__).resolve().parents[1]
source = (root/'src/main.cpp').read_text(encoding='utf-8-sig')
def take(a,b):
    start=source.index(a)
    return source[start:source.index(b,start)]
body = r'''
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <commctrl.h>
#pragma comment(lib,"user32.lib")
#pragma comment(lib,"comctl32.lib")
#include <algorithm>
#include <cassert>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <vector>
enum class ProviderMode { Evolution, PragmaticPlay };
TABLE_STATE
struct AppState {
 HWND overview{};
 std::vector<std::wstring> overviewOrder;
 std::map<std::wstring,TableOverviewState> tableOverview;
 std::set<std::wstring> visibleFilterIds;
 ProviderMode activeProvider=ProviderMode::Evolution;
 bool providerFilterActive=false;
};
bool IsExcludedBaccaratVariantName(const std::wstring&){return false;}
void ParseOverviewFields(TableOverviewState&,bool){}
std::wstring FormatStrategyPercent(double,int){return L"0";}
std::wstring FormatStrategyEdge(double){return L"0";}
std::wstring FormatUnitHundredths(int){return L"0";}
std::string WideToUtf8(const std::wstring& s){return {s.begin(),s.end()};}
struct Accounting {int paperSignals=0; int ActualTotal()const{return 0;} int PaperTotal()const{return 0;}};
struct Ledger { Accounting ReadTable(const std::string&)const{return {};}} gSessionSignalAccounting;
REFRESH
std::wstring id(int i){wchar_t text[32];swprintf_s(text,L"Table %03d",i);return text;}
int main(){
 INITCOMMONCONTROLSEX init{sizeof(init),ICC_LISTVIEW_CLASSES};assert(InitCommonControlsEx(&init));
 // Invisible parent: only this isolated native control is exercised.
 HWND parent=CreateWindowExW(0,L"STATIC",L"Offline scroll test",WS_OVERLAPPEDWINDOW,0,0,800,500,nullptr,nullptr,nullptr,nullptr);
 assert(parent);
 AppState a;
 a.overview=CreateWindowExW(0,WC_LISTVIEWW,L"",WS_CHILD|WS_VISIBLE|WS_HSCROLL|WS_VSCROLL|LVS_REPORT|LVS_SINGLESEL|LVS_SHOWSELALWAYS,
   0,0,760,420,parent,nullptr,nullptr,nullptr);assert(a.overview);
 ListView_SetExtendedListViewStyle(a.overview,LVS_EX_FULLROWSELECT|LVS_EX_DOUBLEBUFFER);
 for(int i=0;i<15;++i){LVCOLUMNW col{};col.mask=LVCF_WIDTH|LVCF_TEXT;col.cx=150;col.pszText=const_cast<wchar_t*>(L"Column");ListView_InsertColumn(a.overview,i,&col);}
 for(int i=0;i<150;++i){a.tableOverview[id(i)].name=id(i);a.tableOverview[id(i)].shoeHands=20;}
 RefreshOverview(&a);assert(ListView_GetItemCount(a.overview)==150);
 ListView_SetItemState(a.overview,0,LVIS_SELECTED|LVIS_FOCUSED,LVIS_SELECTED|LVIS_FOCUSED);
 RECT r{};assert(ListView_GetItemRect(a.overview,0,&r,LVIR_BOUNDS));int height=r.bottom-r.top;
 ListView_Scroll(a.overview,350,40*height);
 assert(ListView_GetTopIndex(a.overview)==40);
 const int horizontal=GetScrollPos(a.overview,SB_HORZ);assert(horizontal>0);
 for(int pass=0;pass<100;++pass){
   for(auto& kv:a.tableOverview)kv.second.shoeHands=20+pass;
   RefreshOverview(&a);
   assert(ListView_GetTopIndex(a.overview)==40);
   assert(GetScrollPos(a.overview,SB_HORZ)==horizontal);
   assert(a.overviewOrder[ListView_GetNextItem(a.overview,-1,LVNI_SELECTED)]==id(0));
 }
 std::cout<<"PASS 100 live refreshes preserve vertical/horizontal scroll and offscreen selection\n";
 wchar_t hands[32];ListView_GetItemText(a.overview,40,4,hands,32);assert(std::wstring(hands)==L"119");
 std::cout<<"PASS existing cell values update in place\n";
 SendMessageW(a.overview,WM_MOUSEWHEEL,MAKEWPARAM(0,static_cast<WORD>(-WHEEL_DELTA)),0);
 int wheeled=ListView_GetTopIndex(a.overview);assert(wheeled>40);
 RefreshOverview(&a);assert(ListView_GetTopIndex(a.overview)==wheeled);
 std::cout<<"PASS mouse wheel scroll survives refresh\n";
 std::wstring anchor=a.overviewOrder[wheeled];
 a.tableOverview[id(100)].signal=L"SETZEN: Pair";RefreshOverview(&a);
 assert(a.overviewOrder[ListView_GetTopIndex(a.overview)]==anchor);
 assert(a.overviewOrder[ListView_GetNextItem(a.overview,-1,LVNI_SELECTED)]==id(0));
 std::cout<<"PASS reordered signals preserve top table and selection by ID\n";
 int beforeRemove=ListView_GetTopIndex(a.overview);
 a.tableOverview.erase(anchor);RefreshOverview(&a);
 assert(ListView_GetTopIndex(a.overview)==beforeRemove);
 a.tableOverview.erase(id(0));RefreshOverview(&a);assert(ListView_GetNextItem(a.overview,-1,LVNI_SELECTED)==-1);
 std::cout<<"PASS removal of anchor or selected table keeps valid viewport/selection\n";
 for(int i=150;i<180;++i)a.tableOverview[id(i)].name=id(i);
 int beforeAdd=ListView_GetTopIndex(a.overview);RefreshOverview(&a);assert(ListView_GetTopIndex(a.overview)==beforeAdd);
 a.activeProvider=ProviderMode::PragmaticPlay;a.providerFilterActive=true;
 RefreshOverview(&a);assert(ListView_GetItemCount(a.overview)==0);
 for(int i=170;i<180;++i)a.visibleFilterIds.insert(id(i));
 RefreshOverview(&a);assert(ListView_GetItemCount(a.overview)==10);assert(ListView_GetTopIndex(a.overview)==0);
 std::cout<<"PASS insertion, empty filter and shorter list keep usable scrollbars\n";
 DestroyWindow(parent);
}
'''
body=body.replace('TABLE_STATE',take('struct TableOverviewState {','struct EvolutionTelegramSignalState'))
body=body.replace('REFRESH',take('static void RefreshOverview(AppState* a) {','static uint64_t CounterDelta'))
with temporary_directory() as directory:
    path=Path(directory)/'scroll.cpp';path.write_text(body,encoding='utf-8')
    exe=compile_cpp(path,Path(directory)/'scroll')
    subprocess.run([str(exe)],check=True,timeout=30)
