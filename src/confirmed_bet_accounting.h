#pragma once

#include <cmath>
#include <string>

namespace confirmed_bet_accounting {

constexpr int kPlayerPair = 1;
constexpr int kBankerPair = 2;
constexpr int kBothPairs = kPlayerPair | kBankerPair;

inline int NormalizePairMask(int mask) {
    return mask & kBothPairs;
}

inline int PairBetCount(int mask) {
    mask = NormalizePairMask(mask);
    return ((mask & kPlayerPair) ? 1 : 0) +
           ((mask & kBankerPair) ? 1 : 0);
}

inline int PairHitCount(int mask, bool playerPair, bool bankerPair) {
    mask = NormalizePairMask(mask);
    return ((mask & kPlayerPair) && playerPair ? 1 : 0) +
           ((mask & kBankerPair) && bankerPair ? 1 : 0);
}

inline int RoundPnlUnits(int mask, bool playerPair, bool bankerPair) {
    return 12 * PairHitCount(mask, playerPair, bankerPair) - PairBetCount(mask);
}

// Net profit in 1/100 unit. Standard commission Baccarat, Tie pays 8:1.
// Player/Banker push on a tie; a Tie wager loses on either non-tie outcome.
inline int MainNetHundredths(const std::string& side, const std::string& result,
                             int stakeUnitsHundredths) {
    if (stakeUnitsHundredths <= 0) return 0;
    if (side == "Tie")
        return result == "tie" ? 8 * stakeUnitsHundredths : -stakeUnitsHundredths;
    if (result == "tie") return 0;
    if (side == "Player" && result == "player") return stakeUnitsHundredths;
    if (side == "Banker" && result == "banker")
        return static_cast<int>(std::llround(stakeUnitsHundredths * 0.95));
    return -stakeUnitsHundredths;
}

// The stake has already been debited on confirmed placement.
inline int MainReturnedHundredths(const std::string& side, const std::string& result,
                                  int stakeUnitsHundredths) {
    return stakeUnitsHundredths + MainNetHundredths(side, result, stakeUnitsHundredths);
}

}  // namespace confirmed_bet_accounting
