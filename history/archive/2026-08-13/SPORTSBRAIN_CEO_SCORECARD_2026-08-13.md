# SportsBrain — CEO Product Audit & Canonical Scorecard
## Stand: 13. August 2026, 22:46 Europe/Berlin

**Dokumentstatus:** Neuer kanonischer CEO-Bewertungsstand  
**Bewertungsmaßstab:** 10.0 bedeutet praktisch makellos für den definierten Scope — premium, kommerziell vertrauenswürdig, ohne bekannte wesentliche Defekte.  
**Wichtig:** Dieses Dokument ersetzt die frühere Scorecard mit fehlerhafter 105%-Gewichtung. Die Gewichtung hier summiert sich exakt auf **100%**.

---

# 1. Executive Summary

SportsBrain ist heute ein technisch ernstzunehmendes, funktionsreiches internes Sportwetten-Analyse- und Signal-System mit einer bereits überraschend breiten Architektur:

- Football- und Tennis-Datenpipelines
- Odds-Provider und Fallback-Logik
- mehrere Modellklassen
- Value-/EV-Signale
- Kelly-/Stake-Logik
- PWA
- Cloudflare Worker/KV
- GitHub Actions
- macOS launchd Runtime
- Ledger, Settlement, CLV und Kalibration
- automatisierte Live- und Closing-Odds-Updates
- erste echte Release-/CI-Gates

Die größte Schwäche ist inzwischen nicht mehr, dass einzelne Komponenten „schlecht gebaut“ wären. Im Gegenteil: Viele Komponenten sind isoliert bereits ordentlich.

Die zentrale Reife-Lücke lautet:

> **SportsBrain hat noch zu viele parallele Wahrheiten, Pfade und Sicherheitssemantiken.**

Ein Bet, ein Tennis-Event, eine Quote, eine Fixture-Identität, ein Runtime-Health-Zustand oder ein „Production“-Sample kann je nach Pfad unterschiedlich interpretiert werden.

Das ist der Hauptgrund, warum ein technisch komplexes System derzeit noch nicht als kommerziell vertrauenswürdiges Produkt bewertet werden kann.

---

# 2. Was sich heute verändert hat

## 2.1 Der wichtigste Fortschritt: Betting Safety wurde systemisch angegangen

Vor heute war der zentrale Betting-Safety-Zustand:

- Top Recommendations war relativ fail-closed.
- Normale Signal-Cards waren nicht gleich streng.
- Match-Detail-Model-Tips konnten außerhalb des kanonischen Signalpfads zu Bets werden.
- PWA-Stakes konnten den 5%-Cap umgehen.
- Worker vertraute zu stark auf Client-Informationen.
- Consumer schrieb PWA-Bets mit `stake_pct=0.0`.
- `MAX_ACTIVE_BETS` stand im Code auf 5 statt CEO-Regel 3.
- `source=value` war nicht ausreichend beweisbar mit einem konkreten kanonischen Signal verbunden.

Heute wurde daraus ein klar definierter P0-A-Workstream.

Auf der aktuellen P0-A-Branch wurden unter anderem implementiert bzw. stark gehärtet:

- `MAX_ACTIVE_BETS = 3`
- explizite Unterscheidung `source=value` vs `source=manual`
- kanonische Value-Signal-Actionability
- serverseitige Signal-Auflösung per `signal_id`
- Bindung von Match/Market/Sport/Fixture an das kanonische Signal
- `current_odds` statt Scan-Odds für Value-Bets
- harte 30-Minuten-Odds-Freshness
- EV-Obergrenze aus `MAX_EV`
- Tennis `UPCOMING/AWAITING_START/DELAYED` als explizite Pre-Match-Zustände
- LIVE/COMPLETED/POSTPONED/CANCELLED/UNKNOWN fail-closed
- Worker-seitige Bankroll- und Active-Bet-Prüfung aus Backend-State
- 5%-Cap auf Worker- und Consumer-Grenze
- explizite Ledger-Felder für `signal_id`, `fixture_key`, `sport`, `bankroll_at_placement`, `cap_applied`
- SQLite-Erweiterung für neue Bet-Identity
- `model_prob` Prozent→Fraction-Normalisierung
- Kalibrationsfähige Domain `0 < model_prob < 1`
- Node-Worker-Contract-Tests als GitHub-CI-Gate
- neue Consumer-Durability-Architektur
- Risk-State-Heartbeat

