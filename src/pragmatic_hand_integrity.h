#pragma once
#include <string>
#include <vector>

namespace pragmatic_hand_integrity {
struct Result {
    bool valid{false};
    int playerPoints{-1};
    int bankerPoints{-1};
    std::string reason;
};

inline int Points(const std::vector<std::string>& cards) {
    int sum = 0;
    for (const auto& card : cards) {
        if (card.size() < 2 || std::string("CDHS").find(card.back()) == std::string::npos)
            return -1;
        const auto rank = card.substr(0, card.size() - 1);
        if (rank == "A") ++sum;
        else if (rank.size() == 1 && rank[0] >= '2' && rank[0] <= '9') sum += rank[0] - '0';
        else if (rank != "10" && rank != "J" && rank != "Q" && rank != "K") return -1;
    }
    return sum % 10;
}

inline Result Check(const std::vector<std::string>& player,
                    const std::vector<std::string>& banker,
                    const std::string& reportedWinner) {
    Result r;
    if (player.size() < 2 || player.size() > 3 || banker.size() < 2 || banker.size() > 3) {
        r.reason = "invalid-card-count-or-side-count";
        return r;
    }
    r.playerPoints = Points(player);
    r.bankerPoints = Points(banker);
    if (r.playerPoints < 0 || r.bankerPoints < 0) r.reason = "invalid-card-code";
    else if (reportedWinner != "player" && reportedWinner != "banker" && reportedWinner != "tie")
        r.reason = "unknown-result";
    else {
        const std::string derived = r.playerPoints > r.bankerPoints ? "player" :
            r.bankerPoints > r.playerPoints ? "banker" : "tie";
        if (derived != reportedWinner) r.reason = "cards-winner-mismatch";
        else r.valid = true;
    }
    return r;
}
}
