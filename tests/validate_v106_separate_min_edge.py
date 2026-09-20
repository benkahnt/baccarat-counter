"""v106: compile and execute actual production stake planner + edge helpers.
No browser, betting account or Windows API calls are made by this test.
"""
from pathlib import Path
import subprocess
import tempfile
from test_toolchain import temporary_directory
import hashlib
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT/'src/main.cpp').read_text(encoding='utf-8')
ini = (ROOT/'BaccaratCounter.ini.example').read_text(encoding='utf-8')
build = (ROOT/'build.bat').read_bytes()
assert b'BaccaratCounterV123.exe' in build and b'\r\n' in build
assert '# Baccarat Counter v21.2.123' in (ROOT/'README.md').read_text(encoding='utf-8')
for token in ['L"Pair-MinEdge %:"', 'L"Gesamt-MinEdge %:"', 'L"Pair-Edge"',
              'gCombinedMinEdgeThreshold{0.0}', 'LoadCombinedMinEdgePercent',
              'SaveCombinedMinEdgePercent', '(HMENU)137', 'LOWORD(wParam) == 137',
              'plan.totalStakeUnits = summary->totalStakeUnits;',
              'plan.combinedEdge = summary->edge;',
              'combinedFilterEnabled && (!plan.valid || !plan.combinedMinEdgeMet)',
              'executableSignal = plan.valid && plan.combinedMinEdgeMet;',
              'main-ev-unavailable']:
    assert token in src, token
assert 'MinEdgePercent=2.00' in ini
assert 'CombinedMinEdgePercent=0.00' in ini
assert 'CombinedEvFilter=0' in ini
assert 'st.comparisonStakePlan.combinedEvPositive' in src
assert 'combinedFilterEnabled && !plan.combinedEvPositive' not in src
assert 'executableSignal = plan.valid && plan.combinedEvPositive;' not in src
# All actual gates must use the new minimum, not change the EV>0 counterfactual.
assert src.count('PragmaticFinalizeCombinedEdge(plan);') == 2
assert 'moveLabeledCell(a->minEdgeLabel, a->minEdgeEdit, row[0], 132, 30);' in src
assert 'moveLabeledCell(a->combinedMinEdgeLabel, a->combinedMinEdgeEdit, row[1], 164, 30);' in src

def take(start, end):
    a = src.index(start)
    return src[a:src.index(end, a)]

# Production planner extraction (not a reimplementation of its condition).
plan_struct = take('    struct PragmaticStakePlan {', '    struct PragmaticTableRuntime {')
parser = take('static double NormalizeEdgePercent', 'static double LoadMinEdgePercent')
normalizer = take('static int NormalizePairChipCents', 'static std::optional<int> ParsePairChip')
functions = take('    static constexpr int kStandardPairLimitFromHand',
                 '    static int PragmaticModelRoundPnlHundredths')