Das ist ein **großer Engineering-Fortschritt**.

## 2.2 Aber: Der Fortschritt ist noch nicht Production-Credit

Der aktuelle PR #10 ist zum Zeitpunkt dieses Dokuments **noch offen und ungemerged**.

Deshalb gilt:

> Die heutigen P0-A-Verbesserungen erhöhen den **Projected Score**, aber noch nicht vollständig den **Production Score**.

Das ist absichtlich streng.

Wir bewerten nicht:
> „Code existiert irgendwo auf einer Branch.“

Wir bewerten Production erst hoch, wenn:

1. Finaler Review bestanden
2. Exact-PR-SHA CI grün
3. Merge erfolgt
4. Main-CI grün
5. Worker/PWA deployed
6. Published Data korrekt
7. reale PWA verifiziert
8. keine Regression im Runtime-Verhalten

---

# 3. Neue kanonische Bewertungslogik

Die alte Scorecard war unbrauchbar als kanonische Basis, weil ihre Gewichte insgesamt 105% ergaben.

Ab heute gilt folgende exakt 100%-gewichtete Struktur.

| Bereich | Gewicht |
|---|---:|
| Betting Safety & Actionability | 10% |
| Stake / Risk Governance | 7% |
| Data Integrity | 8% |
| Odds Freshness & Market Correctness | 6% |
| Tennis LIVE Truth | 5% |
| Tennis Schedule & Event State | 5% |
| Fixture Identity | 4% |
| Predictive Model Quality | 8% |
| Calibration | 6% |
| Measurement / CLV / Evaluation | 5% |
| CI / Release Gates | 7% |
| Deployment / Rollback | 5% |
| Monitoring / Trust | 6% |
| PWA UX / Product Quality | 5% |
| Maintainability / Architecture | 4% |
| Governance / Change Control | 3% |
| Security / Privacy | 4% |
| Commercial Readiness | 2% |
| **Gesamt** | **100%** |

---

# 4. Canonical Scorecard — heutiger Stand

## 4.1 Current Production Score

**SportsBrain Production Score: 4.1 / 10**

Das ist eine leichte rechnerische Verschiebung gegenüber dem vorläufigen 4.0-Audit, nicht primär eine Verbesserung des Produkts. Ursache ist die jetzt saubere 100%-Gewichtung.

Der Score bedeutet:

> Ein ernstzunehmendes internes System mit echten produktionsnahen Komponenten, aber noch nicht zuverlässig genug für einen zahlenden externen Nutzer.

## 4.2 Projected Score nach vollständigem P0-A-Abschluss

Wenn P0-A sauber abgeschlossen, gemerged, deployed und real verifiziert wird:

**Projected Score: ca. 4.7 / 10**

Das wäre ein echter substantieller Sprung.

Nicht weil das System plötzlich komplett besser wäre, sondern weil ein sehr hoch gewichteter Kernbereich — **Betting Safety / Risk Governance / Actionability** — von einem fragilen Zustand in Richtung definierter Invarianten verschoben würde.

---

# 5. Detaillierte Ratings

