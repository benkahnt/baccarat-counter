from pathlib import Path
import hashlib
import re

root = Path(__file__).resolve().parents[1]
src = (root / 'src' / 'main.cpp').read_text(encoding='utf-8')
build = (root / 'build.bat').read_text(encoding='ascii')
readme = (root / 'README.md').read_text(encoding='utf-8')

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'Baccarat Counter v21.2.123' in src
assert 'v21.2.96 – Pragmatic Burn nur bei sicherer Erkennung' in readme

# New state is deliberately split into known composition vs physical cards-out.
for token in [
    'pendingBurnIndicatorCard',
    'pendingBurnDistinctCandidates',
    'pendingBurnAmbiguous',
    'burnConfirmed',
    'burnIndicatorCard',
    'burnPhysicalCardsOut',
    'pendingEndBurnConfirmed',
    'pendingEndBurnPhysicalCards',
]:
    assert token in src, token

# Baccarat burn mapping used by this release: exposed indicator + its burn value.
def physical_burn(rank: str) -> int:
    if rank == 'A': value = 1
    elif rank in '23456789': value = int(rank)
    elif rank in ('10', 'J', 'Q', 'K'): value = 10
    else: return -1
    return value + 1

assert physical_burn('A') == 2
assert physical_burn('2') == 3
assert physical_burn('9') == 10
assert physical_burn('10') == 11
assert physical_burn('J') == 11
assert physical_burn('Q') == 11
assert physical_burn('K') == 11

# A raw burn candidate must not immediately change the strategy.
card_start = src.index('        if (PragmaticTopKey(payload, "card")) {')
card_end = src.index('        if (PragmaticTopKey(payload, "gameresult")) {', card_start)
card_block = src[card_start:card_end]
burn_start = card_block.index('            if (burnCandidate) {')
burn_end = card_block.index('            if (place && *place == "player")', burn_start)
burn_branch = card_block[burn_start:burn_end]
assert 'PragmaticStageBurnCandidate' in burn_branch
assert 'PragmaticStrategySubtractCard' not in burn_branch
assert 'appliedToStrategy' not in burn_branch  # logging lives in the stage helper

stage_start = src.index('    void PragmaticStageBurnCandidate(')
stage_end = src.index('    void PragmaticConfirmPendingBurn(', stage_start)
stage = src[stage_start:stage_end]
assert 'PragmaticStrategySubtractCard' not in stage
assert 'pendingBurnCandidateSignature' in stage
assert 'gameId + "|" + std::to_string(seq) + "|" + rawSc' in stage
assert 'pendingBurnIndicatorRawSc' in stage
assert 'appliedToStrategy' in stage and 'false' in stage

# Promotion only happens with exactly one distinct, unambiguous candidate.
confirm_start = src.index('    void PragmaticConfirmPendingBurn(')
confirm_end = src.index('    void PragmaticStrategySubtractHand(', confirm_start)
confirm = src[confirm_start:confirm_end]
assert 'st.pendingBurnDistinctCandidates == 1' in confirm
assert '!st.pendingBurnAmbiguous' in confirm
assert 'PragmaticStrategySubtractCard(st, confirmedCard)' in confirm
assert 'PRAGMATIC_BURN_UNCONFIRMED' in confirm
assert 'calculationChanged' in confirm and 'false' in confirm
assert 'PRAGMATIC_BURN_CONFIRMED' in confirm
assert 'physicalBurnCards' in confirm
assert 'hiddenBurnCards' in confirm

# Confirmation is on the first betsopen boundary, before the old awaiting flag is cleared.
bets_start = src.index('        if (PragmaticTopKey(payload, "betsopen")) {')
bets_end = src.index('        if (PragmaticTopKey(payload, "betsclosed")) {', bets_start)
bets = src[bets_start:bets_end]
assert bets.index('PragmaticConfirmPendingBurn') < bets.index('st.awaitingFirstGame = false;')

# Display: only confirmed burn yields an exact physical cards-out number.
post_start = src.index('    void PostPragmaticStatus(')
post_end = src.index('    void PragmaticEmitShoeStart(', post_start)
post = src[post_start:post_end]
assert 'exactPhysicalCards' in post
assert 'st.shoeKnownDealt + st.burnPhysicalCardsOut' in post
assert 'exactPhysicalCards,' in post

# Hand diagnostics include both composition and physical cards remaining.
assert 'shoeKnownRegularCards' in src
assert 'physicalCardsOut' in src
assert 'physicalCardsRemaining' in src

# Shoe-end physical penetration is only exact if the burn was confirmed.
end_start = src.index('    void PragmaticFinalizeShoeEnd(')
end_end = src.index('    void PragmaticEmitShoeEnd(', end_start)
end = src[end_start:end_end]
assert 'exactRegular && st.pendingEndBurnConfirmed' in end
assert 'exactPhysicalPenetrationAvailable' in end
assert 'physicalPenetrationIsHigherBecauseBurnUnknown' in end

# Capture window now preserves relevant core frames around shoe start, even after
# the generic raw-frame budget is exhausted. This is diagnostic only.
assert 'shoeWindowRelevant' in src
assert 'it->second.awaitingFirstGame || it->second.pendingShoeEnd' in src
assert 'topKey == "betsopen" || topKey == "endshuffling"' in src

# Guardrail: the Lucky-Pairs math core itself is unchanged from the v95 reference.
math_start = src.index('    std::optional<std::pair<double,double>>\n    PragmaticStrategyMath')
math_end = src.index('    static bool StrategyMeetsThreshold', math_start)
math_hash = hashlib.sha256(src[math_start:math_end].encode()).hexdigest()
assert math_hash == 'ad79af8e9eb2585db96372c475efdd5089c8d4bc201c8e9f8bbdcea867855f6b', math_hash

print('v21.2.96 confirmed Pragmatic burn tracking / conservative Edge guard: OK')
