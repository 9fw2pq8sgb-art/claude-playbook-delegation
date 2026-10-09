---
name: delegieren
description: Opus plant, Sonnet und Haiku arbeiten. Das große Modell zerlegt die Aufgabe, schreibt für jeden Teil ein präzises Playbook und gibt die Ausführung an günstige Subagenten (Sonnet 5.5 oder Haiku 5.5); danach prüft es das Ergebnis gegen ein messbares Gate. Nutzen bei jeder Aufgabe mit viel Lesen, vielen Dateien, Wiederholungen oder langen Ausgaben — auch bei kleinen Aufgaben, sobald das Playbook kürzer ist als die Arbeit. Auslöser: "delegier das", "mit Subagenten", "spar Tokens", "lass Haiku/Sonnet das machen", "/playbook:delegieren".
---

# Delegieren — Opus plant, kleine Modelle arbeiten

Du bist der Planer. Deine Intelligenz steckt im **Playbook**, nicht in der Ausführung. Ein gutes Playbook macht ein kleines Modell so gut wie dich, für einen Bruchteil der Tokens.

## 1. Entscheiden: delegieren oder selbst machen?

- **Selbst machen:** Aufgaben, die mit einem einzigen Tool-Aufruf erledigt sind, Rückfragen an den Nutzer, Architektur- und Grundsatzentscheidungen, Mehrdeutiges.
- **Delegieren:** alles, wo das Playbook kürzer ist als die Arbeit — viel lesen, viele Dateien, Wiederholung, lange Ausgaben, Recherche.

Jeder Subagent startet mit leerem Kontext (Startkosten im zehntausender-Token-Bereich, bei Haiku billig). Darum keine Ein-Zeilen-Edits delegieren.

## 2. Modell wählen — eine Frage

> **Muss der Agent etwas entscheiden, das nicht im Playbook steht?**

| Antwort | Modell | `model`-Wert | Typische Arbeit |
|---|---|---|---|
| Nein | **Haiku 5.5** | `"haiku"` | suchen, lesen, extrahieren, zusammenfassen, umbenennen, formatieren, Daten umformen, Tests/Builds laufen lassen |
| Ja | **Sonnet 5.5** | `"sonnet"` | Code schreiben über mehrere Dateien, debuggen, Recherche mit Abwägung, Reviews, Texte |
| Ja, und es ist Architektur oder mehrdeutig | **du selbst** | — | nicht delegieren |

Regeln:
- Setze `model` bei **jedem** `Agent`-Aufruf explizit. Nie Opus als Subagent.
- Im Zweifel Haiku zuerst. Ein Fehlschlag am Gate ist billiger als Sonnet auf Vorrat.
- Unabhängige Teile **parallel** starten: mehrere `Agent`-Aufrufe in einer Nachricht.

## 3. Playbook schreiben (Pflichtform)

Jeder Agent-Auftrag hat genau diese Teile:

```
ZIEL:      Ein Satz. Was am Ende vorliegt.
KONTEXT:   Absolute Pfade, die er lesen soll — keine Inhalte hineinkopieren.
           Fakten, die er nicht selbst herausfinden soll.
SCHRITTE:  Nummeriert, eine Handlung pro Schritt.
           Entscheidungen vorwegnehmen: "nimm X, nicht Y, weil …".
VERBOTE:   Was er nicht anfasst: Dateien, git push, löschen, Nachrichten senden.
GATE:      Der Befehl oder Check, den er selbst ausführt, bevor er "fertig" meldet.
           Wenn möglich mit Gegenprobe: einen bekannten Fehler einspeisen und
           bestätigen, dass der Check ihn findet.
STOPP:     "Wenn etwas nicht zum Playbook passt: abbrechen und melden, nicht raten."
RÜCKGABE:  Exaktes, kurzes Format:
           STATUS: pass | fail | blockiert
           DATEIEN: <geänderte Pfade>
           GATE: <Ausgabe, gekürzt>
           OFFEN: <Punkte oder "keine">
           Keine Prosa.
```

Ein Playbook ist gut, wenn der Agent ohne Rückfrage fertig wird und das Gate grün ist. Fragt er nach oder rät er, war das Playbook zu dünn — nicht das Modell zu klein.

## 4. Prüfen — der Prüfer ist nie der Arbeiter

1. Der Agent führt sein GATE selbst aus und meldet die Ausgabe.
2. **Du prüfst unabhängig nach:** Gate selbst erneut laufen lassen oder eine Stichprobe nehmen. Vertraue der Meldung "pass" nicht blind.
3. Erst wenn dein eigener Check grün ist, ist die Aufgabe fertig.
4. Melde dem Nutzer, was geprüft wurde **und was nicht** (Fehlerklassen ohne Gate).

## 5. Eskalieren bei Fehlschlag

1. Fail → **zuerst das Playbook schärfen** (fehlender Kontext, unklare Entscheidung), gleiches Modell, zweiter Versuch.
2. Wieder Fail → eine Stufe höher: Haiku → Sonnet → du selbst.
3. Merke dir, welcher Aufgabentyp welches Modell brauchte. Das ist die Grundlage für die nächste Modellwahl.

## 6. Wiederverwenden

Läuft ein Playbook grün und kommt die Aufgabe wieder, speichere es als Vorlage (z. B. `playbooks/<aufgabe>.md` im Projekt) mit Platzhaltern in `<…>`. Beim nächsten Mal: laden, Platzhalter füllen, starten.

## Beispiel

Aufgabe: "Finde alle Stellen, an denen die alte API `getUser()` benutzt wird, und stelle sie auf `fetchUser()` um."

- Suche über das Repo → **Haiku**, Rückgabe: Liste `datei:zeile`.
- Umstellung, falls die Signatur sich unterscheidet → **Sonnet**, Playbook nennt alte und neue Signatur sowie das Test-Kommando als GATE.
- Du: Tests selbst erneut laufen lassen, Diff stichprobenartig lesen, dann an den Nutzer melden.