| Bereich | Gewicht | Production heute | Nach sauberem P0-A | Kommentar |
|---|---:|---:|---:|---|
| Betting Safety & Actionability | 10% | 3.8 | 5.8 | Größter heutiger Fortschritt, aber noch ungemerged |
| Stake / Risk Governance | 7% | 3.3 | 5.8 | 5%-Cap + max 3 werden end-to-end deutlich stärker |
| Data Integrity | 8% | 3.9 | 4.6 | Neue Bet-Identity hilft, Alt-/Tennis-Probleme bleiben |
| Odds Freshness & Market Correctness | 6% | 3.7 | 4.4 | Current-Odds-Gates besser; Tennis-Market-Refresh bleibt Risiko |
| Tennis LIVE Truth | 5% | 6.0 | 6.0 | Wave 3A bleibt einer der stärkeren Bereiche |
| Tennis Schedule & Event State | 5% | 4.0 | 4.0 | Source-Authority/TE-Metadaten noch ungelöst |
| Fixture Identity | 4% | 4.9 | 4.9 | Cross-midnight gut, globale Identität noch nicht gelöst |
| Predictive Model Quality | 8% | 4.7 | 4.7 | Positiver Tennis-Holdout, aber Train/Live-Feature-Parität offen |
| Calibration | 6% | 4.4 | 4.7 | P0-A verhindert neue model_prob-Kontamination |
| Measurement / CLV | 5% | 3.6 | 3.9 | Value/Manual-Trennung verbessert Population langfristig |
| CI / Release Gates | 7% | 5.8 | 6.5 | Node Worker Contract jetzt echtes CI-Gate |
| Deployment / Rollback | 5% | 5.1 | 5.3 | Gute Grundlagen, aber Runtime/Data-HEAD-Komplexität bleibt |
| Monitoring / Trust | 6% | 2.7 | 2.7 | Wave 3D noch nicht umgesetzt |
| PWA UX / Product Quality | 5% | 4.8 | 5.3 | Fail-closed UX und Value/Manual-Semantik verbessern Produkt |
| Maintainability / Architecture | 4% | 4.3 | 4.6 | Canonical Contract hilft, aber System bleibt komplex |
| Governance / Change Control | 3% | 2.5 | 3.0 | CEO/Builder/Auditor-Prozess heute deutlich reifer |
| Security / Privacy | 4% | 2.4 | 2.4 | Public-Repo/Privacy/Persistence noch klar ungelöst |
| Commercial Readiness | 2% | 2.1 | 2.4 | Safety-Fortschritt hilft, aber Produkt noch weit weg |
| **Gewichteter Gesamtwert** | **100%** | **4.1** | **~4.7** | |

---

# 6. Was SportsBrain aktuell besonders gut macht

## 6.1 Tennis LIVE Truth

Die Tennis-LIVE-Architektur ist einer der reiferen Teile des Systems.

Die jüngeren Waves haben den Ansatz deutlich verbessert:

- LIVE nicht mehr nur aus Uhrzeit ableiten
- autoritative Evidence
- AWAITING_START / DELAYED
- qualifizierte Quellen
- Heartbeats
- aktuelle Runtime-Publikation

Das ist ein gutes Beispiel dafür, wie SportsBrain aussehen soll:

> Wahrheit wird explizit modelliert und nicht aus einer einzelnen heuristischen Zahl geraten.

Score: **6.0**

Noch nicht höher, weil Open-Bet-Klassifikation und League/Sport-Identity historisch problematisch waren.

---

## 6.2 CI / Release Engineering

Das System hat mittlerweile echte Gates:

- `compileall`
- Core-Smoke
- Rule-7 Enforcement
- E2E Signal Pipeline Smoke
- Ruff Regression
- seit P0-A zusätzlich deterministische Node Worker Contract Tests

Das ist deutlich mehr als bei einem typischen Hobbyprojekt.

Besonders gut:

> Neue Violations dürfen nicht einfach über Baseline-Inflation versteckt werden.

Score heute: **5.8**  
Projected P0-A: **6.5**

Noch keine 7+, weil:

- Full Suite nicht hartes Gate
- reale Browser-Verifikation nicht CI-hard
- Runtime/Data-HEAD verschiebt main ständig
- Source Release SHA und Runtime HEAD sind noch zu wenig explizit getrennt

---

## 6.3 Odds Provider Architecture

Stärken:

- Provider-Tiering
- Fallbacks
- No-bet bei unzuverlässigem Implied Fallback
- H2H sanity
- Thread-safe caches
- explizitere Source-Autorität

Das Grunddesign ist solide.

Das Problem liegt weniger im Provider-Layer selbst als im End-to-End-Mapping:

> Ist die aktuelle Quote wirklich die aktuelle Quote für genau diesen Markt?

Gerade Tennis Side Markets sind hier noch kritisch.

---

## 6.4 Git-Safe-Push Mechanik

`_git_safe_push.sh` und die Branch-Hygiene sind wesentlich besser als am Projektanfang.

