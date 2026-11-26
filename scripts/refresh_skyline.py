"""Render a skyline from GitHub's public contribution calendar."""
import json
import os
import pathlib
import urllib.request
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parents[1]
QUERY = """query { user(login: "indrajithbandara") { contributionsCollection { contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }"""

def render(weeks):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="760" height="280" viewBox="0 0 760 280"><title>Public contribution skyline</title><rect width="760" height="280" rx="12" fill="#0d1117"/><text x="20" y="30" fill="#56d364" font-family="monospace" font-size="16">$ skyline --public</text>']
    peak = max((d["contributionCount"] for w in weeks for d in w["contributionDays"]), default=1) or 1
    for j in range(7):
        for i, week in enumerate(weeks):
            days = week["contributionDays"]
            if j >= len(days):
                continue
            d = days[j]
            n = d["contributionCount"]
            x, y = 55 + i*12 + j*5, 165 + j*10
            h = round(105*n/peak)
            parts.append(f'<g><title>{escape(d["date"])}: {n} contributions</title><path d="M{x} {y}l8 -4 5 3 -8 4z" fill="#21262d"/>')
            if n:
                parts.append(f'<path d="M{x} {y}v{-h}l8 -4v{h}z" fill="#238636"/><path d="M{x+8} {y-4}v{-h}l5 3v{h}z" fill="#196c2e"/><path d="M{x} {y-h}l8 -4 5 3 -8 4z" fill="#56d364"/>')
            parts.append('</g>')
    parts.append('<text x="20" y="265" fill="#8b949e" font-family="monospace" font-size="12">GitHub contribution calendar | Height relative to peak day</text></svg>')
    return "".join(parts)

def main():
    request = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": QUERY}).encode(), headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Content-Type": "application/json", "User-Agent": "profile-skyline"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError("Contribution query unavailable")
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    if not weeks or len(weeks) > 54:
        raise ValueError("Unexpected calendar")
    (ROOT / "assets" / "contribution-skyline.svg").write_text(render(weeks), encoding="utf-8")

if __name__ == "__main__":
    main()
