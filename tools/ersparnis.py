"""Theoretische Kostenrechnung: alles mit Opus vs. delegiert. Erzeugt docs/img/ersparnis.svg.
Preise $/1M Tokens (Anthropic API, Stand 06.10.2026). Haiku-Preis gilt bis 100K Prompt."""
import pathlib
P = {"opus": (4.00, 20.00), "sonnet": (2.00, 10.00), "haiku": (0.10, 0.50)}
IN, OUT = 800_000, 200_000      # Beispielaufgabe: 1 Mio. Tokens Arbeit, davon 80 % Lesen
PLAN = 0.10                      # Anteil, den Opus selbst behält (Planen, Playbooks, Nachprüfen)
START = 67_000                   # gemessene Startkosten pro Subagent (Input)
AGENTS = 3

def cost(m, i, o): return (i * P[m][0] + o * P[m][1]) / 1e6

def delegiert(mix):  # mix: Anteil der Worker-Arbeit je Modell
    total = cost("opus", IN * PLAN, OUT * PLAN)
    for m, share in mix.items():
        n = AGENTS * share
        total += cost(m, IN * (1 - PLAN) * share + START * n, OUT * (1 - PLAN) * share)
    return total

basis = cost("opus", IN, OUT)
SZ = [("ALLES OPUS", basis),
      ("DELEGIERT: NUR SONNET", delegiert({"sonnet": 1})),
      ("DELEGIERT: 1/3 SONNET, 2/3 HAIKU", delegiert({"sonnet": 1/3, "haiku": 2/3})),
      ("DELEGIERT: NUR HAIKU", delegiert({"haiku": 1}))]
for n, c in SZ: print(f"{n:34s} ${c:7.4f}  Ersparnis {round((1 - c/basis) * 100)} %")

# Kanarienvogel: reine Opus-Rechnung muss 0 % Ersparnis ergeben
assert abs(cost("opus", IN, OUT) - (0.8*4 + 0.2*20)) < 1e-9

W, BX, BW, ROW = 800, 330, 330, 56
rows = []
for k, (n, c) in enumerate(SZ):
    y = 50 + k * ROW; w = BW * c / basis; acc = k == len(SZ) - 1
    lab = "BASIS" if k == 0 else f"-{round((1 - c/basis) * 100)} %"
    rows.append(f'<text x="24" y="{y+22}" class="l">{n}</text>'
                f'<rect x="{BX}" y="{y+4}" width="{w:.1f}" height="28" fill="{"#00C896" if acc else ("#0A0A0A" if k==0 else "#0D1F2D")}"/>'
                f'<text x="{BX + w + 10:.1f}" y="{y+23}" class="v">${c:.2f}  {lab}</text>')
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {80 + len(SZ)*ROW}" width="100%">
<style>text{{font-family:Futura,'Century Gothic','Avenir Next',Arial,sans-serif;letter-spacing:.04em}}
.l{{font-size:13px;fill:#0A0A0A;font-weight:600}}.v{{font-size:14px;fill:#0A0A0A;font-weight:600}}.n{{font-size:13px;fill:#6B7280}}</style>
<rect width="100%" height="100%" fill="#FFFFFF"/>
<text x="24" y="30" class="l">KOSTEN FÜR 1 MIO. TOKENS ARBEIT (80 % LESEN) · ANTHROPIC-API-PREISE</text>
{"".join(rows)}
<text x="24" y="{62 + len(SZ)*ROW}" class="n">Theoretisch. Annahmen: Opus behält 10 % (Planen, Prüfen), 3 Subagenten mit je 67.000 Tokens Start.</text>
</svg>'''
pathlib.Path(__file__).resolve().parent.parent.joinpath("docs/img/ersparnis.svg").write_text(svg, encoding="utf-8")