Stärken:

- Locking
- erlaubte Bot-Pfade
- Rebase/Pull-Handling
- Source-Konflikte fail-closed
- Runtime-Datenkonflikte teilweise kontrolliert

Das ist nötig, weil SportsBrain Git gleichzeitig als Source-Control und teilweise als Runtime-Datastore benutzt.

Die Komplexität ist jedoch selbst ein Architektur-Risiko.

---

# 7. Größte verbleibende Schwächen

## 7.1 Monitoring / Production Trust

**Score: 2.7**

Das ist wahrscheinlich der größte systemweite Reife-Blocker nach P0-A.

Health prüft momentan hauptsächlich:

- Heartbeat
- Job Cadence
- begrenzte File Freshness

Was noch fehlt:

- ACTIVE + stale odds
- ACTIVE + missing odds
- falsche Market-Quote
- >5%-Stake
- False LIVE
- Tennis Open Bet fehlt im Live Monitor
- Schedule Authority Conflict
- Fixture Collision
- Worker/GitHub Semantik-Drift
- Source Release SHA vs Runtime HEAD
- CI des tatsächlichen Source Release
- Public/Backend Schema Contradictions

Das ist der Kern von **Wave 3D**.

Aber Wave 3D sollte erst starten, nachdem die P0-Invarianten selbst sauber definiert sind.

---

## 7.2 Security / Privacy

**Score: 2.4**

SportsBrain ist aus Security-/Privacy-Sicht noch klar ein internes System.

Probleme:

- Repo ist öffentlich
- persönliche Ledger-/Betting-Daten sind bzw. waren im Repo sichtbar
- Operational State liegt im öffentlichen Projekt
- PWA/Legal-Text beschreibt Persistenz teilweise nicht korrekt
- Browser Token Storage
- URL-Token-Risiken
- Multi-User-Isolation noch nicht stark genug
- Default Snapshot Fallback kann konzeptionell falschen User-State zeigen
- keine klare kommerzielle Privacy-/Data-Isolation-Architektur

Wichtig:

Das Repo einfach spontan privat zu schalten ist keine sichere Lösung, weil GitHub Pages/Deployment berücksichtigt werden müssen.

Es braucht eine geplante Migration.

---

## 7.3 Governance / Change Control

**Score: 2.5**

Heute wurde der menschliche Prozess besser.

Aber im System existiert weiterhin Governance Drift:

CEO-Regeln sagen unter anderem:

- max 3 aktive Bets
- 5% Hard Cap
- keine Auto-Bets
- Failed Gate nie Production
- One Source of Truth
- auditable
- rollback required

Historisch im Code vorhanden:

- MAX_ACTIVE_BETS = 5
- PWA Risk Bypass
- `--auto-log`
- `all_live` Override
- User-Overrides
- autonome AI-Heal-Mechanismen
- mehrere Wahrheitspfade

Besonders kritisch:

`auto_heal_ai.py` kann nach aktuellem Audit potenziell selbst:

- Source editieren
- Tests laufen lassen
- committen
- pushen

Das ist eine Governance-Frage, die explizit entschieden werden muss.

---

## 7.4 Data Integrity

**Score: 3.9**

Die größten strukturellen Probleme:

### Sport/League Identity

Historische Tennis-Bets wurden teilweise als:

- `wm2026`
- blank league

gespeichert.

Generic Markets wie `home/away` erlauben kein zuverlässiges nachträgliches Sport-Inference.

P0-A verbessert neue Bets stark.

Historie und alle Downstream-Consumers sind damit aber noch nicht automatisch sauber.

### Source Classification

`source=value` bedeutete historisch nicht zwingend:

> „durch alle kanonischen Signal-Gates freigegebener Production-Modell-Bet“

Dadurch sind ROI, Calibration und CLV-Populationen kontaminiert.

P0-A kann zukünftige Daten sauberer machen, aber historische Reports bleiben vorsichtig zu interpretieren.

---

# 8. Model Quality

## 8.1 Tennis LGBM

Positives:

Holdout:

- n ≈ 8.581
- Elo Brier ≈ 0.21937
- LGBM Brier ≈ 0.21469
- Verbesserung ≈ 0.00468
- Gate passed

