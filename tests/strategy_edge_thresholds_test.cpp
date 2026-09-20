#include "../src/strategy_edge_thresholds.h"
#include <cassert>
#include <climits>
#include <limits>

int main() {
    using namespace strategy_edge_thresholds;
    // +4% per Pair, -1% main, ratio 1:1:5. Net +.03 Pair-Units is
    // +.428571% of total stake, NOT +3% and NOT +.03%.
    auto e = FromExpectedUnits(2 * .04 + 5 * -.01, 20, 100);
    assert(e && e->totalStakeUnits == 7.0);
    assert(std::abs(e->edge - .004285714285714286) < 1e-14);
    assert(MeetsMinimum(e->edge, .004));
    assert(!MeetsMinimum(e->edge, .005));
    assert(MeetsMinimum(e->edge, e->edge));
    assert(!MeetsMinimum(e->edge, e->edge + 1e-9));
    // A zero minimum means break-even or better; the EV>0 comparison model
    // remains a separate strict comparison in main.cpp.
    assert(MeetsMinimum(0, 0));
    assert(!MeetsMinimum(-.001, 0));
    assert(MeetsMinimum(-.001, -.002));
    assert(!MeetsMinimum(-.003, -.002));
    // No compulsory main bet: equal Pair stakes -> exactly the Pair edge.
    e = FromExpectedUnits(2 * .02, 20, 0);
    assert(e && e->totalStakeUnits == 2 && e->edge == .02);
    // Different currency scale does not change the normalized edge.
    auto scaled = FromExpectedUnits(.03, 200, 1000);
    auto small = FromExpectedUnits(.03, 20, 100);
    assert(scaled && small && scaled->edge == small->edge);
    // Use the actual rounded main stake, not an assumed factor of 5.
    e = FromExpectedUnits(.01, 30, 200);
    assert(e && std::abs(e->edge - .01 / (2 + 200.0/30)) < 1e-14);
    const double nan = std::numeric_limits<double>::quiet_NaN();
    const double inf = std::numeric_limits<double>::infinity();
    assert(!FromExpectedUnits(nan, 20, 100));
    assert(!FromExpectedUnits(inf, 20, 100));
    assert(!FromExpectedUnits(.03, 0, 100));
    assert(!FromExpectedUnits(.03, -20, 100));
    assert(!FromExpectedUnits(.03, 20, -1));
    assert(!MeetsMinimum(nan, 0) && !MeetsMinimum(0, nan));
    assert(!MeetsMinimum(inf, 0) && !MeetsMinimum(0, inf));
    e = FromExpectedUnits(0, INT_MAX, INT_MAX);
    assert(e && e->totalStakeUnits == 3 && e->edge == 0);
}
