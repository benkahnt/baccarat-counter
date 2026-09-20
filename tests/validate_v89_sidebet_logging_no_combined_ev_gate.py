from pathlib import Path
import math

root = Path(__file__).resolve().parents[1]
src = (root / 'src/main.cpp').read_text(encoding='utf-8')
build = (root / 'build.bat').read_text(encoding='utf-8', errors='ignore')

# v88 amount-composition + standard fallback retained.
assert 'L"Pair-Chip €:"' in src
assert 'PragmaticFindSingleDenomComposition' in src
assert 'kStandardPairLimitFromHand = 60' in src
assert 'kStandardPairLimitPercent = 20' in src
assert 'PragmaticParsePairLimitTiers' in src
assert 'sideBetsLimits' in src
assert 'const ALL_TABLES_AUTO=true;' in src

# v89: provider limits are explicitly observed and correlated with hand count.
for marker in (
    'PRAGMATIC_SIDEBET_LIMITS_OBSERVED',
    'PRAGMATIC_SIDEBET_LIMITS_CHANGED',
    'PRAGMATIC_SIDEBET_LIMITS_HAND_SNAPSHOT',
    'PRAGMATIC_SIDEBET_LIMITS_DYNAMIC_FRAME',
):
    assert marker in src, marker
assert 'sideBetHand >= 55 && sideBetHand <= 70' in src
assert '(sideBetHand % 10) == 0' in src
assert 'providerTotalGames' in src
assert 'parsedPairTiers' in src
assert 'ruleSource' in src

# v89: combined EV is advisory, not a second strategy threshold.
assert 'combined-ev-not-positive' not in src
assert 'main-plus-pairs-combined-ev-advisory-only' in src
assert 'combinedEvPositive' in src
assert 'PRAGMATIC_COMBINED_EV_ADVISORY' in src
assert 'logged-not-filtered' in src
# The plan becomes valid after technical main-bet composition even if combined EV <= 0.
fragment = src[src.index('const double mainStakeUnits ='):src.index('static std::string PragmaticPrettyName')]
assert 'plan.valid = true;' in fragment
assert 'return plan;' in fragment
assert 'combinedExpectedUnits <= 0.0' not in fragment

# Why this matters: Pair edge +2% with 60:20 and a conventional -1.06% main EV
# has negative combined EV, but must remain an executable MinEdge signal in v89.
pair_amount = 2.00
main_amount = 10.00
pair_edge = 0.02
main_ev = -0.0106
combined_eur = 2 * pair_amount * pair_edge + main_amount * main_ev
assert combined_eur < 0  # approximately -0.026 EUR

# Better Player/Banker side selection remains intact.
assert 'PragmaticComputeMainBetEv' in src
assert 'ev.banker > ev.player' in src

# Pair click transport remains the embedded v81 path.
pair_transport_start = src.index('const std::string& inputSessionId = pending.sessionId;')
pair_transport_end = src.index('void Bootstrap()', pair_transport_start)
pair_transport = src[pair_transport_start:pair_transport_end]
assert 'foregrounded-embedded-pragmatic' in pair_transport
assert 'Input.dispatchMouseEvent' in pair_transport
assert 'PragmaticCurrentBetifyPageSession' not in pair_transport

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'Baccarat Counter v21.2.123' in src
print('v21.2.89 sideBetsLimits logging + no combined-EV veto: OK')
