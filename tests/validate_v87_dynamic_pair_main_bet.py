from pathlib import Path
from test_toolchain import temporary_directory
import re, subprocess, tempfile, math

root=Path(__file__).resolve().parents[1]
src=(root/'src/main.cpp').read_text(encoding='utf-8')
build=(root/'build.bat').read_text(encoding='utf-8',errors='ignore')
ini=(root/'BaccaratCounter.ini.example').read_text(encoding='utf-8')

# v87 base features retained in v88.
assert 'L"Pair-Chip €:"' in src
assert '(HMENU)133' in src
assert 'PairChipEUR' in src and 'PairChipEUR=2.00' in ini
assert 'Alle Tische Auto: EIN' not in src
assert 'Alle Tische Auto: AUS' not in src
assert 'const ALL_TABLES_AUTO=true;' in src

# Provider rule + shared fallback.
assert 'PragmaticParsePairLimitTiers' in src
assert 'sideBetsLimits' in src
assert 'kStandardPairLimitFromHand = 60' in src
assert 'kStandardPairLimitPercent = 20' in src
assert 'st.pairSideBetLimits.empty()' in src
assert 'tier->fromHand' in src and 'tier->maxPercentOfMain' in src

# Pair amount is composed from a real denomination, not required to equal one chip.
assert 'PragmaticFindSingleDenomComposition' in src
assert 'pairChipDenomCents' in src and 'pairChipClicks' in src
assert 'pair-amount-composition-unavailable' in src
assert 'pair-chip-not-available' not in src

# 0.40 EUR -> 0.20 EUR x2 sanity.
def compose(amount, chips, max_clicks=20):
    for chip in sorted(chips, reverse=True):
        if chip > 0 and chip <= amount and amount % chip == 0:
            n=amount//chip
            if 1 <= n <= max_clicks:
                return chip,n
    return None
chips=[20,100,200,500,2500,10000,25000,100000]
assert compose(40,chips)==(20,2)
assert compose(200,chips)==(200,1)

# 0.40 Pair at 20% => 2.00 main; largest exact main denom is 2.00 x1.
pair=40; percent=20
raw=math.ceil(pair*100/percent)
main=math.ceil(raw/min(chips))*min(chips)
assert main==200
assert compose(main,chips)==(200,1)

# Remaining-shoe EV and main-bet sequence are retained.
assert 'PragmaticComputeMainBetEv' in src
assert 'ev.banker > ev.player' in src
assert 'combined-ev-not-positive' not in src
assert 'main-plus-pairs-combined-ev-advisory-only' in src
for marker in ('__BAC_STAKE_PREP_COORDS__','__BAC_STAKE_PREP_CONFIRM__',
               'PRAGMATIC_STAKE_PREP_TRUSTED_CLICK','PRAGMATIC_MAIN_BET_ACCOUNTED',
               'PRAGMATIC_MAIN_BET_RESULT'):
    assert marker in src
assert 'select-main-chip-' in src and 'select-pair-chip-' in src

# Multiple physical Pair chips are dispatched through the same v63/v65/v81 embedded transport.
assert 'pairClicksPerSide' in src
assert 'pending.clickCount' in src
assert 'clickIndex < pending.clickCount' in src
pair_transport=src[src.index('const std::string& inputSessionId = pending.sessionId;')-800:src.index('void Bootstrap()', src.index('const std::string& inputSessionId = pending.sessionId;'))]
assert 'foregrounded-embedded-pragmatic' in pair_transport
assert 'Input.dispatchMouseEvent' in pair_transport
assert 'PragmaticCurrentBetifyPageSession' not in pair_transport

# Accounting remains exact in 1/100 strategy unit.
assert 'gSessionMainBetPnlHundredths' in src
assert 'SessionPnlHundredths()' in src
assert 'FormatUnitHundredths' in src
session_export=(root/'src/session_export.h').read_text(encoding='utf-8')
assert 'BaccaratCounterSession 7' in session_export
assert 'unitsHundredths' in session_export

# Reconstruct focus JS with representative v88 plan and syntax-check it.
method=src.index('void PragmaticFocusSignalTable')
start=src.index('std::string js = R"JS((async()=>{try{',method)
end=src.index('const std::string params =',start)
segment=src[start:end]
chunks=list(re.finditer(r'R"JS\((.*?)\)JS"',segment,re.S))
assert len(chunks)==17, len(chunks)
# RUN, table, name, game, manual, reassert, auto, pair target, pair denom,
# pair clicks, main required, side, main stake, main denom, main clicks, request token.
insertions=['test-run','table-13','Speed Baccarat 13','game-1',
            'false','false','true','40','20','2','true','Player','200','200','1','42']
js=chunks[0].group(1)
for insertion,chunk in zip(insertions,chunks[1:]):
    js += insertion + chunk.group(1)
for token in ('chipTarget','mainTarget','__BAC_STAKE_PREP_COORDS__','__BAC_PAIR_READINESS__',
              'PAIR_CHIP_DENOM_CENTS','PAIR_CHIP_CLICKS'):
    assert token in js
with temporary_directory() as d:
    f=Path(d)/'focus_v88.js'; f.write_text(js,encoding='utf-8')
    subprocess.run(['node','--check',str(f)],check=True)

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'Baccarat Counter v21.2.123' in src
print('v21.2.87 dynamic main bet retained; v89 combined EV advisory: OK')
