#include "session_export.h"
#include <filesystem>
#include <iostream>

int wmain(int argc, wchar_t** argv) {
    if (argc != 2) return 2;
    const std::filesystem::path base(argv[1]);
    std::wstring error;
    if (!session_export::LoadAllRecords(base / L"Sessions").empty()) return 3;
    if (!session_export::EnsureWorkbook(base, error)) {
        std::wcerr << error << L'\n';
        return 4;
    }
    return 0;
}