Das ist echte positive Evidenz.

Deshalb bekommt das Model Quality Rating nicht nur 2–3 Punkte.

Aber:

Training nutzt eine chronologisch fortgeschriebene `RollingState`.

Live Prediction erzeugt nach Audit pro Match eine frische/leere `RollingState`.

Betroffene Features:

- Form
- Surface Form
- H2H
- Rest
- Fatigue
- Quality Form
- Tiebreak History

Damit beweist der Holdout:

> Der historische Full-Feature-Pfad ist besser als Elo.

Er beweist noch nicht:

> Der aktuell live servierte Feature-Pfad ist genauso gut.

Das ist ein großer Unterschied.

**Model Quality: 4.7**

---

## 8.2 BL2

Das BL2-LGBM-Gate ist ein gutes Beispiel für richtige Modell-Governance:

- Blend schlug Baseline nicht
- Gate failed
- Model wurde zwar persistiert, aber Production Guard soll Nutzung verhindern

Das ist grundsätzlich gut.

Aber ein failed Model überhaupt persistent neben Production-Artefakten zu halten erhöht Governance-Komplexität.

---

# 9. Calibration

**Score: 4.4**

Aktueller Tennis-Kalibrationsstand aus dem Audit:

- settled total ≈ 505
- Match Winner n ≈ 132
- Brier ≈ .2035
- Log Loss ≈ .5873
- ECE ≈ .0846
- Meta-Calibrator:
  - before ≈ .2035
  - after ≈ .1883

Das ist positiv.

Aber:

- historische Populationen sind nicht vollständig vertrauenswürdig klassifiziert
- Live-Serving-Feature-Shift
- `source=value` historisch nicht gleich canonical production
- match-winner Tennis war nicht immer als Tennis erkennbar

P0-A verbessert zukünftige Messbarkeit durch:

- valid `model_prob`
- explizites `sport`
- `signal_id`
- klare `source`-Semantik

---

# 10. Measurement / CLV

**Score: 3.6**

Aktueller Season-Report aus dem Audit:

Production-artig klassifiziert:

- n ≈ 75
- P&L ≈ +€25.73
- ROI ≈ +4.20%
- Brier ≈ .2453
- Log Loss ≈ .6851
- ECE ≈ .1716
- CLV Coverage ≈ 23.9%
- CLV Hit Rate ≈ 37.5%
- Max Drawdown ≈ €75.62

Wichtig:

Diese Population darf aktuell **nicht** als sauberer Beweis für „SportsBrain-Modell-Production“ interpretiert werden.

Grund:

`source=value` konnte historisch auch über alternative PWA-Pfade entstehen.

Außerdem konnten Tennis-Matchwinner als Football/general in Reports landen.

P0-A macht die **zukünftige Messpopulation** deutlich besser.

---

# 11. PWA / Product Quality

**Score heute: 4.8**

Stärken:

- tatsächliches PWA-Produkt
- mobile Navigation
- Sportansichten
- Signals
- Bet Modal
- History/Open Bets
- Live Status
- Dashboard State
- Token/User Mechanik

Das ist bereits mehr als ein Backend-Dashboard.

Warum noch nicht 6–7:

- Safety-Semantik war über UI-Pfade uneinheitlich
- Top Recommendations und normale Cards waren unterschiedliche Wahrheiten
- Match Detail hatte eigene Value-Semantik
- Odds konnten visuell und beim Submit differieren
- stale/legacy Actionability
- Security/Token UX
- Public Browser Verification nicht immer möglich
- professionelle Error-/Degraded-State UX noch ausbaufähig

P0-A Projected: **5.3**

---

# 12. Tennis Schedule & Event Integrity

**Score: 4.0**

Probleme:

### Source Authority Bug

TennisExplorer Supplemental schreibt:

`source = tennisexplorer`

Downstream-Enrichment erwartet teilweise:

`odds_source`

Fehlt `odds_source`, kann Default `the_odds_api` greifen.

Damit kann FALLBACK-Beobachtung wie PRIMARY aussehen.

### TennisExplorer Metadata

Aktuelle/rezente Produktion zeigte verdächtige Cluster:

