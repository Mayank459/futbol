"""Local File & Session Odds Ingestion.

Allows ingesting live odds directly from a local JSON file (e.g. data/live_odds.json)
dumped from an active browser session or custom scraping proxy, bypassing Cloudflare safely.
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from src.data.odds_client import MatchOddsComparison, LiveMatch


def load_odds_from_file(file_path: str = "data/live_odds.json") -> Optional[List[MatchOddsComparison]]:
    """Loads and parses odds from a local JSON file if present."""
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matches = []
        for item in data.get("matches", []):
            matches.append(MatchOddsComparison(
                match_id=item["match_id"],
                competition=item.get("competition", "Domestic League"),
                home_team=item["home_team"],
                away_team=item["away_team"],
                kickoff_time=datetime.now(timezone.utc),
                kickoff_str=item.get("kickoff_str", "Today"),
                stake_odds=item["stake_odds"],
                pinnacle_odds=item.get("pinnacle_odds", item["stake_odds"]),
                stake_mirror=item.get("stake_mirror", "stake.ac")
            ))
        return matches
    except Exception as e:
        print(f"Error loading odds from {file_path}: {e}")
        return None


def export_sample_template(file_path: str = "data/live_odds_template.json"):
    """Creates a sample template showing how external live odds can be dumped into data/."""
    template = {
        "source": "stake.ac",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "matches": [
            {
                "match_id": "STAKE_101",
                "competition": "Premier League",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "kickoff_str": "Tomorrow 16:30 UTC",
                "stake_odds": {"home": 1.72, "draw": 3.80, "away": 5.00},
                "pinnacle_odds": {"home": 1.63, "draw": 4.10, "away": 5.80}
            }
        ]
    }
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)

