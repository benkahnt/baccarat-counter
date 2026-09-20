#pragma once
#include <string>
#include <string_view>
#include <vector>
#include <map>
#include <set>
#include <cctype>

// Pure helpers for the isolated diagnostic connection. No strategy or input APIs.
namespace readonly_diagnostics {
inline bool IsRoosterUrl(std::string_view url) {
    std::string s(url);
    for (char& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    if (s.compare(0, 8, "https://") != 0) return false;
    const auto end = s.find_first_of("/?#", 8);
    const auto host = s.substr(8, end == std::string::npos ? end : end - 8);
    return host == "www.rooster.bet" || host == "rooster.bet";
}

// Split only at the current JSON container level; escaped quotes and nested
// objects must not turn a child sessionId into its parent's envelope sessionId.
inline std::vector<std::string> Parts(std::string_view value) {
    std::vector<std::string> out;
    if (value.size() < 2) return out;
    size_t start = 1; int depth = 0; bool quoted = false, escaped = false;
    for (size_t i = 1; i + 1 < value.size(); ++i) {
        const char c = value[i];
        if (quoted) { if (escaped) escaped = false; else if (c == '\\') escaped = true; else if (c == '"') quoted = false; continue; }
        if (c == '"') quoted = true;
        else if (c == '[' || c == '{') ++depth;
        else if (c == ']' || c == '}') --depth;
        else if (c == ',' && depth == 0) { out.emplace_back(value.substr(start, i-start)); start = i+1; }
    }
    if (start + 1 < value.size()) out.emplace_back(value.substr(start, value.size()-start-1));
    return out;
}
inline std::string Field(std::string_view object, std::string_view key) {
    for (const auto& part : Parts(object)) {
        const auto a = part.find_first_not_of(" \r\n\t");
        const std::string prefix = "\"" + std::string(key) + "\"";
        if (a == std::string::npos || part.compare(a, prefix.size(), prefix) != 0) continue;
        const auto colon = part.find_first_not_of(" \r\n\t", a + prefix.size());
        if (colon == std::string::npos || part[colon] != ':') continue;
        const auto begin = part.find_first_not_of(" \r\n\t", colon+1);
        const auto end = part.find_last_not_of(" \r\n\t");
        return begin == std::string::npos ? "" : part.substr(begin, end-begin+1);
    }
    return "";
}

inline const char* Probe() {
    return R"JS((()=>{
const d=document,host=location.hostname.toLowerCase(),path=location.pathname;
const visible=e=>!!e&&e.getClientRects().length>0&&getComputedStyle(e).visibility!=='hidden'&&getComputedStyle(e).display!=='none';
const text=e=>e?String(e.innerText||e.textContent||'').replace(/\s+/g,' ').trim():'';
const casino=host==='rooster.bet'||host==='www.rooster.bet';
const pragmatic=host==='client.pragmaticplaylive.net';
if(!casino&&!pragmatic)return JSON.stringify({kind:'bridge'});
if(casino){
const menus=[...d.querySelectorAll('[role="combobox"]')].filter(visible);
const currency=menus.find(e=>e.getAttribute('aria-label')==='Currency');
const user=menus.some(e=>e.getAttribute('aria-label')==='User Menu');
const password=[...d.querySelectorAll('input[type="password"]')].some(visible);
return JSON.stringify({kind:'casino',login:password?'login-visible':user?'user-menu-visible':'unknown',casinoBalance:currency?text(currency).slice(0,60):null});
}
const balance=[...d.querySelectorAll('[data-testid="wallet-balance-value"], [data-testid="wallet-mobile-balance"] [data-testid="wallet-mobile-value"]')].find(visible);
const total=[...d.querySelectorAll('[data-testid="wallet-total-bet-value"], [data-testid="wallet-mobile-total-bet"] [data-testid="wallet-mobile-value"]')].find(visible);
const body=text(d.body);
const expired=/Sitzung (?:ist )?abgelaufen|session (?:has )?expired|inactivity/i.test(body);
const tiles=[...d.querySelectorAll('[id^="TileHeight-"]')];
return JSON.stringify({kind:'provider',provider:'Pragmatic',view:path.includes('multibaccarat')?'MULTIPLAY':path.includes('/baccarat')?'Haupttisch':'Launcher',expired,providerBalance:visible(balance)?text(balance).slice(0,60):null,totalBet:total?text(total).slice(0,60):null,tableCount:tiles.length,rounds:(body.match(/ID\s*:\s*\d+/g)||[]).slice(0,50)});
})())JS";
}
}
