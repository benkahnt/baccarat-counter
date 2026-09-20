from pathlib import Path
import re

src=(Path(__file__).resolve().parents[1]/'src/main.cpp').read_text(encoding='utf-8')
misses=int(re.search(r'misses >= (\d+) && age >= (\d+)ULL',src).group(1))
age_ms=int(re.search(r'misses >= (\d+) && age >= (\d+)ULL',src).group(2))
assert misses==3 and age_ms==16000
assert 'if (!filteredNames.empty()' in src

active=set()
missing_since={}
missing_count={}

def probe(names, tick):
    global active
    if not names: # loading probe: must not remove anything
        return set(active)
    observed=set(names)
    for n in observed:
        missing_since.pop(n,None); missing_count.pop(n,None); active.add(n)
    remove=[]
    for n in list(active):
        if n in observed: continue
        missing_since.setdefault(n,tick)
        missing_count[n]=missing_count.get(n,0)+1
        if missing_count[n]>=misses and tick-missing_since[n]>=age_ms:
            remove.append(n)
    for n in remove:
        active.remove(n); missing_since.pop(n,None); missing_count.pop(n,None)
    return set(active)

base=[f'T{i}' for i in range(1,13)]
assert len(probe(base,0))==12
expanded=[f'T{i}' for i in range(1,20)]
assert len(probe(expanded,8000))==19  # additions are immediate
reduced=[f'T{i}' for i in range(1,15)]
assert len(probe(reduced,24000))==19  # first miss: grace
assert len(probe(reduced,32000))==19  # second miss: grace
assert len(probe(reduced,40000))==14  # third miss + 16s: remove
assert len(probe([],48000))==14       # empty/loading probe removes nothing
assert len(probe(reduced+['T19'],56000))==15  # reappearance is immediate
print('v79 dynamic table model 12->19->14 + reappearance: OK')
