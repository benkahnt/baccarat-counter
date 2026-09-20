from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root / 'src/main.cpp').read_text(encoding='utf-8')
export = (root / 'src/session_export.h').read_text(encoding='utf-8')
build = (root / 'build.bat').read_text(encoding='utf-8', errors='ignore')
ini = (root / 'BaccaratCounter.ini.example').read_text(encoding='utf-8')

# User-facing persistent toggle; OFF is the non-regressive default.
assert 'gCombinedEvFilterEnabled{false}' in src
assert 'LoadCombinedEvFilterEnabled' in src
assert 'SaveCombinedEvFilterEnabled' in src
assert 'CombinedEvFilter' in ini
assert 'L"GesamtEV-Filter: EIN"' in src
assert 'L"GesamtEV-Filter: AUS"' in src
assert '(HMENU)134' in src
assert 'case 134:' in src

# Gate is optional: v106 compares normalized total edge to its own minimum.
# The historical EV>0 model below remains unchanged.
assert 'PRAGMATIC_SIGNAL_SUPPRESSED_COMBINED_EV_FILTER' in src
assert 'PRAGMATIC_SETZEN_SIGNAL_INVALIDATED_COMBINED_EV_FILTER' in src
assert 'combinedFilterEnabled && (!plan.valid || !plan.combinedMinEdgeMet)' in src
assert 'combinedFilterBlocked ? "filtered" : "logged-not-filtered"' in src
# MinEdge remains evaluated independently, and model tracking is armed before the live gate.
arm_pos = src.index('PRAGMATIC_COMBINED_EV_MODEL_ARMED')
gate_pos = src.index('PRAGMATIC_SIGNAL_SUPPRESSED_COMBINED_EV_FILTER', arm_pos)
assert arm_pos < gate_pos

# Counterfactual models are independent of the button state and settle from real round outcomes.
for token in (
    'gSessionMinEdgeModelPnlHundredths',
    'gSessionPositiveCombinedModelPnlHundredths',
    'gSessionMinEdgeModelSignals',
    'gSessionPositiveCombinedModelSignals',
    'PragmaticModelRoundPnlHundredths',
    'PRAGMATIC_COMBINED_EV_MODEL_RESULT',
):
    assert token in src, token
assert 'st.comparisonStakePlan.combinedEvPositive' in src
assert 'confirmed_bet_accounting::kBothPairs' in src
assert 'stakeUnitsHundredths * 0.95' in (root/'src/confirmed_bet_accounting.h').read_text(encoding='utf8')

# Session format v5 + Excel A/B columns and summaries.
assert 'BaccaratCounterSession 7' in export
for field in (
    'minEdgeModelUnitsHundredths',
    'positiveCombinedEvModelUnitsHundredths',
    'minEdgeModelSignals',
    'positiveCombinedEvModelSignals',
    'combinedEvFilterEnabledAtSave',
):
    assert field in export, field
for header in (
    'Modell MinEdge Units',
    'Modell GesamtEV>0 Units',
    'Delta GesamtEV - MinEdge',
    'MinEdge-Modell Signale',
    'GesamtEV>0 Signale',
    'GesamtEV-Filter beim Speichern',
):
    assert header in export, header
assert '<dimension ref=\\"A1:AA' in export
assert '<autoFilter ref=\\"A4:AA' in export
assert 'SUM(K5:K' in export and 'SUM(L5:L' in export
assert 'Bestes der drei Modelle (gleiche Sessions):' in export
assert 'CompareThreeModels(records)' in export

# Existing v89 diagnostics / v88 amount composition remain.
for marker in (
    'PRAGMATIC_SIDEBET_LIMITS_OBSERVED',
    'PRAGMATIC_SIDEBET_LIMITS_CHANGED',
    'PRAGMATIC_SIDEBET_LIMITS_HAND_SNAPSHOT',
    'PRAGMATIC_SIDEBET_LIMITS_DYNAMIC_FRAME',
):
    assert marker in src
assert 'PragmaticFindSingleDenomComposition' in src
assert 'kStandardPairLimitFromHand = 60' in src
assert 'kStandardPairLimitPercent = 20' in src
assert 'const ALL_TABLES_AUTO=true;' in src

# Critical v81 Pair transport still uses the embedded Pragmatic session.
pair_transport_start = src.index('const std::string& inputSessionId = pending.sessionId;')
pair_transport_end = src.index('void Bootstrap()', pair_transport_start)
pair_transport = src[pair_transport_start:pair_transport_end]
assert 'foregrounded-embedded-pragmatic' in pair_transport
assert 'Input.dispatchMouseEvent' in pair_transport
assert 'PragmaticCurrentBetifyPageSession' not in pair_transport

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'Baccarat Counter v21.2.123' in src
print('v21.2.90 GesamtEV toggle + Excel counterfactual model: OK')
