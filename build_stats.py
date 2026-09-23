"""Builds stats.svg for the profile README from live GitHub data.
Runs daily in GitHub Actions (see .github/workflows/profile.yml)."""
import json, os, sys, urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "praveenbhat1")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = sys.argv[1] if len(sys.argv) > 1 else "stats.svg"

BG, STROKE, RULE = "#121313", "#2A2B2B", "#222323"
CORAL, CHAMP, MUTED, DIM = "#FF6F59", "#F3E9D2", "#9C9588", "#6F6A62"
SHADES = ["#FF6F59", "#F7A48B", "#E9C9A8", "#B9A68D", "#8C8274", "#5F5A53"]
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


user = get(f"https://api.github.com/users/{USER}")
repos, page = [], 1
while True:
    batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
    repos += batch
    if len(batch) < 100:
        break
    page += 1
own = [r for r in repos if not r["fork"]]

langs = {}
for r in own:
    for name, size in get(r["languages_url"]).items():
        if name in ("HTML", "CSS", "Jupyter Notebook", "Dockerfile", "Shell", "Batchfile"):
            continue  # keep the bar about the languages you write logic in
        langs[name] = langs.get(name, 0) + size
top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
total = sum(v for _, v in top) or 1

stars = sum(r["stargazers_count"] for r in own)
since = user["created_at"][:4]
stats = [(str(len(own)), "public projects"), (str(len(langs)), "languages used"),
         (str(stars), "stars earned"), (since, "on GitHub since")]

W, X0, X1 = 820, 40, 780
parts = []
for i, (num, label) in enumerate(stats):
    x = X0 + i * 185
    parts.append(f'<g class="in" style="animation-delay:{.1+i*.1:.1f}s"><text x="{x}" y="118" font-family="{SANS}" font-size="34" font-weight="700" fill="{CHAMP}" letter-spacing="-1">{num}</text>'
                 f'<text x="{x}" y="140" font-family="{SANS}" font-size="12.5" fill="{MUTED}">{label}</text></g>')

parts.append(f'<text x="{X0}" y="182" font-family="{SANS}" font-size="12.5" fill="{DIM}">Most used languages, by code size</text>')
x = X0
bar_w = X1 - X0
for i, (name, size) in enumerate(top):
    w = bar_w * size / total
    parts.append(f'<rect class="grow" style="animation-delay:{.4+i*.08:.2f}s" x="{x:.1f}" y="194" width="{max(w-2,1):.1f}" height="12" rx="3" fill="{SHADES[i]}"/>')
    x += w
lx, ly = X0, 234
for i, (name, size) in enumerate(top):
    pct = f"{100*size/total:.1f}%"
    label = f"{name} {pct}"
    wlab = len(label) * 7.2 + 30
    if lx + wlab > X1:
        lx, ly = X0, ly + 24
    parts.append(f'<circle cx="{lx+5}" cy="{ly-4}" r="5" fill="{SHADES[i]}"/>'
                 f'<text x="{lx+16}" y="{ly}" font-family="{MONO}" font-size="12" fill="{CHAMP}">{name} <tspan fill="{DIM}">{pct}</tspan></text>')
    lx += wlab
H = ly + 30
updated = datetime.now(timezone.utc).strftime("updated %d %b %Y")

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
  <title id="t">GitHub stats: {len(own)} public projects, {len(langs)} languages, {stars} stars, on GitHub since {since}. Top languages: {", ".join(n for n, _ in top)}.</title>
  <style>
    .in{{opacity:0;animation:f .5s ease-out forwards}}
    .grow{{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:g .7s cubic-bezier(.3,0,.2,1) forwards}}
    @keyframes f{{to{{opacity:1}}}} @keyframes g{{to{{transform:scaleX(1)}}}}
    @media (prefers-reduced-motion:reduce){{.in,.grow{{animation:none;opacity:1;transform:none}}}}
  </style>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{BG}" stroke="{STROKE}"/>
  <text x="{X0}" y="44" font-family="{MONO}" font-size="13" fill="{CORAL}">~/github</text>
  <text x="{X1}" y="44" font-family="{MONO}" font-size="12" fill="{DIM}" text-anchor="end">{updated}</text>
  <line x1="{X0}" y1="62" x2="{X1}" y2="62" stroke="{RULE}"/>
  {"".join(parts)}
</svg>'''
open(OUT, "w").write(svg)
print(f"wrote {OUT}: {len(own)} repos, {len(langs)} langs, {stars} stars, top={top}")
