from pathlib import Path

root=Path(__file__).resolve().parents[1]
src=(root/'src/main.cpp').read_text(encoding='utf-8')

# Capture 21:15 proved that v83 dispatched local multibaccarat coordinates
# (about 56/56) through the launcher target. v84 must translate the tab centre
# through the same-origin iframe chain into the launcher-root viewport.
guard_start=src.index('// v21.2.84: Pragmatic can switch the Multiplay sidebar')
guard_end=src.index('    try{\n      if(/\\/desktop\\/multibaccarat\\//i.test(href) && d.body){\n        const tw=',guard_start)
guard=src[guard_start:guard_end]
assert 'const toRootViewportPoint=(x,y)=>' in guard
assert 'px+=r.left+borderLeft;' in guard
assert 'py+=r.top+borderTop;' in guard
assert 'const localX=r.left+r.width/2;' in guard
assert 'const localY=r.top+r.height/2;' in guard
assert 'const rootPoint=toRootViewportPoint(localX,localY);' in guard
assert 'const x=rootPoint.x;' in guard and 'const y=rootPoint.y;' in guard
assert 'localX,localY,frameDepth:rootPoint.depth' in guard

# The selected-state CSS/ARIA signal was not reliable in the live capture.
# A sharp 18 -> 2/3 rendered-name drop is now a secondary Good-Roads signal,
# while the expected 19 -> 14 dynamic table change must remain a normal view.
assert 'knownMax>=8&&renderedNow>0&&renderedNow<=4' in guard
assert 'good-roads-count-drop' in guard
assert 'Number(ctl.maxRendered||0)>=8&&rendered>0&&rendered<=4' in guard

def filtered_by_count(max_rendered, current):
    return max_rendered >= 8 and current > 0 and current <= 4

assert filtered_by_count(18,2)
assert filtered_by_count(18,3)
assert not filtered_by_count(19,14)
assert not filtered_by_count(12,12)
assert not filtered_by_count(18,8)


# The SETZEN-focus fallback emits the same marker and must use the same root
# coordinate convention; otherwise a signal arriving while Good Roads is active
# would reintroduce the v83 local-coordinate bug.
focus_click_start=src.index('const requestAllTablesTrustedClick=reason=>')
focus_click_end=src.index('const ensureAllTablesForFocus=async()=>',focus_click_start)
focus_click=src[focus_click_start:focus_click_end]
assert 'const localX=r.left+r.width/2;' in focus_click
assert 'const rootPoint=toRootViewportPoint(localX,localY);' in focus_click
assert 'x,y,localX,localY,frameDepth:rootPoint.depth' in focus_click

# C++ receives root coordinates and records both spaces for the next capture.
handler_start=src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_ALL_TABLES_TRUSTED_CLICK__"))')
handler_end=src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_ALL_TABLES_CLICK__"))',handler_start)
handler=src[handler_start:handler_end]
assert 'ExtractJsonDouble(payload, "localX")' in handler
assert 'ExtractJsonDouble(payload, "localY")' in handler
assert 'ExtractJsonInt(payload, "frameDepth")' in handler
assert 'coordinateSpace' in handler and 'launcher-root-viewport' in handler
assert handler.count('Input.dispatchMouseEvent') >= 3
assert 'fullSessionId, moveId' in handler
assert 'fullSessionId, pressId' in handler
assert 'fullSessionId, releaseId' in handler

# Pair betting stays on the proven v63/v65 transport restored in v81.
pair_start=src.index('    void HandlePragmaticTrustedPairClickResponse(')
pair_end=src.index('    void Bootstrap()',pair_start)
pair=src[pair_start:pair_end]
assert 'const std::string& inputSessionId = pending.sessionId;' in pair
assert 'foregrounded-embedded-pragmatic' in pair
assert 'foregrounded-betify-page' not in pair

build=(root/'build.bat').read_text(encoding='utf-8')
assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build

print('v84 All-Tables root-coordinate translation + count-drop guard + v81 pair regression: OK')
