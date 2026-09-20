"""Execute production settlement/accounting with frozen signal thresholds."""
from pathlib import Path
import subprocess
from test_toolchain import temporary_directory, compile_cpp

root = Path(__file__).resolve().parents[1]
src = (root/'src/main.cpp').read_text(encoding='utf8')
def take(start, end):
    a = src.index(start)
    return src[a:src.index(end, a)]

settlement = take('            if (complete && st.comparisonGameId == *gameId &&',
                  '            if (complete && st.realMainBetGameId == *gameId &&')
assert 'gSessionConfiguredCombinedModel.Settle(' in settlement
assert 'modelRoundPnlHundredths, st.comparisonStakePlan.combinedMinEdge,' in settlement
assert 'st.comparisonStakePlan.combinedMinEdgeMet);' in settlement
assert 'gCombinedEvFilterEnabled' not in settlement
assert 'gCombinedMinEdgeThreshold' not in settlement
assert 'st.comparisonGameId.clear();' in settlement
assert 'configuredCombinedModelPnlHundredths' in settlement
assert 'configuredCombinedModelSignals' in settlement
assert src.index('st.comparisonStakePlan = plan;') < src.index('PRAGMATIC_SIGNAL_SUPPRESSED_COMBINED_EV_FILTER', src.index('st.comparisonStakePlan = plan;'))
snapshot = take('static session_export::Record SnapshotSessionRecord', 'static void QueueSessionSave')
for member in ['configuredCombinedEvModelUnitsHundredths', 'configuredCombinedEvModelSignals',
               'combinedMinEdgeUsedMinimum', 'combinedMinEdgeUsedMaximum']:
    assert member in snapshot
assert src.count('gSessionConfiguredCombinedModel.Reset();') == 1

code = r'''
#include <cassert>
#include <cmath>
#include <string>
#include <iostream>
#include "configured_edge_model.h"
#include "strategy_edge_thresholds.h"
#include "confirmed_bet_accounting.h"
''' + take('    struct PragmaticStakePlan {', '    struct PragmaticTableRuntime {') + take(
    '    static int PragmaticModelRoundPnlHundredths(', '    static std::string PragmaticPrettyName') + r'''
int main() {
    configured_edge_model::Session model;
    assert(model.Read().signals == 0 && model.Read().pnlHundredths == 0);
    assert(!model.Read().minimumUsed && !model.Read().maximumUsed);
    PragmaticStakePlan plan;
    plan.valid = true; plan.pairChipCents = 20;
    plan.mainRequired = true; plan.mainStakeCents = 100; plan.mainSide = "Banker";
    plan.combinedMinEdge = .0025;
    plan.combinedMinEdgeMet = strategy_edge_thresholds::MeetsMinimum(.002, plan.combinedMinEdge);
    assert(!plan.combinedMinEdgeMet); // Positive but below +0.25%.
    auto state = model.Settle(PragmaticModelRoundPnlHundredths(plan, true, false, "banker"),
                              plan.combinedMinEdge, plan.combinedMinEdgeMet);
    assert(state.signals == 0 && state.pnlHundredths == 0);
    assert(state.minimumUsed.value() == .0025); // Track excluded opportunities too.
    plan.combinedMinEdgeMet = strategy_edge_thresholds::MeetsMinimum(.0025, plan.combinedMinEdge);
    assert(plan.combinedMinEdgeMet); // Inclusive equality.
    // Simulate a later UI change: the frozen plan remains eligible.
    const double currentUiThreshold = .0225;
    assert(!strategy_edge_thresholds::MeetsMinimum(.0025, currentUiThreshold));
    state = model.Settle(PragmaticModelRoundPnlHundredths(plan, true, false, "banker"),
                          plan.combinedMinEdge, plan.combinedMinEdgeMet);
    assert(state.signals == 1 && state.pnlHundredths == 1475); // 10 pair + 4.75 main.
    state = model.Settle(PragmaticModelRoundPnlHundredths(plan, false, false, "player"), .0025, true);
    assert(state.signals == 2 && state.pnlHundredths == 775); // -2 pair -5 main.
    state = model.Settle(PragmaticModelRoundPnlHundredths(plan, false, false, "tie"), .0025, true);
    assert(state.signals == 3 && state.pnlHundredths == 575); // Tie pushes main only.
    assert(strategy_edge_thresholds::MeetsMinimum(0, 0));
    state = model.Settle(-200, 0, strategy_edge_thresholds::MeetsMinimum(0, 0));
    assert(state.signals == 4 && state.pnlHundredths == 375);
    assert(state.minimumUsed.value() == 0 && state.maximumUsed.value() == .0025);
    model.Settle(1000, .0225, false);
    assert(model.Read().maximumUsed.value() == .0225);
    plan.mainRequired = false;
    assert(PragmaticModelRoundPnlHundredths(plan, true, false, "banker") == 1000);
    model.Reset();
    assert(model.Read().signals == 0 && model.Read().pnlHundredths == 0);
    assert(!model.Read().minimumUsed && !model.Read().maximumUsed);
    std::cout << "v110 frozen threshold model, production P/L and reset: OK\n";
}
'''
with temporary_directory() as d:
    cpp = Path(d)/'model.cpp'
    cpp.write_text(code, encoding='utf8')
    exe = compile_cpp(cpp, Path(d)/'model', [root/'src'])
    subprocess.run([str(exe)], check=True)
print('v110 capture, export snapshot and live-filter independence: OK')
