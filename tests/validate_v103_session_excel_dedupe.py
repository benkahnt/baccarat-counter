from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT/'src/main.cpp').read_text(encoding='utf-8')
export = (ROOT/'src/session_export.h').read_text(encoding='utf-8')
build_b = (ROOT/'build.bat').read_bytes()
build = build_b.decode('utf-8', errors='replace')
readme = (ROOT/'README.md').read_text(encoding='utf-8')

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'BaccaratCounter/21.2.110' in src
assert 'Baccarat Counter v21.2.123' in src
assert '# Baccarat Counter v21.2.123' in readme
assert b'\r\n' in build_b and build_b.count(b'\r\n') > 50

# Logical de-duplication must not rely solely on random GUID ids.
for token in [
    'SameLogicalSession(const Record& a, const Record& b)',
    'a.startIso == b.startIso',
    'AppendOrMergeLogicalRecord',
    'PreferDuplicateCandidate',
    'MergeDuplicateRecord',
    'RecordCompletenessScore',
]:
    assert token in export, token

load_start = export.index('inline std::vector<Record> LoadAllRecords')
load = export[load_start:export.index('inline std::uint32_t Crc32', load_start)]
assert 'AppendOrMergeLogicalRecord(records, historical)' in load
assert 'AppendOrMergeLogicalRecord(records, *parsed)' in load
assert 'item.id == parsed->id' not in load

# No source .session files are deleted by the clean-up; only the generated
# workbook view is logically collapsed.
assert 'std::filesystem::remove(entry.path()' not in export

# Existing workbook rebuild path runs at startup and therefore cleans an old
# workbook automatically even before another manual save.
assert 'session_export::EnsureWorkbook(' in src
assert 'CentralSessionDirectory()' in src

# Edge/Burn/Pair logic remains unchanged by this Excel-only release.
def extract_function(text, signature):
    i=text.index(signature); b=text.index('{',i); depth=0; state='normal'; esc=False; j=b
    while j<len(text):
        c=text[j]; n=text[j+1] if j+1<len(text) else ''
        if state=='line':
            if c=='\n': state='normal'
        elif state=='block':
            if c=='*' and n=='/': state='normal'; j+=1
        elif state=='str':
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=='"': state='normal'
        elif state=='char':
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=="'": state='normal'
        else:
            if c=='/' and n=='/': state='line'; j+=1
            elif c=='/' and n=='*': state='block'; j+=1
            elif c=='"': state='str'
            elif c=="'": state='char'
            elif c=='{': depth+=1
            elif c=='}':
                depth-=1
                if depth==0: return text[i:j+1]
        j+=1
    raise AssertionError('unbalanced')

import hashlib
hashes={
 'PragmaticStrategyMath(const PragmaticTableRuntime& st) const':'c9be49425035bb2b84569b8c803c92d690024314ede223982e43441e78a2c9bf',
 'QueueTelegramSignalSettlement(HWND hwnd':'2726f2b51a6a0213761aa66bfcb120ff7e585489eb4b422f7f1be67bd55a3117',
 'bool PragmaticClickPairBet(':'298a181b6081de73354c78aeee9f26fa34ed47473ac9de48ef5757baadc93b05',
}
for sig,h in hashes.items():
    assert hashlib.sha256(extract_function(src,sig).encode()).hexdigest()==h, sig

print('v21.2.105 logical session Excel de-duplication: OK')