- viele ähnliche Kickoff-Zeiten
- fragwürdige Tournament-Zuordnungen
- Cincinnati/m1000-Metadaten bei ungewöhnlichen Spielern

Scraper kann durch Whole-Page-Regex Tournament-/Match-Kontext kollidieren.

Das ist ein echter Data-Trust-Blocker.

---

# 13. Fixture Identity

**Score: 4.9**

Gut:

Wave 3B/3B.1 hat echte Probleme gelöst:

- Cross-midnight
- rescheduled starts
- continuity

Aktueller Fallback:

`normalized_sport_key + canonical_player_pair`

Problem:

Keine sichere globale Eindeutigkeit über:

- Jahr
- Season
- Round
- Draw
- Event Instance

Mögliche Kollision:

gleiche Spieler
+ gleiche wiederkehrende Turnier-ID
+ nächstes Jahr

oder:

Qualifying + Main Draw Rematch.

Langfristig:

> Provider-native stable event IDs sollten Primary Identity sein.

---

# 14. Deployment / Runtime

**Score: 5.1**

SportsBrain ist ungewöhnlich hybrid:

- GitHub Actions
- GitHub Pages
- Cloudflare Worker/KV
- lokaler Mac
- launchd
- Git als Source
- Git teilweise als Runtime-Datastore

Das funktioniert, ist aber komplex.

Positiv:

- Rollback-Denken
- Safe Push
- Source Conflict Handling
- Exact-SHA CI

Negativ:

- `main` bekommt extrem häufig Runtime/Data Commits
- HEAD ist daher nicht automatisch Source Release
- Build/Release SHA kann von Runtime HEAD abweichen
- Debugging wird schwieriger
- Workflow kann Source- und Dataversionen vermischen

Eine wichtige künftige Architekturregel:

> **Source Release SHA und Runtime/Data HEAD müssen als zwei explizite Objekte behandelt werden.**

---

# 15. Monitoring / Trust — Wave 3D Zielbild

Bevor SportsBrain deutlich über 5/10 kommt, braucht es einen echten **Production Trust Monitor**.

Vorgeschlagene zentrale Zustände:

- HEALTHY
- DEGRADED
- UNSAFE

Er sollte mindestens erkennen:

1. actionable signal + stale odds
2. actionable signal + missing current_odds
3. actionable signal + missing EV
4. impossible/absurd EV
5. stake >5%
6. >3 active bets
7. false Tennis LIVE
8. open Tennis bet fehlt in LIVE monitor
9. schedule authority contradiction
10. Worker/GitHub semantic divergence
11. duplicate fixture identity
12. source release without green CI
13. public schema stale
14. risk-state stale
15. market/quote semantic mismatch
16. sport/league identity missing
17. PWA canonical value without signal provenance
18. public/backend bankroll contradiction

Wave 3D darf aber nicht nur einen hübschen Status erzeugen.

> Ein Trust Monitor ist nur so gut wie die Semantik, die er überwacht.

Deshalb war es richtig, P0-A vor Wave 3D zu priorisieren.

---

# 16. Die größten heutigen Lessons Learned

## 16.1 „Tests grün“ ist nicht gleich „Produkt korrekt“

Heute fanden mehrere CEO-Reviews echte Probleme trotz grüner Tests:

- Client-Bankroll als Sicherheitsquelle
- Fake signal_id
- stale Scan Odds
- JS ReferenceError
- falsche event_status Semantik
- model_prob 52 statt .52
- Queue/Delete vor durable persistence
- Consumer Git-Push unerreichbar
- Playwright-Behauptung bei Node-Pure-Function-Tests

Das ist keine Kritik an Tests an sich.

Es bedeutet:

> Die Test-Spezifikation muss dieselben Invarianten kennen wie das Produkt.

---

## 16.2 Claude sollte Builder sein, nicht CEO

Der neue optimale Prozess:

### ChatGPT / CEO

- Architecture
- Investigation
- GitHub Read-only Audit
- Diff Review
- Production Semantics
- Prioritization
- Test Specification
- Scorecard
- Roadmap
- Merge Decision

### Claude / Builder

