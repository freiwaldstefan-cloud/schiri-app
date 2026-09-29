# Schiri App 2026

**Regeltests und Spieltagstools für Basketball-Schiedsrichter** — eine vollständig eigenständige Single-File-Webanwendung (`index.html`), ohne Server, ohne Build-Schritt, ohne Abhängigkeiten.

Erstellt von [Freiwald & Co – KI-Beratung für Kommunikation](https://freiwald-co.de).

## Funktionen

- **Regeltests**: 25 Zufallsfragen pro Durchlauf aus den offiziellen DBB-Fragenkatalogen 2026 (198 Regelfragen R-1–R-198 und 142 Kampfrichterfragen K-1–K-142), bestanden mit höchstens 7 Fehlern. Lernmodus (sofortige Auflösung) und Prüfungsmodus (Auswertung am Ende), Wiederholung falscher Fragen, Schwächen-Training, „Nur neue Fragen"-Modus, Katalog-Fortschritt und Ergebnis-Verlauf — alles je Katalog getrennt.
- **Regelwerk**: Volltext der Artikel 1–51 sowie Anhang B (Anschreibebogen) und Anhang C (Protest) aus den Offiziellen Basketball-Regeln 2026 (V 1.1, DBB-Übersetzung), mit Suche. Artikel-Nennungen und Fachbegriffe in den Antwort-Erklärungen sind anklickbar und öffnen die Originalstelle, teils mit Sprungmarke und Handzeichen-Bild.
- **Handzeichen**: alle offiziellen Schiedsrichter-Handzeichen (Anhang A, S. 72–78) als eingebettete Bilder.
- **Anschreibebogen**: Anhang-B-Regeln plus Bogen-Beispiele (Bild 9–15).
- **Protest/Spielbericht**: Kurzleitfaden für den Ablauf nach dem Spiel mit Quellen-Links.
- **Gebühren-Rechner**: Spielleitungsgebühren nach NBV Beitrags- und Gebührenkatalog 2026/2027 (Punkt 4.3) inkl. Fahrtkosten (0,30 €/km bzw. Tickets, mind. 6,00 €), weiteren Kosten, Testspiel- und Verkürzungsregeln; Endbetrag wird auf 0,50 € aufgerundet.

## Architektur

Alles liegt in **einer** Datei: `index.html` (~2 MB).

```
index.html
├── <style>      Design-Tokens (Light/Dark via prefers-color-scheme + data-theme),
│                Komponenten-CSS, untere Navigationsleiste
├── HTML         Screens als <section id="scr-*">:
│                home, start (Regeltests), quiz, result, rules, signals,
│                score (Anschreibebogen), protest, fees + Regel-Dialog (#ruleOverlay)
└── <script>     Daten-Konstanten + App-Logik (Vanilla JS, keine Libraries)
```

### Eingebettete Daten-Konstanten (je eine Zeile JSON; nur `FEES` ist mehrzeilig und wird von Hand gepflegt)

| Konstante     | Inhalt                                                        | Quelle |
|---------------|---------------------------------------------------------------|--------|
| `QUESTIONS`   | 198 Regelfragen `{nr,q,a,e,art}` (a: true=Ja)                 | DBB_Schiedsrichter_Fragenkataloge_2026, Tab 1 |
| `KRQUESTIONS` | 142 Kampfrichterfragen, gleiches Schema                       | dito, Tab 2 |
| `RULES`       | `{ "1"–"51", "B", "C": {t: Titel, x: Volltext} }`             | Offizielle Basketball-Regeln 2026 V 1.1 (PDF) |
| `SIGNALS`     | 3 Handzeichen-Ausschnitte (JPEG-Data-URIs, S. 77)             | dito |
| `SIGPAGES`    | 7 Handzeichen-Seiten S. 72–78 (WebP-Data-URIs)                | dito |
| `BPAGES`      | 7 Anschreibebogen-Seiten (Bild 9–15, WebP-Data-URIs)          | dito |
| `FEES`        | 12 Ligen mit Spielleitungsgebühren                            | NBV-Gebührenkatalog 2026/2027, Punkt 4.3 |

### Wichtige Logikbausteine

- `CATALOGS` / `C()` — aktiver Fragenkatalog (r/k) mit eigenen localStorage-Keys.
- `startQuiz(mode, pool?, isRepeat?, kind?)` — Runde starten; `isRepeat`-Runden (Wiederholung/Schwächen) zählen nicht für Verlauf/Bestehen; nur volle 25er-Runden werden gewertet (`PASS_MAX_WRONG = 7`).
- `linkify(text)` — verlinkt `Art. X`, `Art. X/Y`, `Art. B.x` und Fachbegriffe (Technisches/Disruptive/Flagrant Foul, Korrigierbare Fehler) in Erklärungen; `openRule(art, anchor, sig)` öffnet den Regel-Dialog, `sec:`-Anker springen zur Abschnittszeile.
- `goTo(name)` / `show(name)` — Navigation; Leiste wird während einer Quiz-Runde ausgeblendet (`NAV_FOR_SCREEN`).
- `calcFees()` — Gebührenlogik (centgenau; Aufrundung des Endbetrags auf 0,50 €).

### localStorage (pro Browser/Gerät, keine Server-Daten)

`schiriQuizHistory`/`…K` (Verläufe), `schiriQuizQStats`/`…K` (Fragenstatistik für Schwächen/Fortschritt), `schiriQuizCat` (gewählter Katalog). Alle Zugriffe sind try/catch-gekapselt — die App läuft auch ohne Storage.

## Daten aktualisieren

Für neue Kataloge/Regelwerke: offizielle Dateien besorgen, mit `tools/extract_data.py` die JSON-/Bilddaten erzeugen und die entsprechenden `const …=`-Zeilen in `index.html` ersetzen (jede Konstante steht in genau einer Zeile — das Skript kann das automatisch, siehe `python3 tools/extract_data.py --help`). Benötigt: `python3`, `openpyxl`, `Pillow`, `poppler-utils` (pdftotext/pdftoppm).

## Deployment

Statisches Hosting genügt. GitHub Pages: Settings → Pages → „Deploy from a branch" → `main`, `/ (root)` — die App läuft dann unter `https://<user>.github.io/<repo>/`. Jeder beliebige Webspace funktioniert ebenso (Datei hochladen, fertig). Einzige externe Ressource ist die Schriftart (Google Fonts) mit lokalem Fallback.

## Lizenz und Rechte ⚠️

- Der **Programmcode** steht unter MIT-Lizenz (siehe `LICENSE`).
- Die **eingebetteten Inhalte sind davon ausdrücklich ausgenommen**: Fragenkataloge und Regelübersetzung © Deutscher Basketball Bund e. V. (DBB), Regeln © FIBA, Gebührendaten © Niedersächsischer Basketballverband e. V. (NBV). Ihre Weiterverbreitung — auch über dieses Repository — bedarf der Zustimmung der Rechteinhaber. Vor einer Veröffentlichung oder Weitergabe bitte die Freigabe von DBB/NBV einholen bzw. dokumentieren.
- Die App ersetzt keine offiziellen Dokumente: **maßgeblich sind stets die offiziellen FIBA-Regeln und die aktuellen Ordnungen von DBB/NBV.** Alle Angaben ohne Gewähr.
