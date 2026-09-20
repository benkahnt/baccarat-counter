#include "../src/confirmed_bet_accounting.h"

#include <cassert>

int main() {
    using namespace confirmed_bet_accounting;

    assert(PairBetCount(0) == 0);
    assert(PairBetCount(kPlayerPair) == 1);
    assert(PairBetCount(kBankerPair) == 1);
    assert(PairBetCount(kBothPairs) == 2);

    assert(RoundPnlUnits(kBothPairs, false, false) == -2);
    assert(RoundPnlUnits(kBothPairs, true, false) == 10);
    assert(RoundPnlUnits(kBothPairs, false, true) == 10);
    assert(RoundPnlUnits(kBothPairs, true, true) == 22);

    assert(RoundPnlUnits(kPlayerPair, false, false) == -1);
    assert(RoundPnlUnits(kPlayerPair, true, false) == 11);
    assert(RoundPnlUnits(kPlayerPair, false, true) == -1);

    assert(RoundPnlUnits(kBankerPair, false, false) == -1);
    assert(RoundPnlUnits(kBankerPair, false, true) == 11);
    assert(RoundPnlUnits(kBankerPair, true, false) == -1);

    // Unknown bits must never create phantom bets or hits.
    assert(NormalizePairMask(7) == kBothPairs);
    assert(RoundPnlUnits(4, true, true) == 0);
}
