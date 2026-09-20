from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
src=(root/'src/main.cpp').read_text(encoding='utf-8')

assert "__BCP_PRAGMATIC_ALL_TABLES_GUARD__" in src
assert "multiplayViewMode=goodRoadsActive?'good-roads':'all-tables'" in src
assert 'multiplayViewMode != "good-roads"' in src
assert 'PRAGMATIC_MULTIPLAY_FILTERED_VIEW_IGNORED' in src
assert "requestAllTablesTrustedClick('focus-fallback')" in src
assert '__BAC_PRAGMATIC_ALL_TABLES_TRUSTED_CLICK__' in src

# Model the membership gate: a reduced Good-Roads view must not age out
# the other tables. Only a proven All-Tables view may remove them.
active=set(f'T{i}' for i in range(1,20))
missing_since={}
missing_count={}

def probe(names,tick,mode):
    global active
    if not names or mode=='good-roads':
        return set(active)
    observed=set(names)
    for n in observed:
        active.add(n); missing_since.pop(n,None); missing_count.pop(n,None)
    drop=[]
    for n in list(active):
        if n in observed: continue
        missing_since.setdefault(n,tick)
        missing_count[n]=missing_count.get(n,0)+1
        if missing_count[n]>=3 and tick-missing_since[n]>=16000:
            drop.append(n)
    for n in drop:
        active.remove(n); missing_since.pop(n,None); missing_count.pop(n,None)
    return set(active)

assert len(probe(['T1','T2'],0,'good-roads'))==19
assert len(probe(['T1','T2'],8000,'good-roads'))==19
assert len(probe(['T1','T2'],20000,'good-roads'))==19
# Once All Tables really shows 14 tables, the original grace behavior applies.
reduced=[f'T{i}' for i in range(1,15)]
assert len(probe(reduced,24000,'all-tables'))==19
assert len(probe(reduced,32000,'all-tables'))==19
assert len(probe(reduced,40000,'all-tables'))==14
print('v82 Good Roads guard + filtered-view membership suppression: OK')
