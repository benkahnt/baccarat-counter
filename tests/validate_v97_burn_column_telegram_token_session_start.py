from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / 'src' / 'main.cpp').read_text(encoding='utf-8')
build = (ROOT / 'build.bat').read_text(encoding='utf-8', errors='replace')
readme = (ROOT / 'README.md').read_text(encoding='utf-8')
telegram = (ROOT / 'TELEGRAM_SETUP.md').read_text(encoding='utf-8')

assert 'BaccaratCounterV123.exe' in build
assert 'v21.2.123' in build
assert 'Baccarat Counter v21.2.123' in src
assert '# Baccarat Counter v21.2.123' in readme

# Dedicated burn observation column. Unknown/unconfirmed burn is diagnostic only.
assert 'L"Burnkarten"' in src
assert 'int burnCards{-1};' in src
assert 'bool burnCardsExact{false};' in src
assert 'burnCards = L"?";' in src
# v113 appends separate Paper hands / total P/L without removing the burn column.
assert 'for(int c=1;c<15;++c)' in src
assert 'for(int i=0;i<15;++i)' in src
assert 'L"Ist P/L",L"Paper Hände",L"Paper P/L gesamt"' in src
assert 'burnCards,pp,ed,sig,hitRounds,pairBets,actualPnl,paperHands,paperPnl' in src
assert 'st.shoeTracked ? (st.burnConfirmed ? st.burnPhysicalCardsOut : 0) : -1' in src
assert 'st.shoeTracked && st.burnConfirmed && st.burnPhysicalCardsOut > 0' in src

# Bot token is editable in the GUI, masked, locally persisted and never echoed in logs.
assert 'L"Telegram Bot-Token:"' in src
assert 'ES_AUTOHSCROLL|ES_PASSWORD' in src
assert '(HMENU)136' in src
assert 'SaveTelegramBotToken' in src
assert 'WritePrivateProfileStringW(L"Telegram", L"BotToken"' in src
assert 'token.empty() ? L"0" : L"1"' in src
assert 'Token wird nicht im Log ausgegeben.' in src
assert 'Bot-Token' in telegram and 'maskierten Feld' in telegram

# Start notification requires BOTH UI readiness and a real game-progress frame.
assert 'MaybeQueueTelegramPragmaticSessionStart' in src
assert 'pragmaticMultiplayEverReady_.load(std::memory_order_acquire)' in src
assert 'pragmaticMultiplayRealGameFrameSeen_.load(std::memory_order_acquire)' in src
assert 'pragmaticMultiplayRealGameFrameSeen_.exchange(' in src
assert 'telegramPragmaticSessionStartSent_.compare_exchange_strong' in src
assert 'TELEGRAM_SESSION_START_TRIGGER' in src
assert 'Neue Baccarat-Session gestartet' in src
assert 'Karten-Zählung an allen Tischen läuft.' in src
assert 'MaybeQueueTelegramPragmaticSessionStart("multiplay-live-game-frame")' in src
assert 'MaybeQueueTelegramPragmaticSessionStart("multiplay-ready")' in src
assert 'MaybeQueueTelegramPragmaticSessionStart("multiplay-health-ready")' in src

# v111: the signal toggle now also controls the start notification.
helper = re.search(r'static void QueueTelegramSignalResult\(.*?\n\}', src, re.S)
assert helper and 'gTelegramSignalEnabled' in helper.group(0)
session_start = re.search(r'void MaybeQueueTelegramPragmaticSessionStart\(.*?\n    \}', src, re.S)
assert session_start and 'gTelegramSignalEnabled' in session_start.group(0)

# The proven Lucky-Pairs math body remains byte-identical to v21.2.96.
def extract_function(text, signature):
    i = text.index(signature)
    line_start = text.rfind('\n', 0, i) + 1
    prev_start = text.rfind('\n', 0, line_start - 1) + 1
    if text[prev_start:line_start].strip().startswith('std::optional'):
        i = prev_start
    b = text.index('{', i)
    depth = 0
    state = 'normal'
    esc = False
    j = b
    while j < len(text):
        c = text[j]
        n = text[j + 1] if j + 1 < len(text) else ''
        if state == 'line':
            if c == '\n': state = 'normal'
        elif state == 'block':
            if c == '*' and n == '/': state = 'normal'; j += 1
        elif state == 'str':
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': state = 'normal'
        elif state == 'char':
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == "'": state = 'normal'
        else:
            if c == '/' and n == '/': state = 'line'; j += 1
            elif c == '/' and n == '*': state = 'block'; j += 1
            elif c == '"': state = 'str'
            elif c == "'": state = 'char'
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return text[i:j + 1]
        j += 1
    raise AssertionError('unbalanced function')

strategy = extract_function(src, 'PragmaticStrategyMath(const PragmaticTableRuntime& st) const')
assert hashlib.sha256(strategy.encode()).hexdigest() == 'a21cd3867249c33a87042c3b8b4e621f3716f4d2a9fba223d5404be158bc0579'
settlement = extract_function(src, 'QueueTelegramSignalSettlement(HWND hwnd')
assert hashlib.sha256(settlement.encode()).hexdigest() == '2726f2b51a6a0213761aa66bfcb120ff7e585489eb4b422f7f1be67bd55a3117'

print('v21.2.97 Burn column / Telegram token UI / session-start notification: OK')
