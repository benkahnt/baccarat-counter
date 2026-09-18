#pragma once
#include <windows.h>

// Thread-scoped idle-sleep prevention, released on every worker exit path.
// Does not change the power plan, screen timeout or explicit user sleep.
class MonitorAwake {
public:
    explicit MonitorAwake(bool enabled) {
        if (enabled) held_ = SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED) != 0;
    }
    ~MonitorAwake() { if (held_) SetThreadExecutionState(ES_CONTINUOUS); }
    bool Held() const { return held_; }
    MonitorAwake(const MonitorAwake&) = delete;
    MonitorAwake& operator=(const MonitorAwake&) = delete;
private:
    bool held_{};
};