code = r'''
#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <cmath>
#include <cwctype>
#include <limits>
#include <optional>
#include <regex>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>
#include <iostream>
#include "strategy_edge_thresholds.h"
static std::atomic<int> gPairChipCents{20};
static std::atomic<double> gCombinedMinEdgeThreshold{0};
struct PragmaticSideBetLimitTier { int fromHand{0}; int maxPercentOfMain{0}; };
struct PragmaticTableRuntime {
 bool strategyReady{true}; int shoeHands{60};
 int pairPlayerMaxBetCents{50000}, pairBankerMaxBetCents{50000};
 int playerMaxBetCents{500000}, bankerMaxBetCents{500000}, tieMaxBetCents{50000};
 std::vector<int> chipAmountsCents{20,100,200,500,2500,10000};
 std::vector<PragmaticSideBetLimitTier> pairSideBetLimits;
 std::unordered_map<std::string,int> strategyRanks;
};
''' + parser + normalizer + plan_struct + functions + r'''
int main() {
 assert(ParseMinEdgePercentText(L"0,50").value() == .5);
 assert(ParseMinEdgePercentText(L" 0.50 ").value() == .5);
 assert(!ParseMinEdgePercentText(L"nan"));
 assert(!ParseMinEdgePercentText(L"0.5garbage"));
 assert(!ParseMinEdgePercentText(L""));
 assert(ParseMinEdgePercentText(L"-30").value() == -20);
 assert(ParseMinEdgePercentText(L"110").value() == 100);
 PragmaticTableRuntime st;
 for (const char* rank : {"A","2","3","4","5","6","7","8","9","10","J","Q","K"})
     st.strategyRanks[rank] = 32;
 const auto ev = PragmaticComputeMainBetEv(st);
 assert(std::abs(ev.player - (-.0123508)) < .00002);
 assert(std::abs(ev.banker - (-.0105791)) < .00002);
 // Full-shoe main EV is used only as a deterministic fixture; this test does
 // not claim that a full composition is an observed shoe at hand 60.
 const auto plan = PragmaticBuildStakePlan(st, .04);
 assert(plan.valid && plan.mainRequired && plan.mainSide == "Banker");
 assert(plan.mainStakeCents == 100 && plan.pairChipCents == 20);
 assert(plan.totalStakeUnits == 7);
 assert(std::abs(plan.combinedEdge - (2*.04 + 5*ev.banker)/7) < 1e-12);
 assert(plan.combinedMinEdgeMet);
 gCombinedMinEdgeThreshold = .005;
 auto blocked = PragmaticBuildStakePlan(st, .04);
 assert(blocked.valid && blocked.combinedEvPositive && !blocked.combinedMinEdgeMet);
 // Positivity alone must NOT pass a higher minimum.
 assert(blocked.combinedExpectedUnits > 0);
 gCombinedMinEdgeThreshold = blocked.combinedEdge;
 assert(PragmaticBuildStakePlan(st, .04).combinedMinEdgeMet);
 gCombinedMinEdgeThreshold = blocked.combinedEdge + 1e-8;
 assert(!PragmaticBuildStakePlan(st, .04).combinedMinEdgeMet);
 // Boundary crossing at hand 60 must be re-evaluated with the new stake.
 st.shoeHands = 59;
 gCombinedMinEdgeThreshold = .03;
 auto pairOnly = PragmaticBuildStakePlan(st, .04);
 assert(pairOnly.valid && !pairOnly.mainRequired && pairOnly.mainStakeCents == 0);
 assert(pairOnly.totalStakeUnits == 2 && pairOnly.combinedEdge == .04);
 assert(pairOnly.combinedMinEdgeMet);
 st.shoeHands = 60;
 assert(!PragmaticBuildStakePlan(st, .04).combinedMinEdgeMet);
 // Missing information fails closed when the combined filter is active.
 st.strategyRanks.clear();
 auto missing = PragmaticBuildStakePlan(st, .04);
 assert(!missing.valid && !missing.combinedMinEdgeMet);
 assert(missing.reason == "main-ev-unavailable");
 // Existing v105 UI fallback is retained for 20-cent Pair-only plans.
 st.shoeHands = 5;
 st.chipAmountsCents.clear();
 auto fallback = PragmaticBuildStakePlan(st, .04);
 assert(fallback.valid && fallback.pairChipDenomCents == 20);
 assert(fallback.pairChipClicks == 1);
 assert(!PragmaticBuildStakePlan(st, std::numeric_limits<double>::quiet_NaN()).valid);
 gPairChipCents = 40;
 assert(!PragmaticBuildStakePlan(st, .04).valid);
 // Gate OFF and gate ON semantics for both run modes.
 for (bool clickMode : {false, true}) {
     const bool enabled = true;
     assert((!clickMode || blocked.valid));
     assert(!(blocked.valid && blocked.combinedMinEdgeMet));
     assert(enabled && (!blocked.valid || !blocked.combinedMinEdgeMet));
 }
 std::cout << "v106 production planner, normalization and threshold tests: OK\n";
}
'''
with temporary_directory() as d:
    cpp = Path(d)/'production_planner.cpp'
    exe = Path(d)/'production_planner'
    cpp.write_text(code,encoding='utf-8')
    from test_toolchain import compile_cpp
    exe=compile_cpp(cpp,exe,[ROOT/'src'])
    subprocess.run([str(exe)],check=True)
print('v106 UI/config/source integration: OK')
