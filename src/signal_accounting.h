#pragma once

#include <cstdint>
#include <mutex>
#include <string>
#include <unordered_map>

namespace signal_accounting {

struct Snapshot {
    int paperSignals{0};
    int paperPairHundredths{0};
    int paperMainHundredths{0};
    int actualPairHundredths{0};
    int actualMainHundredths{0};
    std::uint64_t revision{0};
    int PaperTotal() const { return paperPairHundredths + paperMainHundredths; }
    int ActualTotal() const { return actualPairHundredths + actualMainHundredths; }
};

// Receives the existing model's resolved result; never recalculates strategy.
// Only the frozen live-policy decision may call RecordPaper. Actual entries
// exclusively come from confirmed placement debit/settlement callbacks.
class Session {
public:
    bool RecordPaper(const std::string& table, const std::string& game,
                     int pairHundredths, int totalHundredths) {
        if (table.empty() || game.empty()) return false;
        std::lock_guard<std::mutex> lock(mutex_);
        auto& entry = tables_[table];
        if (entry.lastPaperGame == game) return false;
        entry.lastPaperGame = game;
        for (auto* value : {&entry.value, &total_}) {
            ++value->paperSignals;
            value->paperPairHundredths += pairHundredths;
            value->paperMainHundredths += totalHundredths - pairHundredths;
            ++value->revision;
        }
        return true;
    }

    void RecordActualDelta(const std::string& table, int pairHundredths,
                           int mainHundredths) {
        std::lock_guard<std::mutex> lock(mutex_);
        for (auto* value : {&tables_[table].value, &total_}) {
            value->actualPairHundredths += pairHundredths;
            value->actualMainHundredths += mainHundredths;
            ++value->revision;
        }
    }

    Snapshot Read() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return total_;
    }

    Snapshot ReadTable(const std::string& table) const {
        std::lock_guard<std::mutex> lock(mutex_);
        const auto found = tables_.find(table);
        return found == tables_.end() ? Snapshot{} : found->second.value;
    }

    void Reset() {
        std::lock_guard<std::mutex> lock(mutex_);
        total_ = {};
        tables_.clear();
    }

private:
    struct Entry { Snapshot value; std::string lastPaperGame; };
    mutable std::mutex mutex_;
    Snapshot total_;
    std::unordered_map<std::string, Entry> tables_;
};

} // namespace signal_accounting