- konkrete Änderungen
- Tests implementieren
- lokal ausführen
- Commit
- Push/PR
- kurzer Report

Das erhöht sowohl Qualität als auch Token-Effizienz.

---

## 16.3 Prompt-Kürze muss nicht Qualitätsverlust bedeuten

Ein schlechter kurzer Prompt:

> „Fix the betting safety bugs.“

Ein guter kurzer Prompt:

> „In `consume_pending_bets.py::_durable_push`, remote containment is not proven when staged diff is empty. Implement X invariant. Add tests A-D. Do not touch anything else.“

Qualität kommt aus:

- präziser Diagnose
- expliziten Invarianten
- exaktem Scope
- Acceptance Criteria

nicht aus Prompt-Länge allein.

Diese Scorecard kann künftig als persistenter CEO-Kontext dienen, sodass Claude-Prompts nicht jedes Mal die komplette Produktgeschichte wiederholen müssen.

---

# 17. Prioritäten ab morgen

## P0-A — abschließen

Noch offene CEO-Finalpunkte zum aktuellen Zeitpunkt:

1. Remote Durability auch bei lokalem ungepushten Commit beweisen
2. Permanent Reject vs Retryable Failure
3. Cancellation Queue unter dieselbe durable ACK-Invariante bringen
4. echte Playwright-P0-A-Browserverifikation durchführen
5. finaler main sync
6. exact-SHA CI
7. CEO Review
8. Merge
9. Post-Merge CI
10. Worker/PWA/Public Verification

Erst dann:

**P0-A CLOSED**

---

## P0-B — Monitoring Truth

Danach:

`status=ok` darf niemals mit realem failed exit koexistieren.

Health muss semantisch korrekt werden.

---

## P0-C — Privacy / Persistence Architecture

Ziel:

- persönliche Betting-Daten nicht öffentlich
- PWA weiter funktionsfähig
- keine spontane Pages-Zerstörung
- klare User-Isolation
- Legal-/Persistence-Text korrekt

---

## P0-D — Governance / Autonomous Writer

Explizite CEO-Entscheidung:

Was darf `auto_heal_ai.py`?

Empfehlung:

> Diagnose/Proposal erlaubt, autonomer Source-Write/Commit/Push ohne kontrollierten Builder-/Review-Prozess langfristig nicht.

---

## Danach: Wave 3D

Erst nach den zentralen Semantik-/Governance-Fixes.

---

# 18. Top 10 aktuelle Produkt-Risiken

1. Public Privacy / persönliche Ledger-Daten
2. Monitoring erkennt semantische Widersprüche nicht ausreichend
3. Tennis Schedule Source Authority
4. Tennis Market-specific Odds Refresh
5. Historical sport/league contamination
6. Production Measurement Population contamination
7. Train-vs-Live Tennis LGBM Feature Shift
8. Fixture Identity nicht global stabil
9. Autonomous AI source writer / Governance Drift
10. Git als Source + Runtime State erzeugt hohe operative Komplexität

---

# 19. Top 10 aktuelle Stärken

1. Ernstzunehmende End-to-End-Architektur
2. Gute Tennis LIVE-State-Entwicklung
3. Positive Tennis-LGBM-Holdout-Evidenz
4. Solider Odds Provider Layer
5. Git Safe Push deutlich gehärtet
6. CI hat echte harte Gates
7. PWA ist bereits ein echtes nutzbares Produkt
8. Ledger/Settlement/CLV-Pipeline existiert
9. P0-A schafft erstmals echte zentrale Betting-Invarianten
10. CEO/Builder/Auditor-Prozess ist seit heute deutlich professioneller

---

# 20. Was für einen Score von 5.0 nötig ist

SportsBrain überschreitet aus CEO-Sicht die 5.0 nachhaltig, wenn ungefähr folgende Punkte erfüllt sind:

- P0-A vollständig closed und production-verifiziert
- Health Status semantisch korrekt
- keine offensichtliche Queue-/Ledger-Durability-Lücke
- Source/Runtime SHA explizit
- Tennis Schedule Authority korrigiert
- Tennis Market Quote Mapping abgesichert
- neue Bets sauber sport-/signal-identifizierbar
- Production-Metrics Population sauber
- Privacy-Plan aktiv umgesetzt
- Trust Monitor in erster belastbarer Version

