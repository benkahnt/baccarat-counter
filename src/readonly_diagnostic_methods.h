// Included inside CdpMonitor. This path never invokes the normal provider,
// strategy, capture, recovery, Telegram or input handlers.
    struct DiagnosticRequest {
        std::string kind;
        std::string session;
        int context = 0;
        ULONGLONG tick = 0;
    };
    std::map<uint64_t, DiagnosticRequest> diagnosticRequests_;
    std::set<std::string> diagnosticSessions_;
    std::map<std::string, std::set<int>> diagnosticContexts_;
    std::string diagnosticRoot_;

    static std::string DiagnosticString(const std::string& obj, const char* key) {
        const auto raw = readonly_diagnostics::Field(obj, key);
        return ExtractJsonString("{\"value\":" + raw + "}", "value").value_or("");
    }
    static int DiagnosticInt(const std::string& obj, const char* key) {
        const auto raw = readonly_diagnostics::Field(obj, key);
        return ExtractJsonInt("{\"value\":" + raw + "}", "value").value_or(0);
    }
    uint64_t DiagnosticSend(const std::string& method, const std::string& params,
                            const std::string& session, const std::string& kind,
                            int context = 0) {
        // Only this private sender bypasses the diagnostic SendRaw barrier.
        // Runtime expressions are generated here from the fixed read-only probe.
        if (method != "Target.getTargets" && method != "Target.attachToTarget" &&
            method != "Target.setAutoAttach" && method != "Runtime.enable" && method != "Page.enable" && method != "Page.getFrameTree" &&
            method != "Runtime.evaluate") return 0;
        const uint64_t id = NextId();
        const std::string safeParams = method == "Runtime.evaluate"
            ? "{\"expression\":\"" + JsonEscape(readonly_diagnostics::Probe()) +
                "\",\"returnByValue\":true,\"timeout\":2000,\"contextId\":" + std::to_string(context) + "}"
            : params;
        std::string json = "{\"id\":" + std::to_string(id) + ",\"method\":\"" + method + "\",\"params\":" + safeParams;
        if (!session.empty()) json += ",\"sessionId\":\"" + JsonEscape(session) + "\"";
        json += "}";
        if (!SendRaw(json, true)) return 0;
        diagnosticRequests_[id] = {kind, session, context, GetTickCount64()};
        return id;
    }
    void DiagnosticOwnSession(const std::string& session) {
        if (session.empty() || !diagnosticSessions_.insert(session).second) return;
        DiagnosticSend("Runtime.enable", "{}", session, "enable");
        DiagnosticSend("Target.setAutoAttach",
            "{\"autoAttach\":true,\"waitForDebuggerOnStart\":false,\"flatten\":true,"
            "\"filter\":[{\"type\":\"iframe\",\"exclude\":false},{\"exclude\":true}]}", session, "enable");
    }
    void DiagnosticMessage(const std::string& json) {
        if (stop_) return;
        const auto id = static_cast<uint64_t>(DiagnosticInt(json, "id"));
        if (id) {
            const auto it = diagnosticRequests_.find(id);
            if (it == diagnosticRequests_.end()) return;
            const auto request = it->second;
            diagnosticRequests_.erase(it);
            if (!readonly_diagnostics::Field(json, "error").empty()) {
                Log(L"ROOSTERBET DIAGNOSE – Leseabfrage fehlgeschlagen; kein Datenwert übernommen.");
                if (request.kind == "targets" || request.kind == "attach") stop_ = true;
                return;
            }
            const auto result = readonly_diagnostics::Field(json, "result");
            if (request.kind == "targets") {
                std::vector<std::string> pages;
                for (const auto& info : readonly_diagnostics::Parts(readonly_diagnostics::Field(result, "targetInfos"))) {
                    if (DiagnosticString(info, "type") == "page" &&
                        readonly_diagnostics::IsRoosterUrl(DiagnosticString(info, "url")))
                        pages.push_back(DiagnosticString(info, "targetId"));
                }
                if (pages.size() != 1 || pages.front().empty()) {
                    Log(L"ROOSTERBET DIAGNOSE – genau einen bestehenden Roosterbet-Tab öffnen. Keine automatische Navigation.");
                    stop_ = true; return;
                }
                DiagnosticSend("Target.attachToTarget", "{\"targetId\":\"" + JsonEscape(pages.front()) +
                    "\",\"flatten\":true}", "", "attach");
            } else if (request.kind == "attach") {
                diagnosticRoot_ = DiagnosticString(result, "sessionId");
                if (diagnosticRoot_.empty()) { stop_ = true; return; }
                DiagnosticSend("Page.enable", "{}", diagnosticRoot_, "enable");
                DiagnosticSend("Page.getFrameTree", "{}", diagnosticRoot_, "verify");
            } else if (request.kind == "verify") {
                const auto tree = readonly_diagnostics::Field(result, "frameTree");
                if (!readonly_diagnostics::IsRoosterUrl(DiagnosticString(readonly_diagnostics::Field(tree, "frame"), "url"))) {
                    stop_ = true; Log(L"ROOSTERBET DIAGNOSE – Tab-Zuordnung hat sich geändert; beendet."); return;
                }
                DiagnosticOwnSession(diagnosticRoot_);
                Log(L"ROOSTERBET DIAGNOSE – bestehender Tab verbunden. Werte erscheinen im Protokoll; keine Zählung, Signale oder Wettaktionen.");
            } else if (request.kind == "probe") {
                if (!diagnosticContexts_[request.session].count(request.context)) return;
                if (!readonly_diagnostics::Field(result, "exceptionDetails").empty()) return;
                const auto remote = readonly_diagnostics::Field(result, "result");
                const auto value = DiagnosticString(remote, "value");
                const auto kind = DiagnosticString(value, "kind");
                if (kind != "casino" && kind != "provider") return;
                // The fixed probe emits only status and visible value fields,
                // never full URLs, browser storage, credentials or raw traffic.
                Log(L"DIAGNOSE " + Utf8ToWide(IsoNow()) + L" " + Utf8ToWide(value));
            }
            return;
        }
        const auto method = DiagnosticString(json, "method");
        const auto parent = DiagnosticString(json, "sessionId");
        const auto params = readonly_diagnostics::Field(json, "params");
        if (method == "Target.detachedFromTarget" &&
            DiagnosticString(params, "sessionId") == diagnosticRoot_) {
            stop_ = true; Log(L"ROOSTERBET DIAGNOSE – Spieltab wurde geschlossen oder getrennt."); return;
        }
        if (parent != diagnosticRoot_ && !diagnosticSessions_.count(parent)) return;
        if (method == "Page.frameNavigated" && parent == diagnosticRoot_) {
            const auto frame = readonly_diagnostics::Field(params, "frame");
            if (DiagnosticString(frame, "parentId").empty() &&
                !readonly_diagnostics::IsRoosterUrl(DiagnosticString(frame, "url"))) {
                stop_ = true; Log(L"ROOSTERBET DIAGNOSE – Tab hat Roosterbet verlassen; beendet.");
            }
            return;
        }
        if (method == "Target.attachedToTarget") {
            const auto info = readonly_diagnostics::Field(params, "targetInfo");
            if (DiagnosticString(info, "type") == "iframe")
                DiagnosticOwnSession(DiagnosticString(params, "sessionId"));
        } else if (method == "Runtime.executionContextCreated") {
            const auto context = readonly_diagnostics::Field(params, "context");
            const auto aux = readonly_diagnostics::Field(context, "auxData");
            const int contextId = DiagnosticInt(context, "id");
            if (contextId && readonly_diagnostics::Field(aux, "isDefault") == "true")
                diagnosticContexts_[parent].insert(contextId);
        } else if (method == "Runtime.executionContextsCleared") {
            diagnosticContexts_[parent].clear();
        } else if (method == "Runtime.executionContextDestroyed") {
            diagnosticContexts_[parent].erase(DiagnosticInt(params, "executionContextId"));
        } else if (method == "Target.detachedFromTarget") {
            const auto child = DiagnosticString(params, "sessionId");
            diagnosticSessions_.erase(child); diagnosticContexts_.erase(child);
        } else if (method == "Inspector.detached") {
            if (parent == diagnosticRoot_) stop_ = true;
            diagnosticContexts_.erase(parent); diagnosticSessions_.erase(parent);
            Log(L"ROOSTERBET DIAGNOSE – Browser-Rahmen nicht mehr erreichbar.");
        }
    }
    void DiagnosticPoll() {
        const auto now = GetTickCount64();
        bool expired = false;
        for (auto it = diagnosticRequests_.begin(); it != diagnosticRequests_.end();) {
            if (now - it->second.tick > 15000) { expired = true; it = diagnosticRequests_.erase(it); }
            else ++it;
        }
        // A timed-out read may still be executing: stop instead of piling up requests.
        if (expired) { Log(L"ROOSTERBET DIAGNOSE – Lesezeitüberschreitung; Diagnose beendet."); stop_ = true; return; }
        if (!diagnosticRequests_.empty()) return;
        for (const auto& entry : diagnosticContexts_)
            for (int context : entry.second)
                DiagnosticSend("Runtime.evaluate", "{}", entry.first, "probe", context);
    }
    void RunReadOnlyDiagnostic() {
        diagnosticRequests_.clear(); diagnosticSessions_.clear(); diagnosticContexts_.clear(); diagnosticRoot_.clear();
        std::string browserWs;
        if (!HttpGetJsonVersion(browserWs) || !ConnectBrowserWs(browserWs)) {
            Log(L"ROOSTERBET DIAGNOSE – Debug-Chrome nicht erreichbar. Bitte bestehenden Debug-Browser öffnen."); return;
        }
        DiagnosticSend("Target.getTargets", "{}", "", "targets");
        std::vector<uint8_t> chunk(64 * 1024);
        std::string message;
        ULONGLONG pollTick = 0;
        while (!stop_) {
            DWORD count = 0;
            WINHTTP_WEB_SOCKET_BUFFER_TYPE type = WINHTTP_WEB_SOCKET_UTF8_MESSAGE_BUFFER_TYPE;
            const DWORD err = WinHttpWebSocketReceive(hWebSocket_, chunk.data(), static_cast<DWORD>(chunk.size()), &count, &type);
            if (err != ERROR_SUCCESS && err != ERROR_WINHTTP_TIMEOUT) break;
            if (err == ERROR_SUCCESS) {
                if (type == WINHTTP_WEB_SOCKET_CLOSE_BUFFER_TYPE) break;
                if (type == WINHTTP_WEB_SOCKET_UTF8_FRAGMENT_BUFFER_TYPE || type == WINHTTP_WEB_SOCKET_UTF8_MESSAGE_BUFFER_TYPE) {
                    message.append(reinterpret_cast<const char*>(chunk.data()), count);
                    if (message.size() > 8 * 1024 * 1024) { Log(L"DIAGNOSE – Browserantwort zu groß; beendet."); break; }
                    if (type == WINHTTP_WEB_SOCKET_UTF8_MESSAGE_BUFFER_TYPE) { DiagnosticMessage(message); message.clear(); }
                }
            }
            if (GetTickCount64() - pollTick >= 5000) { pollTick = GetTickCount64(); DiagnosticPoll(); }
        }
        // Closing this debugging connection releases its scoped child attachments.
        CloseHandles();
        Log(L"ROOSTERBET DIAGNOSE beendet. Browserseite unverändert. STOP gibt die Auswahl frei.");
    }
