#pragma once
#include <cstdint>

namespace connection_health {
inline std::uint64_t Age(std::uint64_t now, std::uint64_t tick) {
    return tick && now >= tick ? now - tick : 0;
}
struct Decision {
    bool domStale{};
    bool gameStale{};
    bool cardsStale{};
    bool Recover() const { return domStale || gameStale || cardsStale; }
    bool FeedStale() const { return gameStale || cardsStale; }
};
inline Decision Evaluate(std::uint64_t now, std::uint64_t ready,
                         std::uint64_t main, std::uint64_t game,
                         std::uint64_t cards, int observedSideTables) {
    Decision out;
    // UI readiness is useful for a UI failure, but never a prerequisite for
    // detecting a transport outage that has already been observed directly.
    out.domStale = ready && main && Age(now, ready) >= 8000 && Age(now, main) <= 7000;
    out.gameStale = game && Age(now, game) >= 12000;
    // Control/timer messages can continue while the card feed is stuck.
    // Apply this aggregate check only to a previously active multi-table feed.
    out.cardsStale = observedSideTables >= 5 && cards && Age(now, cards) >= 45000;
    return out;
}
}
