#pragma once
#include <string_view>

namespace casino_profile {
enum class Casino { Betify = 0, Roosterbet = 1 };

struct Profile {
    Casino casino;
    const wchar_t* name;
    const wchar_t* key;
    const char* home;
    bool launchVerified;
};

inline constexpr Profile profiles[] = {
    {Casino::Betify, L"Betify", L"betify", "https://betify.com/", true},
    {Casino::Roosterbet, L"Roosterbet", L"roosterbet", "https://rooster.bet/", false},
};

inline const Profile& Get(Casino casino) {
    return profiles[casino == Casino::Roosterbet ? 1 : 0];
}

inline Casino FromKey(std::wstring_view key) {
    return key == L"roosterbet" ? Casino::Roosterbet : Casino::Betify;
}
} // namespace casino_profile
