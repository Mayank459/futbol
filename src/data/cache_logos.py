import urllib.request
import json
import os

leagues = [39, 140, 135, 78]
logos = {}

for lid in leagues:
    url = f"https://v3.football.api-sports.io/teams?league={lid}&season=2023"
    req = urllib.request.Request(url, headers={"x-apisports-key": "59cf31a5455f79eceebdbbf889ba8c59"})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read())
            items = data.get("response", [])
            for item in items:
                t = item.get("team", {})
                name = t.get("name")
                logo = t.get("logo")
                if name and logo:
                    logos[name.lower()] = logo
                    logos[name] = logo
            print(f"League {lid} loaded {len(items)} teams")
    except Exception as e:
        print(f"Error league {lid}: {e}")

aliases = {
    "manchester united": "https://media.api-sports.io/football/teams/33.png",
    "manchester city": "https://media.api-sports.io/football/teams/50.png",
    "arsenal": "https://media.api-sports.io/football/teams/42.png",
    "chelsea": "https://media.api-sports.io/football/teams/49.png",
    "liverpool": "https://media.api-sports.io/football/teams/40.png",
    "tottenham hotspur": "https://media.api-sports.io/football/teams/47.png",
    "newcastle united": "https://media.api-sports.io/football/teams/34.png",
    "aston villa": "https://media.api-sports.io/football/teams/66.png",
    "real madrid": "https://media.api-sports.io/football/teams/541.png",
    "barcelona": "https://media.api-sports.io/football/teams/529.png",
    "atlético madrid": "https://media.api-sports.io/football/teams/530.png",
    "atletico madrid": "https://media.api-sports.io/football/teams/530.png",
    "celta vigo": "https://media.api-sports.io/football/teams/538.png",
    "levante": "https://media.api-sports.io/football/teams/539.png",
    "sevilla": "https://media.api-sports.io/football/teams/536.png",
    "inter milan": "https://media.api-sports.io/football/teams/505.png",
    "ac milan": "https://media.api-sports.io/football/teams/489.png",
    "juventus": "https://media.api-sports.io/football/teams/496.png",
    "napoli": "https://media.api-sports.io/football/teams/492.png",
    "bayern munich": "https://media.api-sports.io/football/teams/157.png",
    "borussia dortmund": "https://media.api-sports.io/football/teams/165.png",
    "bayer leverkusen": "https://media.api-sports.io/football/teams/168.png",
    "rb leipzig": "https://media.api-sports.io/football/teams/173.png"
}
for k, v in aliases.items():
    logos[k] = v

os.makedirs("data", exist_ok=True)
with open("data/team_logos.json", "w", encoding="utf-8") as f:
    json.dump(logos, f, indent=2)

print(f"Total logos cached: {len(logos)}")

