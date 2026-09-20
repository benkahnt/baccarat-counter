#include <cassert>
#include <algorithm>

class SessionLimitModel {
public:
    SessionLimitModel(int target, int stopLoss)
        : target_(std::max(1, target)),
          stopLoss_(stopLoss > 0 ? -stopLoss : std::min(-1, stopLoss)),
          warning_(std::min(-1, stopLoss_ + 10)) {}

    void ArmSignalRound(int pairBets = 2) {
        if (!CanEmitSignal()) return;
        pnl_ -= pairBets;
    }

    enum class Result { None, Warning, Target, StopLoss };

    Result CompleteSignalRound(int pairHits) {
        pnl_ += 12 * pairHits;
        if (!warningSent_ && pnl_ <= warning_) {
            warningSent_ = true;
            if (pnl_ <= stopLoss_) {
                stopped_ = true;
                return Result::StopLoss;
            }
            return Result::Warning;
        }
        if (!stopped_ && pnl_ >= target_) {
            stopped_ = true;
            return Result::Target;
        }
        if (!stopped_ && pnl_ <= stopLoss_) {
            stopped_ = true;
            return Result::StopLoss;
        }
        return Result::None;
    }

    bool CanEmitSignal() const { return !stopped_; }
    bool WarningSent() const { return warningSent_; }
    int Warning() const { return warning_; }
    int Pnl() const { return pnl_; }

private:
    int target_;
    int stopLoss_;
    int warning_;
    int pnl_{0};
    bool warningSent_{false};
    bool stopped_{false};
};

int main() {
    // Existing +20 target behavior stays intact.
    SessionLimitModel target20(20, -50);
    target20.ArmSignalRound();
    assert(target20.CompleteSignalRound(1) == SessionLimitModel::Result::None);
    assert(target20.Pnl() == 10);
    target20.ArmSignalRound();
    assert(target20.CompleteSignalRound(0) == SessionLimitModel::Result::None);
    assert(target20.Pnl() == 8);
    target20.ArmSignalRound();
    assert(target20.CompleteSignalRound(1) == SessionLimitModel::Result::None);
    assert(target20.Pnl() == 18);
    target20.ArmSignalRound();
    assert(target20.CompleteSignalRound(1) == SessionLimitModel::Result::Target);
    assert(target20.Pnl() == 28);
    assert(!target20.CanEmitSignal());

    // Default -50 Stoploss: exactly one warning at -40 and hard stop at -50.
    SessionLimitModel loss(20, -50);
    assert(loss.Warning() == -40);
    for (int i = 0; i < 19; ++i) {
        loss.ArmSignalRound();
        assert(loss.CompleteSignalRound(0) == SessionLimitModel::Result::None);
    }
    assert(loss.Pnl() == -38);
    loss.ArmSignalRound();
    assert(loss.CompleteSignalRound(0) == SessionLimitModel::Result::Warning);
    assert(loss.Pnl() == -40);
    assert(loss.WarningSent());
    for (int i = 0; i < 4; ++i) {
        loss.ArmSignalRound();
        assert(loss.CompleteSignalRound(0) == SessionLimitModel::Result::None);
    }
    assert(loss.Pnl() == -48);
    loss.ArmSignalRound();
    assert(loss.CompleteSignalRound(0) == SessionLimitModel::Result::StopLoss);
    assert(loss.Pnl() == -50);
    assert(!loss.CanEmitSignal());

    // Positive input is normalized to a negative floor; warning stays 10u above it.
    SessionLimitModel normalized(20, 80);
    assert(normalized.Warning() == -70);

    return 0;
}
