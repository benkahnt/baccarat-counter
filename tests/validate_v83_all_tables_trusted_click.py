from pathlib import Path
import hashlib

root=Path(__file__).resolve().parents[1]
src=(root/'src/main.cpp').read_text(encoding='utf-8')

# v83 uses a trusted CDP click for the All-Tables tab; v82 DOM click proved ineffective.
assert '__BAC_PRAGMATIC_ALL_TABLES_TRUSTED_CLICK__' in src
assert 'PRAGMATIC_MULTIPLAY_ALL_TABLES_TRUSTED_CLICK_DISPATCHED' in src
assert "startup-delayed-1" in src and "startup-delayed-2" in src
assert 'const offsets=[3600,6500];' in src
assert "requestAllTablesTrustedClick('focus-fallback')" in src
assert 'good-roads-explicit' in src

# The active-view detector may use explicit tab state, but must not use the old
# GOOD ROADS BEARBEITEN body-text shortcut that fired continuously in the v82 capture.
guard_start=src.index('// v21.2.84: Pragmatic can switch the Multiplay sidebar')
guard_end=src.index('    try{\n      if(/\\/desktop\\/multibaccarat\\//i.test(href) && d.body){\n        const tw=',guard_start)
guard=src[guard_start:guard_end]
assert 'GOOD\\s+ROADS\\s+BEARBEITEN' not in guard
assert '.click();' not in guard
assert 'Input.dispatchMouseEvent' not in guard  # C++ owns the trusted dispatch.

# C++ must dispatch the tab click on the same embedded Pragmatic session that
# emitted the request marker.
handler_start=src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_ALL_TABLES_TRUSTED_CLICK__"))')
handler_end=src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_ALL_TABLES_CLICK__"))',handler_start)
handler=src[handler_start:handler_end]
assert handler.count('Input.dispatchMouseEvent') >= 3
assert 'fullSessionId, moveId' in handler
assert 'fullSessionId, pressId' in handler
assert 'fullSessionId, releaseId' in handler
assert 'sendOk' in handler

# The proven v81 pair-bet click transport remains untouched.
pair_start=src.index('    void HandlePragmaticTrustedPairClickResponse(')
pair_end=src.index('    void Bootstrap()',pair_start)
pair=src[pair_start:pair_end]
assert 'const std::string& inputSessionId = pending.sessionId;' in pair
assert 'foregrounded-embedded-pragmatic' in pair
assert 'foregrounded-betify-page' not in pair

# UI cleanup from v82 remains.
assert 'L"BUTTON", L"Fokus"' not in src
assert 'L"BUTTON", L"Simulator Auto: AUS"' not in src

# Build/version marker.
build=(root/'build.bat').read_text(encoding='utf-8')
assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build

print('v83 trusted All-Tables click + delayed startup guard + v81 pair transport regression: OK')
