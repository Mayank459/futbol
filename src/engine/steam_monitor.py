"""Market Steam & Latency Arbitrage Monitor.

Tracks real-time line movement velocity between Pinnacle (sharp consensus) and Stake (stake.ac).
Key Capabilities:
1. Calculates Line Movement Velocity: d(Prob)/dt.
2. Identifies Sharp Steam: Rapid price compression caused by high-limit syndicates or breaking team news.
3. Quantifies Execution Lag: Detects when Stake's line hasn't moved yet, offering a positive EV latency window.
4. Alerts: Categorizes by urgency ("CRITICAL - Moving Fast", "HIGH - Stale Line Window", "MODERATE").
"""

import os
import sys
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from src.data.odds_client import StakeOddsClient, MatchOddsComparison
from src.modeling.devig import devig_shin
from src.alerts.telegram_notifier import TelegramNotifier


class SteamEvent(BaseModel):
    match_id: str
    match_name: str
    competition: str
    kickoff_str: str
    selection: str
    team_selected: str
    stake_current_odds: float
    pinnacle_current_odds: float
    pinnacle_fair_odds: float
    historical_pinnacle_odds: Optional[float] = None
    line_drop_pct: float
    lag_edge_pct: float
    urgency_level: str  # "CRITICAL", "HIGH", "MODERATE"
    detection_time_utc: str
    estimated_window_seconds: int = 180


class RealTimeSteamMonitor:
    def __init__(
        self,
        stake_mirror: str = "stake.ac",
        min_steam_edge: float = 0.020,  # 2.0% minimum latency discrepancy
        history_path: str = "data/pinnacle_line_history.json",
        notifier: Optional[TelegramNotifier] = None
    ):
        self.stake_mirror = stake_mirror
        self.min_steam_edge = min_steam_edge
        self.history_path = history_path
        self.notifier = notifier or TelegramNotifier(stake_mirror=stake_mirror)
        self.odds_client = StakeOddsClient(mode="aggregator", stake_mirror=stake_mirror)
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_history(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def scan_for_steam_events(self) -> List[SteamEvent]:
        """Scans all active fixtures for Pinnacle steam movement and Stake execution lag."""
        fixtures = self.odds_client.get_todays_odds()
        active_events: List[SteamEvent] = []
        now_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

        for f in fixtures:
            shin_fair = devig_shin(f.pinnacle_odds)

            # Check both Home and Away
            for sel, team_name in [("home", f.home_team), ("away", f.away_team)]:
                pin_odds = f.pinnacle_odds.get(sel, 2.0)
                stake_odds = f.stake_odds.get(sel, 2.0)
                fair_prob = shin_fair.get(sel, 0.5)
                fair_odds = round(1.0 / fair_prob, 3)

                # Track historical Pinnacle line movement
                hist_key = f"{f.match_id}_{sel}"
                prev_pin = self.history.get(hist_key, {}).get("pinnacle_odds", pin_odds)

                # Line drop calculation (Pinnacle odds compressing = sharp steam)
                line_drop = ((prev_pin - pin_odds) / prev_pin) * 100.0 if prev_pin > 0 else 0.0

                # Latency edge: how much Stake is overpaying compared to Pinnacle Fair
                latency_edge = (stake_odds / fair_odds) - 1.0

                if latency_edge >= self.min_steam_edge:
                    # Urgency classification
                    if latency_edge >= 0.045 or line_drop >= 3.0:
                        urgency = "CRITICAL"
                        win_sec = 120
                    elif latency_edge >= 0.030:
                        urgency = "HIGH"
                        win_sec = 240
                    else:
                        urgency = "MODERATE"
                        win_sec = 360

                    event = SteamEvent(
                        match_id=f.match_id,
                        match_name=f"{f.home_team} vs {f.away_team}",
                        competition=f.competition,
                        kickoff_str=f.kickoff_str,
                        selection=sel.upper(),
                        team_selected=team_name,
                        stake_current_odds=stake_odds,
                        pinnacle_current_odds=pin_odds,
                        pinnacle_fair_odds=round(fair_odds, 2),
                        historical_pinnacle_odds=round(prev_pin, 2) if prev_pin != pin_odds else None,
                        line_drop_pct=round(line_drop, 2),
                        lag_edge_pct=round(latency_edge * 100, 2),
                        urgency_level=urgency,
                        detection_time_utc=now_utc,
                        estimated_window_seconds=win_sec
                    )
                    active_events.append(event)

                # Update history
                self.history[hist_key] = {
                    "pinnacle_odds": pin_odds,
                    "stake_odds": stake_odds,
                    "updated_at": now_utc
                }

        self._save_history()
        return active_events
