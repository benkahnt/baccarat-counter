from pathlib import Path
import re
import subprocess
import tempfile
from test_toolchain import temporary_directory

root = Path(__file__).resolve().parents[1]
src = (root / "src/main.cpp").read_text(encoding="utf-8")

method = src.index("void PragmaticFocusSignalTable")
start = src.index('std::string js = R"JS((async()=>{try{', method)
end = src.index("const std::string params =", start)
segment = src[start:end]
chunks = list(re.finditer(r'R"JS\((.*?)\)JS"', segment, re.S))
assert len(chunks) == 17

insertions = [
    "test-run",
    "table-18",
    "Speed Baccarat 18",
    "game-123",
    "false",
    "false",
    "true",
    "40",
    "20",
    "2",
    "true",
    "Player",
    "1000",
    "500",
    "2",
    "42",
]
javascript = chunks[0].group(1)
for insertion, chunk in zip(insertions, chunks[1:]):
    javascript += insertion + chunk.group(1)

assert "const AUTO_BET_REQUEST=true;" in javascript
assert "const ALL_TABLES_AUTO=true;" in javascript
assert "if(!AUTO_BET_REQUEST||operation.finished||operation.pending)return false;" in javascript
assert "playerX" in javascript and "bankerX" in javascript
assert "toRootViewportPoint" in javascript
assert "focusMode:'betsopen'" in javascript
assert "const isMainBaccarat=/\\/desktop\\/baccarat\\//i.test(href);" in javascript
assert "const mainBaccaratRoot=()=>" in javascript
assert "finder:'main-baccarat-header'" in javascript
assert "bankier pair|bankier paar" in javascript
assert "^(banker|bankier|b)" in javascript
assert "const pairAreaFromText=(n,side)=>" in javascript
assert "flags.player&&!flags.banker" in javascript
assert "flags.banker&&!flags.player" in javascript
assert "pairTargetsFound:immediateTargetCount" in javascript
assert "const pairControlState=area=>" in javascript
assert "state.reason='pair-area-covered'" in javascript
assert "state.reason='active-hit-target'" in javascript
assert "uiWaitDeadline:Date.now()+20000" in javascript
assert "operation.deadline=Math.min(operation.hardDeadline,now+budget)" in javascript
assert "if(!waitForBettingUi(currentTable,requestedPhase))return false;" in javascript
assert "operation.attempt>=4" in javascript
assert "playerRequested:!operation.confirmed.player" in javascript
assert "bankerRequested:!operation.confirmed.banker" in javascript
assert "ROOT_WINDOW.setTimeout(probeAndMaybeArm,150)" in javascript
assert "__BAC_PAIR_READINESS__" in javascript
assert "__BAC_PAIR_RETRY_FINISHED__" in javascript
assert "total-bet-changed-without-side-attribution" in javascript
for removed in ("__bcp_signal_banner__", "data-bcp-signal-table",
                "data-bcp-signal-pair", "chooseNeutralCursorPoint"):
    assert removed not in javascript

with temporary_directory() as directory:
    js_path = Path(directory) / "focus.js"
    js_path.write_text(javascript, encoding="utf-8")
    subprocess.run(["node", "--check", str(js_path)], check=True)

    click_method = src.index("bool PragmaticClickPairBet")
    click_start = src.index('const std::string js = R"JS(', click_method)
    click_end = src.index("uint64_t requestId", click_start)
    click_segment = src[click_start:click_end]
    click_chunks = list(re.finditer(r'R"JS\((.*?)\)JS"', click_segment, re.S))
    assert len(click_chunks) == 5
    click_javascript = click_chunks[0].group(1)
    for insertion, chunk in zip(
            ("table-18|game-123|42", "player", "1", "test-run"),
            click_chunks[1:]):
        click_javascript += insertion + chunk.group(1)
    assert "target.click();" not in click_javascript
    assert "const interactionInfo=node=>" in click_javascript
    assert "resolvedInteractionTarget" in click_javascript
    assert "mode:'cdp-content-quad'" in click_javascript
    assert 'return target;' in click_javascript
    assert "pair-control-not-hit-testable" in click_javascript
    assert "Number(entry.attempt||0)!==ATTEMPT" in click_javascript
    assert "return area;" not in click_javascript
    assert "__BAC_PAIR_DOM_CLICK__" in click_javascript
    assert "Input.dispatchMouseEvent" not in click_javascript
    click_path = Path(directory) / "pair-dom-click.js"
    click_path.write_text(click_javascript, encoding="utf-8")
    subprocess.run(["node", "--check", str(click_path)], check=True)

print("focus and exact Pair-target JavaScript syntax OK")
