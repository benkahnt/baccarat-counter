    void MaybeQueueEvolutionSignal(const std::string& payload, const std::string& tableId) {
        if (provider_ != ProviderMode::Evolution || startupPrepareOnly_ ||
            gPragmaticAutoBetMode.load() != 2 || evolutionSessionExpiredPending_.load() ||
            evolutionWidgetRecoveryTick_ || gUnitTargetReached.load() || gStopLossReached.load()) return;
        const auto it = evolutionModels_.find(tableId);
        const auto edge = ExtractJsonDouble(payload,"luckyPairEdge");
        const auto game = ExtractJsonString(payload,"gameId").value_or("");
        if (it == evolutionModels_.end() || !it->second.shoe.strategyReady || !edge || game.empty() ||
            ExtractJsonString(payload,"betting").value_or("") != "BetsOpen" ||
            ExtractJsonString(payload,"dealing").value_or("") == "Finished" ||
            !strategy_edge_thresholds::MeetsMinimum(*edge,gMinEdgeThreshold.load())) return;
        const auto plan = PragmaticBuildStakePlan(it->second.shoe,*edge,true);
        if (!plan.valid || (gCombinedEvFilterEnabled.load() && !plan.combinedMinEdgeMet)) return;
        const std::string key=tableId+"|"+game;
        if (evolutionSignalAttempted_.count(key)) return;
        std::lock_guard<std::mutex> lock(pragmaticManualChipTestMu_);
        if (pragmaticManualChipTestPending_) return;
        ManualChipTestRequest request{tableId,GetTickCount64(),0,false};
        request.evolutionSignal=true;request.targetGameId=game;
        request.mainSide=plan.mainRequired?plan.mainSide:"Banker";
        request.mainCents=plan.mainRequired?plan.mainStakeCents:0;
        request.pairCents=plan.pairChipCents;
        pragmaticManualChipTestPending_=request;
        evolutionSignalAttempted_.insert(key);
    }

    struct EvolutionConfirmedWager {
        ManualChipTestRequest request;
        int mainCents=0,playerPairCents=0,bankerPairCents=0;
    };
    struct EvolutionSettledWager {
        EvolutionConfirmedWager bet;
        int pairPnlHundredths=0,mainPnlHundredths=0;
        int Total() const {return pairPnlHundredths+mainPnlHundredths;}
    };
    std::unordered_map<std::string,ManualChipTestRequest> evolutionWagerCandidates_;
    std::unordered_map<std::string,EvolutionConfirmedWager> evolutionAcceptedWagers_;

    void RecordEvolutionAcceptedWager(const std::string& payload) {
        const auto table=ExtractJsonString(payload,"tableId").value_or("");
        const auto game=ExtractJsonString(payload,"gameId").value_or("");
        const auto key=table+"|"+game;
        const auto candidate=evolutionWagerCandidates_.find(key);
        if(candidate==evolutionWagerCandidates_.end())return;
        const auto& request=candidate->second;
        const auto player=ExtractJsonInt(payload,"Player"),banker=ExtractJsonInt(payload,"Banker"),tie=ExtractJsonInt(payload,"Tie");
        const auto pp=ExtractJsonInt(payload,"PlayerPair"),bp=ExtractJsonInt(payload,"BankerPair");
        if(!player||!banker||!tie||!pp||!bp||*player<0||*banker<0||*tie<0||*pp<0||*bp<0)return;
        const int main=request.mainSide=="Player"?*player:request.mainSide=="Tie"?*tie:*banker;
        if(*player> (request.mainSide=="Player"?request.mainCents:0) ||
           *banker> (request.mainSide=="Banker"?request.mainCents:0) ||
           *tie> (request.mainSide=="Tie"?request.mainCents:0) || *pp>request.pairCents || *bp>request.pairCents)return;
        auto& recorded=evolutionAcceptedWagers_[key];
        const auto units=[&](int cents){return static_cast<int>(std::llround(cents*100.0/request.pairCents));};
        gSessionSignalAccounting.RecordActualDelta(table,
            units(recorded.playerPairCents+recorded.bankerPairCents)-units(*pp+*bp),units(recorded.mainCents)-units(main));
        recorded={request,main,*pp,*bp};
        capture_.WriteRaw("{\"kind\":\"EVOLUTION_CONFIRMED_WAGER\",\"iso\":\""+IsoNow()+"\",\"payload\":"+payload+"}");
    }

    std::optional<EvolutionSettledWager> SettleEvolutionAcceptedWager(const std::string& payload,const std::string& tableId,
                                     bool playerPair,bool bankerPair) {
        const auto game=ExtractJsonString(payload,"gameId").value_or("");
        const auto key=tableId+"|"+game;
        const auto it=evolutionAcceptedWagers_.find(key);
        if(it==evolutionAcceptedWagers_.end()){evolutionWagerCandidates_.erase(key);return std::nullopt;}
        std::string winner=ExtractJsonString(payload,"winner").value_or("");
        std::transform(winner.begin(),winner.end(),winner.begin(),[](unsigned char c){return static_cast<char>(std::tolower(c));});
        if(winner!="player"&&winner!="banker"&&winner!="tie")return std::nullopt;
        const auto bet=it->second;
        const auto units=[&](int cents){return static_cast<int>(std::llround(cents*100.0/bet.request.pairCents));};
        const int mainUnits=units(bet.mainCents);
        const int mainReturn=mainUnits+confirmed_bet_accounting::MainNetHundredths(bet.request.mainSide,winner,mainUnits);
        const int pairReturn=12*units((playerPair?bet.playerPairCents:0)+(bankerPair?bet.bankerPairCents:0));
        const EvolutionSettledWager settled{bet,pairReturn-units(bet.playerPairCents+bet.bankerPairCents),mainReturn-mainUnits};
        gSessionSignalAccounting.RecordActualDelta(tableId,pairReturn,mainReturn);
        capture_.WriteRaw("{\"kind\":\"EVOLUTION_CONFIRMED_WAGER_RESULT\",\"iso\":\""+IsoNow()+"\",\"tableid\":\""+JsonEscape(tableId)+"\",\"gameId\":\""+JsonEscape(game)+"\",\"mainReturnHundredths\":"+std::to_string(mainReturn)+"}");
        evolutionAcceptedWagers_.erase(it);evolutionWagerCandidates_.erase(key);
        return settled;
    }

