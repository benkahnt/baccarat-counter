from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
src = (root / "src/main.cpp").read_text(encoding="utf-8")

# The v63/v65 geometry target is the actual hit-tested node, not the Pair-area parent.
method = src.index("bool PragmaticClickPairBet")
js_start = src.index('const std::string js = R"JS(', method)
js_end = src.index("uint64_t requestId", js_start)
click_js = src[js_start:js_end]
assert "return target;" in click_js
assert "return area;" not in click_js
assert "mode:'cdp-content-quad'" in click_js
assert "resolvedInteractionTarget" in click_js

# The trusted input must remain on the same embedded Pragmatic CDP session
# that owns the Runtime.evaluate object and DOM.getContentQuads response.
handler = src.index("void HandlePragmaticTrustedPairClickResponse")
handler_end = src.index("void Bootstrap()", handler)
trusted = src[handler:handler_end]
assert "const std::string& inputSessionId = pending.sessionId;" in trusted
assert "PragmaticCurrentBetifyPageSession()" not in trusted
assert 'inputSessionMode\\\":\\\"foregrounded-embedded-pragmatic' in trusted
assert "Input.dispatchMouseEvent" in trusted
assert "DOM.getContentQuads" in trusted

# Runtime-persistence/focus repair from v80 must remain present.
assert "PRAGMATIC_RUNTIME_SESSION_PROMOTED" in src
assert "PRAGMATIC_FOCUS_NO_RUNTIME" in src
assert "PRAGMATIC_RUNTIME_REDISCOVERY_REQUESTED" in src

print("v21.2.81 v63/v65 Pair click transport restored; v80 runtime persistence retained: OK")
