from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root / 'src/main.cpp').read_text(encoding='utf-8')
build = (root / 'build.bat').read_text(encoding='utf-8')
ini = (root / 'BaccaratCounter.ini.example').read_text(encoding='utf-8')

# UI + persistence.
assert 'gPragmaticAllTablesAutoEnabled' in src
assert 'LoadPragmaticAllTablesAutoEnabled' in src
assert 'SavePragmaticAllTablesAutoEnabled' in src
assert 'L"Pragmatic", L"AllTablesAuto"' in src
assert 'Alle Tische Auto: EIN' in src
assert 'Alle Tische Auto: AUS' in src
assert '(HMENU)132' in src
assert 'case 132:' in src
assert '[Pragmatic]' in ini and 'AllTablesAuto=1' in ini

# Probe/guard remains able to classify Good Roads, but OFF blocks every
# automatic startup/count-drop click without hiding the view-mode signal from
# the dynamic table membership logic.
probe = src[src.index('std::string PragmaticProbeScript'):src.index('std::string EvolutionBootstrapScript')]
assert 'const ALL_TABLES_AUTO=' in probe
assert '__BCP_PRAGMATIC_ALL_TABLES_AUTO_NATIVE__' in probe
assert 'const allTablesAutoEnabled=()=>' in probe
assert 'if(!allTablesAutoEnabled())return;' in probe
assert "multiplayViewMode=goodRoadsActive?'good-roads':'all-tables'" in probe
assert 'good-roads-count-drop' in probe

# Signal focus fallback obeys the same toggle.
focus_start = src.index('void PragmaticFocusSignalTable')
focus_end = src.index('void MaybeFinalizeParallelSignalFocus', focus_start)
focus = src[focus_start:focus_end]
assert 'const ALL_TABLES_AUTO=' in focus
assert 'if(!ALL_TABLES_AUTO||!isMulti||!document.body)return false;' in focus
assert '__BAC_PRAGMATIC_ALL_TABLES_AUTO_SUPPRESSED__' in focus

# C++ adds a final safety gate so a stale console request cannot click after
# the user switched automation OFF.
handler_start = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_ALL_TABLES_TRUSTED_CLICK__"))')
handler_end = src.index('if (auto value = extractConsoleValue("__BAC_PRAGMATIC_ALL_TABLES_CLICK__"))', handler_start)
handler = src[handler_start:handler_end]
assert 'gPragmaticAllTablesAutoEnabled.load' in handler
assert 'PRAGMATIC_MULTIPLAY_ALL_TABLES_AUTO_SUPPRESSED' in handler

# The live toggle updates already-installed frame guards without clicking.
assert 'SetPragmaticAllTablesAutoEnabled(bool enabled)' in src
assert '__BCP_PRAGMATIC_ALL_TABLES_AUTO_NATIVE__=ENABLED' in src
assert 'PRAGMATIC_MULTIPLAY_ALL_TABLES_AUTO_TOGGLED' in src

# Pair betting remains on the known-good v63/v65 transport restored in v81.
pair_start = src.index('void HandlePragmaticTrustedPairClickResponse')
pair_end = src.index('void Bootstrap()', pair_start)
pair = src[pair_start:pair_end]
assert 'const std::string& inputSessionId = pending.sessionId;' in pair
assert 'foregrounded-embedded-pragmatic' in pair
assert 'PragmaticCurrentBetifyPageSession()' not in pair

# v86 is an A/B toggle only; it must not silently introduce the proposed
# 0.20 main-bet workaround.
assert 'PRAGMATIC_MAIN_BET_BEFORE_PAIR' not in src

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'Baccarat Counter v21.2.123' in src

print('v21.2.88 All-Tables live A/B toggle + v81 Pair-click regression: OK')
