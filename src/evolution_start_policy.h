#pragma once
#include <cstdint>

namespace evolution_start_policy {
struct Budget {
    unsigned attempts{0};
    std::uint64_t nextAllowed{0};
    bool denied{false};
    std::uint64_t healthySince{0}, lastHealthy{0};
    const char* Reason(std::uint64_t now) const {
        if (denied) return "explicit-launch-error";
        if (attempts >= 3) return "attempt-limit";
        if (now < nextAllowed) return "cooldown";
        return "ready";
    }
    bool Acquire(std::uint64_t now) {
        if (denied || attempts >= 3 || now < nextAllowed) return false;
        ++attempts;
        healthySince = lastHealthy = 0;
        nextAllowed = now + (attempts == 1 ? 60000ULL : 120000ULL);
        return true;
    }
    void ObserveHealthy(std::uint64_t now) {
        if (denied) return;
        if (!lastHealthy || now < lastHealthy || now - lastHealthy > 15000ULL)
            healthySince = now;
        lastHealthy = now;
        if (now >= healthySince && now - healthySince >= 60000ULL) {
            attempts = 0;
            nextAllowed = 0;
        }
    }
};
}
