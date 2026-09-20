# Baccarat Counter – v21.2.124 Entwicklungsstand

[v124 mit Quellcode und Windows-Build herunterladen](https://github.com/benkahnt/baccarat-counter/raw/refs/heads/main/BaccaratCounter_v21_2_124_DEVELOPMENT.zip)

Stand: 20.09.2026. **Keine finale Gesamtfreigabe.** Das Archiv enthält
Quellcode, lokale Tests und den vorhandenen x64-Windows-Entwicklungsbuild.
Der Quellcode ist außerdem im Ordner `src` direkt einsehbar.

## Aktueller Umfang

- Casino-Auswahl und Korrekturen der Datenintegritätsprüfung.
- Roosterbet/Pragmatic enthält ausschließlich eine separate lesende Diagnose.
  Sie liefert Statuswerte im Log, keine Integration in Zähltabelle oder Abrechnung.
  Die weitere Roosterbet-Diagnose wurde auf Nutzerwunsch beendet.
- Diagnose-Absturzpfad abgesichert, mobiler Gesamteinsatz ergänzt und
  Protokoll-Feldgrenze korrigiert.
- Keine neue Freigabe der bestehenden Evolution-Funktionen oder Sitzungserhaltung.

## Prüfung dieses Stands

Nativer MSVC-x64-Build erfolgreich, zwei bekannte C4505-Warnungen.
Isolierte Diagnose-/Transporttests, DOM-Probe und Win32-Protokollregression
bestanden. Kurze lesende Live-Prüfung bestätigte Rundenfortschritt am
Pragmatic-Haupttisch und MULTIPLAY, getrennte Walletwerte sowie STOP.
Dies belegt keine vollständige Karten-/Schuherfassung oder reale Wettabwicklung.
Historische versionsgebundene Tests sind keine vollständige v124-Freigabe;
einige benötigen nicht veröffentlichte lokale Session-Testdaten.

## Dateien und Bauen

`build.bat` benötigt Visual Studio C++ Build Tools und das Windows SDK.
Python-Tests benötigen Python, Browser-Fixtures Node.js und gegebenenfalls
Playwright (`PLAYWRIGHT_MODULE` kann dessen Modulpfad angeben).
Die einzige Anpassung an der öffentlichen Quellkopie ersetzt einen privaten
absoluten Playwright-Pfad im Test durch diese portable Modulauflösung.

Das Archiv vollständig entpacken. Der Build liegt unter
`build/BaccaratCounterV124_Development.exe`. Der bestehende Programmstart
kann das mitgelieferte Chrome-Startskript aufrufen; die dokumentierte isolierte
Diagnoseprüfung erfolgte ohne dieses Skript neben der Test-EXE.
Vorhandene Wettfunktionen können echte Einsätze auslösen.

Private INI-Dateien, Tokens, Kontodaten, Sessionaufzeichnungen, Captures und
Browserprofile sind nicht enthalten. `MANIFEST.json` enthält die Dateihashes,
`SHA256SUMS.txt` die Archivprüfsumme. v123 bleibt als historischer Download erhalten.

[Projekt-Board](https://github.com/users/benkahnt/projects/2)