// Included inside CdpMonitor after EvolutionModelState and its planner.
    void FinishEvolutionChipTest(const std::string& reason) {
        std::lock_guard<std::mutex> guard(pragmaticManualChipTestMu_);
        pragmaticManualChipTestPending_.reset();
        evolutionTestRequestTick_ = 0;
        evolutionTestRuntime_.clear();
        Log(L"EVOLUTION WETTE - " + Utf8ToWide(reason));
    }

    void MaybeStartEvolutionChipTest() {
        if (provider_ != ProviderMode::Evolution || startupPrepareOnly_) return;
        std::optional<ManualChipTestRequest> request;
        { std::lock_guard<std::mutex> guard(pragmaticManualChipTestMu_);
          request = pragmaticManualChipTestPending_; }
        if (!request) return;
        if (request->evolutionSignal) {
            const auto it=evolutionModels_.find(request->tableId);
            if(gPragmaticAutoBetMode.load()!=2 || gUnitTargetReached.load() || gStopLossReached.load() ||
               it==evolutionModels_.end() || !it->second.shoe.strategyReady ||
               it->second.gameId!=request->targetGameId || !it->second.livePolicyAllowed) {
                FinishEvolutionChipTest("Signal nicht mehr gueltig; keine weiteren Klicks.");return;
            }
            const auto current=PragmaticBuildStakePlan(it->second.shoe,it->second.pairEdge,true);
            if(!strategy_edge_thresholds::MeetsMinimum(it->second.pairEdge,gMinEdgeThreshold.load()) ||
               !current.valid || (gCombinedEvFilterEnabled.load()&&!current.combinedMinEdgeMet) ||
               current.pairChipCents!=request->pairCents || current.mainStakeCents!=request->mainCents ||
               (current.mainRequired && current.mainSide!=request->mainSide)) {
                FinishEvolutionChipTest("Filter oder Einsatz geaendert; keine weiteren Klicks.");return;
            }
        }
        const ULONGLONG now = GetTickCount64();
        if (now < request->requestedTick || now - request->requestedTick > 90000ULL) {
            FinishEvolutionChipTest("90 Sekunden abgelaufen; keine weiteren Klicks."); return;
        }
        if (evolutionExplicitSessionEnd_.load() || evolutionWidgetRecoveryTick_ || evolutionLaunchErrorPaused_.load(std::memory_order_acquire) ||
            evolutionSessionRecoveryActive_.load(std::memory_order_relaxed) ||
            evolutionSessionExpiredPending_.load(std::memory_order_relaxed)) {
            FinishEvolutionChipTest("Sitzung unterbrochen oder Wiederverbindung aktiv."); return;
        }
        if (now >= evolutionTestLastPoll_ && now - evolutionTestLastPoll_ < 350ULL) return;
        evolutionTestLastPoll_ = now;
        std::string runtime;
        { std::lock_guard<std::mutex> guard(providerMu_);
          runtime = evolutionDataRuntimeSession_.empty() ? evolutionActionRuntimeSession_
                                                        : evolutionDataRuntimeSession_; }
        if (runtime.empty()) return;
        if (evolutionTestRequestTick_ != request->requestedTick) {
            const auto it = evolutionModels_.find(request->tableId);
            if (it != evolutionModels_.end() && IsExcludedBaccaratVariantName(it->second.shoe.name)) {
                FinishEvolutionChipTest("Ausgeschlossene Baccarat-Variante."); return;
            }
            PragmaticTableRuntime sample;
            bool standard = it == evolutionModels_.end() || !it->second.shoe.strategyReady;
            if (!standard) sample = it->second.shoe;
            else {
                sample.strategyReady = true;
                for (const char* rank : {"A","2","3","4","5","6","7","8","9","10","J","Q","K"})
                    sample.strategyRanks[rank] = 32;
            }
            const auto ev = PragmaticComputeMainBetEv(sample);
            evolutionTestMainSide_ = "Banker";
            double best = ev.banker;
            if (ev.player > best) { best = ev.player; evolutionTestMainSide_ = "Player"; }
            if (ev.tie > best) evolutionTestMainSide_ = "Tie";
            if(request->evolutionSignal) evolutionTestMainSide_=request->mainSide;
            evolutionTestRequestTick_ = request->requestedTick;
            evolutionTestLastSequence_ = 0;
            evolutionTestRuntime_ = runtime;
            evolutionTestGame_.clear();
            capture_.WriteRaw("{\"kind\":\"EVOLUTION_PLACEMENT_REQUEST\",\"iso\":\"" + IsoNow() +
                "\",\"tableid\":\"" + JsonEscape(request->tableId) + "\",\"mainSide\":\"" + evolutionTestMainSide_ +
                "\",\"mainCents\":" + std::to_string(request->mainCents) + ",\"pairCents\":" + std::to_string(request->pairCents) +
                ",\"signal\":" + (request->evolutionSignal?"true":"false") + ",\"standardEightDeckAssumption\":" + (standard?"true":"false") + "}");
            Log((request->evolutionSignal ? std::wstring(L"EVOLUTION SIGNAL-WETTE - ") : std::wstring(L"EVOLUTION TEST-WETTE - ")) +
                Utf8ToWide(evolutionTestMainSide_) + L" " + FormatTelegramMoneyMinor(request->mainCents,1) +
                L" + je " + FormatTelegramMoneyMinor(request->pairCents,1) + L" P Pair/B Pair. " +
                (standard ? std::wstring(L"Testannahme: frischer 8-Deck-Schuh.") : std::wstring(L"Hauptwette aus bekanntem Kartenbestand berechnet.")));
        }
        if (evolutionTestRuntime_ != runtime) {
            FinishEvolutionChipTest("Anbieter-Runtime gewechselt; neuer Test erforderlich."); return;
        }
        if(!request->evolutionSignal && evolutionTestGame_.empty()) {
            PragmaticTableRuntime current;
            const auto it=evolutionModels_.find(request->tableId);
            if(it!=evolutionModels_.end()&&it->second.shoe.strategyReady)current=it->second.shoe;
            else {current.strategyReady=true;for(const char* rank:{"A","2","3","4","5","6","7","8","9","10","J","Q","K"})current.strategyRanks[rank]=32;}
            const auto ev=PragmaticComputeMainBetEv(current);
            evolutionTestMainSide_=ev.player>ev.banker?"Player":"Banker";
            if(ev.tie>std::max(ev.player,ev.banker))evolutionTestMainSide_="Tie";
        }
        const std::string requestJson = "{\"runToken\":\"" + JsonEscape(scanRunToken_) +
            "\",\"request\":\"" + std::to_string(request->requestedTick) +
            "\",\"tableId\":\"" + JsonEscape(request->tableId) +
            "\",\"mainSide\":\"" + evolutionTestMainSide_ + "\",\"signal\":" +
            (request->evolutionSignal ? "true" : "false") + ",\"targetGameId\":\"" + JsonEscape(request->targetGameId) +
            "\",\"mainCents\":" + std::to_string(request->mainCents) + ",\"pairCents\":" + std::to_string(request->pairCents) + "}";
        std::string script = kEvolutionChipTestScript;
        const std::string marker = "__EVO_TEST_REQUEST__";
        script.replace(script.find(marker), marker.size(), requestJson);
        SendCommand("Runtime.evaluate", "{\"expression\":\"" + JsonEscape(script) +
            "\",\"awaitPromise\":false,\"returnByValue\":true}", runtime);
    }

    void HandleEvolutionChipTestEvent(const std::string& payload, const std::string& runtime) {
        if (provider_ != ProviderMode::Evolution || stop_.load(std::memory_order_acquire)) return;
        std::optional<ManualChipTestRequest> request;
        { std::lock_guard<std::mutex> guard(pragmaticManualChipTestMu_);
          request = pragmaticManualChipTestPending_; }
        if (!request || runtime != evolutionTestRuntime_ ||
            ExtractJsonString(payload, "runToken").value_or("") != scanRunToken_ ||
            ExtractJsonString(payload, "request").value_or("") != std::to_string(request->requestedTick) ||
            ExtractJsonString(payload, "tableId").value_or("") != request->tableId) return;
        const std::string action = ExtractJsonString(payload, "action").value_or("");
        const std::string detail = ExtractJsonString(payload, "detail").value_or("");
        capture_.WriteRaw("{\"kind\":\"EVOLUTION_MANUAL_CHIP_TEST_STEP\",\"iso\":\"" +
            IsoNow() + "\",\"payload\":" + payload + "}");
        if (action == "FAILED" || action == "CANCELLED" || action == "SUCCESS") {
            FinishEvolutionChipTest(action + ": " + detail); return;
        }
        if (action == "WAIT" || action == "STORED") {
            Log(L"EVOLUTION WETTE - " + Utf8ToWide(detail)); return;
        }
        if (action != "CLICK") return;
        if(request->evolutionSignal && (gPragmaticAutoBetMode.load()!=2 ||
           gUnitTargetReached.load() || gStopLossReached.load())) {
            FinishEvolutionChipTest("Automatisches Setzen gestoppt; keine weiteren Klicks.");return;
        }
        const auto sequence = ExtractJsonInt(payload, "seq");
        const double x = ExtractJsonDouble(payload, "x").value_or(-1.0);
        const double y = ExtractJsonDouble(payload, "y").value_or(-1.0);
        const double ts = ExtractJsonDouble(payload, "ts").value_or(0.0);
        const double wallNow = static_cast<double>(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count());
        const auto now = GetTickCount64();
        if (!sequence || *sequence <= evolutionTestLastSequence_ || !std::isfinite(x) ||
            !std::isfinite(y) || x < 0 || y < 0 || x > 20000 || y > 20000 ||
            !std::isfinite(ts) || wallNow < ts || wallNow - ts > 750 ||
            now < request->requestedTick || now - request->requestedTick > 90000ULL ||
            evolutionExplicitSessionEnd_.load() || evolutionWidgetRecoveryTick_ || evolutionLaunchErrorPaused_.load(std::memory_order_acquire) ||
            evolutionSessionRecoveryActive_.load(std::memory_order_relaxed) ||
            evolutionSessionExpiredPending_.load(std::memory_order_relaxed)) {
            FinishEvolutionChipTest("Klickanforderung veraltet oder Sitzung nicht bereit."); return;
        }
        const std::string kind = ExtractJsonString(payload, "kind").value_or("");
        if (kind != "chip" && kind != "toggle" && kind != "wager") return;
        if (kind == "wager") {
            const std::string game = ExtractJsonString(payload, "gameId").value_or("");
            const std::string key = request->tableId + "|" + game;
            if (game.empty() || (!evolutionTestGame_.empty() && game != evolutionTestGame_) ||
                (evolutionTestGame_.empty() && evolutionTestUsedGames_.count(key))) {
                FinishEvolutionChipTest("Runde unklar oder in dieser Runde bereits getestet."); return;
            }
            evolutionTestGame_ = game;
            evolutionTestUsedGames_.insert(key);
            if(request->evolutionSignal && !evolutionWagerCandidates_.count(key)) {
                auto candidate=*request;candidate.mainSide=evolutionTestMainSide_;
                evolutionWagerCandidates_[key]=candidate;
            }
        }
        evolutionTestLastSequence_ = *sequence;
        const std::string coords = "\"x\":" + std::to_string(x) + ",\"y\":" + std::to_string(y);
        SendCommand("Input.dispatchMouseEvent", "{\"type\":\"mousePressed\"," + coords +
            ",\"button\":\"left\",\"buttons\":1,\"clickCount\":1}", runtime);
        SendCommand("Input.dispatchMouseEvent", "{\"type\":\"mouseReleased\"," + coords +
            ",\"button\":\"left\",\"buttons\":0,\"clickCount\":1}", runtime);
    }
