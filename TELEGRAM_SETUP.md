# Telegram-Benachrichtigungen – v21.2.123

Telegram ist optional und wird **nur lokal auf dem PC** konfiguriert. Der Bot-Token gehört nicht in Captures, Chats oder Support-Nachrichten.

## Einmalige Einrichtung

1. In Telegram `@BotFather` öffnen.
2. `/newbot` ausführen und einen privaten Bot anlegen.
3. Den von BotFather gelieferten Token kopieren.
4. Den neuen Bot in Telegram öffnen und ihm **mindestens eine Nachricht** schicken, z. B. `Start`.
5. `BaccaratCounterV123.exe` starten.
6. Den Token direkt im neuen maskierten Feld **Telegram Bot-Token** einfügen. Beim Verlassen des Feldes – spätestens beim Klick auf **Verbinden** – wird er lokal in `BaccaratCounter.ini` gespeichert. Ein nichtleerer Token aktiviert Telegram global; ein leeres Feld deaktiviert Telegram global.

Die INI muss für den Bot-Token nicht mehr manuell bearbeitet werden. Intern bleibt die Konfiguration kompatibel:

```ini
[Telegram]
Enabled=1
SignalEnabled=0
BotToken=HIER_DEIN_BOT_TOKEN
ChatId=
```

`ChatId` darf leer bleiben. Beim ersten Telegram-Versand fragt die Software bei Bedarf `getUpdates` ab, nimmt die zuletzt gefundene Chat-ID und speichert sie lokal in die INI. Alternativ kann die Chat-ID weiterhin manuell eingetragen werden.

## Session-Startmeldung

Bei Pragmatic Play wird pro neu gestarteter Monitor-Session einmalig eine Telegram-Nachricht gesendet, sobald **MULTIPLAY bereit** ist und zusätzlich ein **echter MULTIPLAY-Spiel-Datenframe** angekommen ist. Damit wird nicht nur eine sichtbare Oberfläche, sondern der tatsächlich laufende Zählpfad bestätigt. Diese Startmeldung wird nur bei `Telegram-Signal: ON` gesendet. Bei OFF wird weder eine Startmeldung eingereiht noch eine wartende Startmeldung versandt; der Schalter wird im Hintergrund vor dem Versand erneut geprüft.

## Schalter „Telegram-Signal: ON/OFF“

- **OFF:** Signal-Abschlüsse und MULTIPLAY-Startmeldungen werden nicht per Telegram verschickt.
- **ON:** Eine Nachricht wird erst gesendet, wenn die zum Signal gehörende Hand vollständig gespielt und ausgewertet wurde.

Der Zustand wird lokal als `SignalEnabled=0/1` gespeichert. `Enabled=1` bleibt zusätzlich der Telegram-Master-Schalter; bei `Enabled=0` wird auch mit eingeschaltetem Signal-Schalter nichts versendet.

## Inhalt der Abschlussmeldung

Bei Pragmatic Play enthält die Nachricht nach der gespielten Hand:

- **Signal: GEWINN/VERLUST**,
- **Hand: PLAYER/BANKER/TIE**,
- **Player Pair: gewonnen/verloren**,
- **Banker Pair: gewonnen/verloren**,
- **Chips erfolgreich platziert: JA/NEIN**,
- Hauptwette auf Player, Banker oder Tie mit tatsächlich akzeptiertem Betrag, falls erforderlich,
- tatsächlich bestätigter Betrag auf **Player Pair**,
- tatsächlich bestätigter Betrag auf **Banker Pair**,
- bei bekannten Chipdaten zusätzlich die Zusammensetzung, z. B. `2 × 0,50 EUR = 1,00 EUR`,
- **Hand-P/L (tatsächlich)** in Units,
- **Session-P/L** in Units,
- **Kontostand** aus der aktuellsten sicheren Balance-Erkennung nach dem Handergebnis.

Im Klickmodus werden nur bestätigte Einsätze als real platziert behandelt. Eine Hauptwette zählt mit dem tatsächlich angenommenen Betrag, auch wenn dieser vom Plan abweicht. Banker-Gewinne berücksichtigen die 5%-Provision. Player/Banker pushen bei Unentschieden; eine Tie-Hauptwette zahlt dann 8:1 netto (9-fache Rückzahlung einschließlich Einsatz) und verliert sonst.

Im Paper-/Aus-Modus werden keine realen Chips behauptet. Dort zeigt die Meldung die Pair-Modell-P/L an.

Bei Evolution werden Handgewinner und Pair-Ergebnisse ebenfalls erst nach der Folgehand gesendet. Das Modell enthält die geplante Hauptwette einschließlich Tie. Reale Chip-Platzierungen werden dort als **nicht bestätigt** gekennzeichnet, weil dieser Pfad keine verlässliche Einsatzbestätigung liefert.

Der Telegram-Versand wartet nach dem Handabschluss kurz auf eine neuere sichtbare Balance-Aktualisierung. Falls kein sicherer Kontostand verfügbar ist, steht in der Nachricht `Kontostand: nicht verfügbar`.

## Bestehende automatische Nachrichten

Mit dem Standard-Stoploss `-50`:

- bei **-40 Units**: einmalige Stoploss-Vorwarnung,
- bei **-50 Units**: Stoploss erreicht / Session gestoppt,
- beim positiven **Unit-Ziel**: Ziel erreicht.

Diese drei Meldungen sind **nicht** vom Schalter `Telegram-Signal: ON/OFF` abhängig. Sie werden wie bisher gesendet, sobald `[Telegram] Enabled=1` aktiv ist.

Telegram läuft in separaten Hintergrund-Threads. Ein Internet-/Telegram-Fehler darf Scanner und Autobet nicht blockieren. Der BotToken wird nicht in Log oder Capture ausgegeben.


## Ergebnisdarstellung ab v21.2.113

Jedes freigegebene Signal erhält unabhängig vom Platzierungserfolg eine Paper-Auswertung einschließlich der erforderlichen Hauptwette (Player, Banker oder Tie). Telegram nennt Paper-Hand-P/L und Paper-Session-P/L getrennt von den ausschließlich bestätigten Ist-Einsätzen. Ohne bestätigten Einsatz lautet die Überschrift „NICHT PLATZIERT“, nicht „VERLUST“. Ein ausgeschalteter Telegram-Signalbutton unterdrückt weiterhin Signal-, Ergebnis- und MULTIPLAY-Startmeldungen gemäß der bestehenden Schaltersteuerung.
