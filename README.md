# Playbook-Delegation für Claude Code

**Opus plant. Sonnet und Haiku arbeiten.**

Ein Skill für Claude Code. Das große Modell (Opus) zerlegt eine Aufgabe und schreibt für jeden Teil ein genaues **Playbook**. Günstige Subagenten führen das Playbook aus: **Sonnet 5.5** oder **Haiku 5.5**. Zum Schluss prüft Opus das Ergebnis selbst nach.

Die Intelligenz des großen Modells steckt also im Plan und nicht in der Fleißarbeit. Das spart viele Tokens, und die Qualität bleibt gleich.

**[Interaktive Anleitung öffnen](https://9fw2pq8sgb-art.github.io/claude-playbook-delegation/anleitung.html)**: Ablauf zum Durchklicken, Entscheidungsbaum, Installationsbefehle zum Kopieren.

---

## Installation

**Voraussetzung:** Claude Code **2.1.293 oder neuer**. Die Version zeigt `claude --version`, aktualisieren geht mit `claude update`. Ältere Versionen kennen Haiku 5.5 nicht.

Ein Neustart ist nicht nötig, es gibt zwei Wege.

### Weg A: Claude installiert selbst (am einfachsten)

Diesen Satz in eine laufende Claude-Code-Session kopieren, im Terminal oder in der Desktop-App:

```text
Installiere das Claude-Code-Plugin playbook@playbook-delegation aus dem Marketplace 9fw2pq8sgb-art/claude-playbook-delegation mit "claude plugin marketplace add" und "claude plugin install". Sag mir danach genau, was ich eintippen muss, damit es in dieser Session sofort aktiv ist.
```

Claude installiert das Plugin und sagt dir danach, dass du einmal `/reload-plugins` eintippen musst.

### Weg B: im Terminal

```bash
claude plugin marketplace add 9fw2pq8sgb-art/claude-playbook-delegation
```

```bash
claude plugin install playbook@playbook-delegation
```

**Danach wichtig:** In jeder Session, die schon offen ist, einmal eintippen:

```text
/reload-plugins
```

Das funktioniert auch in der Desktop-App, und ein Neustart der App ist nicht nötig. Neue Sessions laden das Plugin von selbst. Prüfen:

```bash
claude plugin list
```

In der Liste steht `playbook@playbook-delegation` mit Status `enabled`.

## Benutzen

Im Chat von Claude Code:

- `/playbook:delegieren` und dann die Aufgabe beschreiben, **oder**
- einfach sagen: „delegier das“, „mach das mit Subagenten“, „spar Tokens“.

Claude entscheidet selbst, welche Teile an Haiku oder Sonnet gehen und welche es selbst erledigt.

---

## So funktioniert es

### 1. Der Ablauf

![Ablauf: Auftrag, Opus zerlegt, Playbooks, Haiku und Sonnet arbeiten parallel, Gate, Opus prüft nach, fertig](https://raw.githubusercontent.com/9fw2pq8sgb-art/claude-playbook-delegation/main/docs/img/ablauf.svg)

1. **Auftrag:** Du beschreibst die Aufgabe.
2. **Opus zerlegt:** Opus teilt sie in Stücke und entscheidet bei jedem Stück, ob Delegieren sich lohnt. Das ist der Fall, sobald das Playbook kürzer ist als die Arbeit.
3. **Playbooks:** Für jedes Stück schreibt Opus ein Playbook.
4. **Haiku / Sonnet arbeiten:** Unabhängige Stücke laufen parallel.
5. **Gate:** Jeder Agent prüft sein Ergebnis selbst, zum Beispiel mit einem Test, einem Build oder einem Check.
6. **Opus prüft nach:** Opus lässt das Gate noch einmal selbst laufen. Der Prüfer ist nie der Arbeiter.
7. **Fertig.** Fällt das Gate durch, wird zuerst das Playbook geschärft und dann neu gestartet.

### 2. Die Modellwahl: eine Frage

![Modellwahl: Muss der Agent etwas entscheiden, das nicht im Playbook steht?](https://raw.githubusercontent.com/9fw2pq8sgb-art/claude-playbook-delegation/main/docs/img/modellwahl.svg)

| Antwort | Modell | Typische Arbeit |
|---|---|---|
| Nein | **Haiku 5.5** | suchen, lesen, extrahieren, zusammenfassen, umbenennen, formatieren, Tests/Builds laufen lassen |
| Ja | **Sonnet 5.5** | Code über mehrere Dateien, Debugging, Recherche mit Abwägung, Reviews, Texte |
| Ja, Architektur oder mehrdeutig | **Opus selbst** | planen, Grundsatzentscheidungen, Endabnahme |

Im Zweifel nimmt Opus zuerst Haiku. Ein Fehlschlag am Gate kostet weniger, als vorsorglich Sonnet zu nehmen.

### 3. Das Playbook

Jeder Auftrag an einen Agenten hat dieselbe Form:

| Feld | Inhalt |
|---|---|
| **ZIEL** | ein Satz: Was liegt am Ende vor? |
| **KONTEXT** | Pfade zum Lesen und Fakten, die der Agent nicht selbst suchen soll |
| **SCHRITTE** | nummeriert, eine Handlung pro Schritt, Entscheidungen schon getroffen |
| **VERBOTE** | was er nicht anfasst: Dateien, Push, Löschen, Nachrichten |
| **GATE** | der Check, den er vor „fertig“ selbst ausführt |
| **STOPP** | „Passt etwas nicht zum Playbook: abbrechen und melden, nicht raten.“ |
| **RÜCKGABE** | kurz und fest: Status · Dateien · Gate-Ausgabe · offene Punkte |

Fragt ein Agent nach oder rät er, war das Playbook zu dünn. An einem zu kleinen Modell liegt das selten.

### 4. Eskalation

![Eskalation: erst Playbook schärfen, dann eine Stufe höher – Haiku, Sonnet, Opus](https://raw.githubusercontent.com/9fw2pq8sgb-art/claude-playbook-delegation/main/docs/img/eskalation.svg)

1. Fehlschlag: zuerst das Playbook schärfen. Dasselbe Modell versucht es ein zweites Mal.
2. Wieder ein Fehlschlag: eine Stufe höher, also Haiku → Sonnet → Opus selbst.
3. Gute Playbooks werden als Vorlage gespeichert und beim nächsten Mal wiederverwendet.

### 5. Wie viel spart das? (theoretisch)

Die Zahl der Tokens bleibt ungefähr gleich. Was sinkt, ist der **Preis pro Token**. Die kleinen Modelle sind pro Token viel billiger als Opus:

| Modell | Input $/1 Mio. | Output $/1 Mio. | im Vergleich zu Opus |
|---|---|---|---|
| Opus 5.5 | 4,00 | 20,00 | 100 % |
| Sonnet 5.5 | 2,00 | 10,00 | **50 %**, also halber Preis |
| Haiku 5.5 | 0,10 | 0,50 | **2,5 %**, also 40-mal billiger* |

<sub>Anthropic-API-Preise, Stand 06.10.2026. *Haiku-Preis gilt bis 100.000 Tokens Prompt, darüber 0,50 / 2,50 $.</sub>

**Beispielrechnung:** Eine Aufgabe braucht 1 Mio. Tokens Arbeit, davon 80 % Lesen. Opus behält 10 % selbst (planen, Playbooks schreiben, nachprüfen). Dazu kommen 3 Subagenten mit je 67.000 Tokens Startkosten.

![Kostenvergleich: alles Opus 7,20 $, nur Sonnet 4,36 $, Mischung 2,06 $, nur Haiku 0,90 $](https://raw.githubusercontent.com/9fw2pq8sgb-art/claude-playbook-delegation/main/docs/img/ersparnis.svg)

| Szenario | Kosten | Ersparnis |
|---|---|---|
| Alles Opus | 7,20 $ | – |
| Delegiert, nur Sonnet | 4,36 $ | 39 % |
| Delegiert, 1/3 Sonnet + 2/3 Haiku | 2,06 $ | 71 % |
| Delegiert, nur Haiku | 0,90 $ | 87 % |

Was man daraus lernt:

- **Haiku bringt den großen Hebel.** Sonnet halbiert nur den Preis. Darum gilt im Zweifel: Haiku zuerst.
- **Der Opus-Anteil ist die Untergrenze.** Bei „nur Haiku“ entfallen 0,72 $ der 0,90 $ auf die 10 % Planung durch Opus. Ein knappes, gutes Playbook spart also doppelt.
- **Puffer gegen Mehrverbrauch:** Haiku ist 40-mal billiger. Selbst wenn es für dieselbe Arbeit doppelt so viele Tokens bräuchte, bliebe es weit unter Opus.

**Was diese Rechnung nicht weiß:**
- ob ein kleines Modell bei deiner Aufgabe mehr Tokens oder mehr Versuche braucht,
- wie viel Prompt-Caching ohnehin schon spart,
- wie die Nutzungslimits im Abo (Pro/Max) die Modelle gewichten. Die Rechnung nutzt API-Preise.

Die Annahmen stehen in [`tools/ersparnis.py`](tools/ersparnis.py). Eigene Werte eintragen und mit `python3 tools/ersparnis.py` neu rechnen. Das Skript erzeugt auch die Grafik.

---

## Optional: immer aktiv

Der Skill läuft, wenn er aufgerufen wird. Soll er immer gelten, kommen diese Zeilen in die eigene `~/.claude/CLAUDE.md`:

```markdown
## Delegation
Bei jeder Aufgabe mit viel Lesen, vielen Dateien oder Wiederholung den Skill `playbook:delegieren` anwenden:
Opus schreibt das Playbook, Subagenten laufen mit `model: "haiku"` oder `model: "sonnet"`, Opus prüft nach.
```

## Grenzen

- Jeder Subagent startet mit leerem Kontext. Schon der Start kostet Tokens: Gemessen waren es rund 67.000 für eine einzige Antwort. Bei Haiku ist das günstig, für Ein-Zeilen-Aufgaben lohnt es sich trotzdem nicht. Die erledigt Opus selbst.
- Wie viel du sparst, hängt von der Aufgabe ab. Einen pauschalen Wert gibt es nicht.
- Die Namen `haiku` und `sonnet` zeigen über die Anthropic API immer auf die neueste Version. Bei Bedrock, Vertex oder Foundry kann `haiku` noch auf Haiku 4.5 zeigen.

## Ohne Plugin-System installieren

Den Ordner `plugins/playbook/skills/delegieren/` nach `~/.claude/skills/delegieren/` kopieren. Der Aufruf heißt dann `/delegieren`. Updates kommen auf diesem Weg nicht automatisch.

## Aktualisieren und Entfernen

```bash
claude plugin marketplace update playbook-delegation
```

```bash
claude plugin marketplace remove playbook-delegation
```

Der zweite Befehl entfernt das Plugin mit.

## Aufbau

```
.claude-plugin/marketplace.json               # Katalog für "marketplace add"
plugins/playbook/.claude-plugin/plugin.json
plugins/playbook/skills/delegieren/SKILL.md   # der Skill
docs/anleitung.html                           # interaktive Anleitung (GitHub Pages)
docs/img/*.svg                                # Grafiken dieser README
tools/ersparnis.py                            # Kostenrechnung, erzeugt ersparnis.svg
```
