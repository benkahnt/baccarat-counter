#pragma once

#include <cmath>
#include <optional>

// v21.2.106: pure, portable stake-normalization and threshold comparison.
// This does not estimate card probabilities or change the existing EV model.
namespace strategy_edge_thresholds {

struct TotalEdge {
    double totalStakeUnits; // One Unit is the stake on ONE Pair side.
    double edge;            // Fraction of total stake; 0.005 means +0.50%.
};

inline std::optional<TotalEdge> FromExpectedUnits(
        double expectedUnits, int pairStakeCents, int mainStakeCents) {
    if (!std::isfinite(expectedUnits) || pairStakeCents <= 0 || mainStakeCents < 0)
        return std::nullopt;
    // Convert before adding; never add potentially large cent integers.
    const double totalUnits = 2.0 +
        static_cast<double>(mainStakeCents) / static_cast<double>(pairStakeCents);
    const double edge = expectedUnits / totalUnits;
    if (!std::isfinite(totalUnits) || totalUnits <= 0.0 || !std::isfinite(edge))
        return std::nullopt;
    return TotalEdge{totalUnits, edge};
}

inline bool MeetsMinimum(double edge, double minimumEdge) {
    // Compare unrounded fractions. A small machine-arithmetic tolerance is
    // used only at equality; no display rounding may authorize a bet.
    if (!std::isfinite(edge) || !std::isfinite(minimumEdge)) return false;
    constexpr double epsilon = 1e-12;
    return edge >= minimumEdge || minimumEdge - edge <= epsilon;
}

} // namespace strategy_edge_thresholds