---

# 21. Was für einen Score von 6.0 nötig ist

- Monitoring kann zentrale Safety-Contradictions automatisch erkennen
- Security/Privacy nicht mehr klarer Internal-System-Blocker
- Train/Live Model Feature Parity nachgewiesen
- Fixture Identity robust
- CLV Coverage deutlich höher
- historische Messpopulationen bereinigt/segmentiert
- PWA durchgängige Premium-Semantik
- Rollback/Release Flow belastbar
- keine autonome unkontrollierte Source-Mutation
- echte Production Incident Tests

---

# 22. Was für 7+ nötig ist

Ab 7 reden wir nicht mehr über:

> „funktioniert meistens gut“

sondern:

> „echtes production-ready Produkt“.

Dafür braucht SportsBrain unter anderem:

- starke User Isolation
- Security Hardening
- Privacy Migration
- Monitoring & Alerting
- Audit Trail
- reproduzierbare Releases
- Disaster Recovery
- SLOs
- klare Persistence Architecture
- Provider Incident Handling
- belastbare Modell-Monitoring-Pipeline
- langfristige Calibration
- hochwertige PWA UX
- dokumentierte Operations
- keine wesentlichen bekannten Safety-Invarianten verletzt

---

# 23. CEO-Gesamturteil

SportsBrain ist **nicht schlecht**.

Es ist im Gegenteil bereits technisch viel komplexer und ernstzunehmender als ein typisches Hobbyprojekt.

Aber Komplexität ist nicht dasselbe wie Reife.

Aktuell gilt:

> **SportsBrain hat viele gute Komponenten, aber noch nicht genug globale Wahrheiten.**

Der nächste große Reife-Sprung entsteht nicht primär durch:

- mehr Modelle
- mehr Sportarten
- mehr Signale
- mehr UI

sondern durch:

- eine Wahrheit pro Konzept
- fail-closed Invarianten
- saubere Identity
- durable Persistence
- Trust Monitoring
- Security/Privacy
- kontrollierte Governance

Heute war deshalb ein sehr produktiver Tag, obwohl kaum etwas sichtbar „Neues“ für den Endnutzer entstanden ist.

Wir haben begonnen, einen der gefährlichsten Teile des Systems — **Betting Actionability und Risk Enforcement** — von einer Sammlung lokaler Regeln zu einer systemweiten Invariante umzubauen.

Das ist aus CEO-Sicht wertvoller als mehrere neue Features.

---

# 24. Canonical Snapshot

**Datum:** 2026-08-13 22:46 Europe/Berlin

**Current main:** Runtime/Data HEAD bewegt sich weiter durch Bot-Commits. Zum Audit-Zeitpunkt lag `main` bei einem Tennis-Live-Runtime-Commit.

**P0-A PR:** #10  
**P0-A Branch:** `p0/p0a-corrections`  
**P0-A Status:** OPEN / not merged  
**Current Production Score:** **4.1 / 10**  
**Projected after fully verified P0-A:** **~4.7 / 10**

**Highest-rated area:** Tennis LIVE Truth — 6.0  
**Lowest-rated area:** Commercial Readiness — 2.1  
**Most important technical next step:** P0-A final durability closure  
**Most important systemic next step after P0-A:** Monitoring Truth / Production Trust  
**Most important business-risk area:** Security & Privacy

---

# 25. Bewertungsregel für zukünftige Updates

Ab jetzt wird diese Datei nach jedem größeren Workstream nach denselben Regeln aktualisiert:

1. **Keine Punkte für ungemergten Code als Production Score.**
2. Branch-/Projected Scores separat.
3. Score kann auch fallen.
4. Tests alleine erhöhen keinen Score.
5. Jeder Score-Anstieg braucht konkrete neue Evidenz.
6. Security, Reliability und Data Integrity wiegen stärker als neue Features.
7. 10.0 bleibt wörtlich „praktisch makellos“.
8. Alle Gewichte müssen exakt 100% ergeben.

Damit wird diese Scorecard zum langfristigen CEO-Messinstrument für SportsBrain.
