// Included inside CdpMonitor. UI recovery never replaces the browser document.
    void MaybeRecoverEvolutionWidget() {
        if (provider_ != ProviderMode::Evolution || !evolutionWidgetRecoveryTick_ || evolutionExplicitSessionEnd_.load() ||
            evolutionLaunchErrorPaused_.load(std::memory_order_acquire)) return;
        const auto now = GetTickCount64();
        if (now < evolutionWidgetRecoveryTick_ || now - evolutionWidgetRecoveryTick_ > 32000) {
            evolutionWidgetRecoveryTick_ = 0;
            Log(L"EVOLUTION â€“ MULTIPLAY-Wiederherstellung abgebrochen; Kartenstaende bleiben gespeichert. Bitte MULTIPLAY manuell oeffnen.");
            return;
        }
        if (now - evolutionWidgetRecoveryPoll_ < 350) return;
        evolutionWidgetRecoveryPoll_ = now;
        std::string runtime;
        { std::lock_guard<std::mutex> lock(providerMu_); runtime = evolutionDataRuntimeSession_; }
        if (runtime.empty()) return;
        if (evolutionWidgetRecoveryRuntime_.empty()) evolutionWidgetRecoveryRuntime_ = runtime;
        if (runtime != evolutionWidgetRecoveryRuntime_) { evolutionWidgetRecoveryTick_ = 0; return; }
        std::string script = kEvolutionWidgetRecoveryScript;
        const std::string marker = "__EVO_RECOVERY_REQUEST__";
        const std::string request = "{\"runToken\":\"" + JsonEscape(scanRunToken_) +
            "\",\"request\":\"" + std::to_string(evolutionWidgetRecoveryTick_) +
            "\",\"stale\":" + (evolutionWidgetRecoveryStale_ ? "true" : "false") + "}";
        script.replace(script.find(marker), marker.size(), request);
        SendCommand("Runtime.evaluate", "{\"expression\":\"" + JsonEscape(script) +
                    "\",\"returnByValue\":true}", runtime);
    }

    void HandleEvolutionWidgetRecovery(const std::string& payload, const std::string& runtime) {
        if (!evolutionWidgetRecoveryTick_ || runtime != evolutionWidgetRecoveryRuntime_ ||
            ExtractJsonString(payload,"runToken").value_or("") != scanRunToken_ ||
            ExtractJsonString(payload,"request").value_or("") != std::to_string(evolutionWidgetRecoveryTick_)) return;
        const auto action = ExtractJsonString(payload,"action").value_or("");
        capture_.WriteRaw("{\"kind\":\"EVOLUTION_WIDGET_RECOVERY\",\"iso\":\"" + IsoNow() + "\",\"payload\":" + payload + "}");
        Log(L"EVOLUTION â€“ " + Utf8ToWide(ExtractJsonString(payload,"detail").value_or(action)));
        if(action=="CLOSE" || action=="OPEN") {
            const auto x=ExtractJsonDouble(payload,"x"),y=ExtractJsonDouble(payload,"y"),ts=ExtractJsonDouble(payload,"ts");
            const double now=static_cast<double>(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count());
            const int bit=action=="CLOSE"?1:2;
            if(!x||!y||!ts||!std::isfinite(*x)||!std::isfinite(*y)||!std::isfinite(*ts)||*x<0||*y<0||*x>20000||*y>20000||now<*ts||now-*ts>1000||(evolutionWidgetRecoveryClicks_&bit))return;
            evolutionWidgetRecoveryClicks_|=bit;
            const auto coords="\"x\":"+std::to_string(*x)+",\"y\":"+std::to_string(*y);
            SendCommand("Input.dispatchMouseEvent","{\"type\":\"mousePressed\","+coords+",\"button\":\"left\",\"buttons\":1,\"clickCount\":1}",runtime);
            SendCommand("Input.dispatchMouseEvent","{\"type\":\"mouseReleased\","+coords+",\"button\":\"left\",\"buttons\":0,\"clickCount\":1}",runtime);
        }
        if(action=="AUTH_REQUIRED"){EvolutionExplicitSessionEnd("inactivity-login-required");return;}
        if (action == "RECOVERED") {
            evolutionSessionExpiredPending_.store(false, std::memory_order_relaxed);
            evolutionSessionExpiredDetectedTick_.store(0, std::memory_order_relaxed);
            evolutionActionReadyTick_.store(GetTickCount64(), std::memory_order_relaxed);
            evolutionWidgetRecoveryTick_ = 0;
        } else if (action == "FAILED") evolutionWidgetRecoveryTick_ = 0;
    }
