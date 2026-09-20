"""Verify production log append/rotation against a private, hidden Win32 EDIT."""
from pathlib import Path
import re
import subprocess
from test_toolchain import compile_cpp, temporary_directory

root = Path(__file__).resolve().parents[1]
source = (root / 'src/main.cpp').read_text(encoding='utf-8-sig')
append = source[source.index('static void AppendLog('):source.index('static void UpdateTabVisibility(')]
limit = re.search(r'SendMessageW\(a->log, EM_SETLIMITTEXT, (\d+), 0\);', source).group(1)
code = r'''
#include <windows.h>
#include <string>
#include <cassert>
#include <iostream>
#pragma comment(lib, "user32.lib")
APPEND
int main() {
 HWND edit=CreateWindowExW(0,L"EDIT",L"",ES_MULTILINE|ES_READONLY,0,0,10,10,nullptr,nullptr,GetModuleHandleW(nullptr),nullptr);
 assert(edit);
 SendMessageW(edit,EM_SETLIMITTEXT,LOG_CAPACITY,0);
 for(int i=0;i<300;i++) AppendLog(edit,std::wstring(1000,L'x'));
 AppendLog(edit,L"LATEST-RECORD");
 int size=GetWindowTextLengthW(edit);
 assert(size>32767 && size<122000);
 std::wstring text(size+1,L'\0');
 GetWindowTextW(edit,text.data(),size+1);
 text.resize(size);
 assert(text.ends_with(L"LATEST-RECORD\r\n"));
 DestroyWindow(edit);
 std::cout<<"PASS: log continues past default EDIT limit and retains latest record after rotation\n";
}
'''.replace('APPEND', append).replace('LOG_CAPACITY', limit)
with temporary_directory() as directory:
    folder = Path(directory)
    cpp = folder / 'gui_log_test.cpp'
    cpp.write_text(code, encoding='utf-8')
    exe = compile_cpp(cpp, folder / 'gui_log_test')
    subprocess.run([str(exe)], check=True)
