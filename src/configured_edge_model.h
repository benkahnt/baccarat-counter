#pragma once

#include <algorithm>
#include <mutex>
#include <optional>

namespace configured_edge_model {

struct Snapshot {
    int pnlHundredths{0};
    int signals{0};
    std::optional<double> minimumUsed;
    std::optional<double> maximumUsed;
};

// Only resolved, valid Pair-MinEdge opportunities reach this accumulator.
// Eligibility and threshold are frozen in the stake plan at signal time.
// Live filter state and later setting changes must not affect this model.
class Session {
public:
    Snapshot Settle(int roundPnlHundredths, double minimumAtSignal, bool minimumMet) {
        std::lock_guard<std::mutex> lock(mutex_);
        state_.minimumUsed = std::min(state_.minimumUsed.value_or(minimumAtSignal), minimumAtSignal);
        state_.maximumUsed = std::max(state_.maximumUsed.value_or(minimumAtSignal), minimumAtSignal);
        if (minimumMet) {
            state_.pnlHundredths += roundPnlHundredths;
            ++state_.signals;
        }
        return state_;
    }

    Snapshot Read() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return state_;
    }

    void Reset() {
        std::lock_guard<std::mutex> lock(mutex_);
        state_ = {};
    }

private:
    mutable std::mutex mutex_;
    Snapshot state_;
};

} // namespace configured_edge_model
