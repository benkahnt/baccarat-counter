#!/usr/bin/env python3
import json, pathlib, sys
cap=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "/mnt/data/cpp_capture_20260914_192403.jsonl")
blank=set(); proved=[]; first_signal=None
for lineno,line in enumerate(cap.read_text(encoding="utf-8").splitlines(),1):
    e=json.loads(line)
    if e.get("kind")=="PRAGMATIC_TARGET_CANDIDATE" and e.get("type")=="iframe" and not e.get("url"):
        blank.add(e.get("session"))
    if e.get("kind")=="PRAGMATIC_MULTIPLAY_PROBE":
        sid=e.get("session")
        p=e.get("payload") or {}
        href=""
        mt=p.get("mainTables") or []
        if mt: href=str(mt[0].get("href") or "")
        if not href:
            docs=p.get("docs") or []
            if docs: href=str(docs[0].get("href") or "")
        if sid in blank and "/desktop/" in href:
            proved.append((lineno,sid,href))
    if e.get("kind")=="PRAGMATIC_SIGNAL_FOCUS_REQUEST" and first_signal is None:
        first_signal=lineno
assert proved, "failing capture contains no blank-url session later proven as Pragmatic desktop runtime"
line,sid,href=proved[0]
assert first_signal is not None and line < first_signal, (line, first_signal)
assert sid=="27E94852", (sid,href)
print(f"capture replay OK: {sid} promoted at line {line} before first focus signal line {first_signal}; href={href}")
