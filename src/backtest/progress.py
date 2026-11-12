"""Live Progress Tracker for Backtests.
Writes real-time status and ASCII progress bar to PROGRESS.md and console.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional


def make_ascii_bar(percent: float, length: int = 20) -> str:
    """Generates an ASCII progress bar, e.g. [██████████░░░░░░░░░░] 50.0%"""
    filled_len = int(round(length * (percent / 100.0)))
    filled_len = max(0, min(length, filled_len))
    bar = "█" * filled_len + "░" * (length - filled_len)
    return f"[{bar}] {percent:.1f}%"


class LiveProgressTracker:
    def __init__(self, league_names: List[str], md_path: str = "PROGRESS.md", expected_matches: Optional[Dict[str, int]] = None):
        self.md_path = md_path
        self.start_time = time.time()
        self.leagues: Dict[str, Dict] = {}
        for name in league_names:
            exp = (expected_matches or {}).get(name, 380 if name in ["Premier League", "La Liga", "Serie A"] else 306)
            self.leagues[name] = {
                "status": "⏳ Pending",
                "current_match": 0,
                "total_matches": exp,
                "bets": 0,
                "wins": 0,
                "clv_sum": 0.0,
                "pnl": 0.0,
                "percent": 0.0
            }
        self.active_league: Optional[str] = None
        self._write_md("Initializing Backtest...")

    def start_league(self, league_name: str, total_matches: int):
        self.active_league = league_name
        self.leagues[league_name]["status"] = "🏃 Running"
        self.leagues[league_name]["total_matches"] = total_matches
        self.update_match(league_name, 0, 0, 0, 0.0, 0.0)

    def update_match(
        self,
        league_name: str,
        current_match: int,
        bets_count: int,
        wins_count: int,
        clv_sum: float,
        pnl: float
    ):
        data = self.leagues[league_name]
        data["current_match"] = current_match
        data["bets"] = bets_count
        data["wins"] = wins_count
        data["clv_sum"] = clv_sum
        data["pnl"] = pnl
        total = data["total_matches"]
        pct = (current_match / total * 100.0) if total > 0 else 0.0
        data["percent"] = min(100.0, pct)

        # Write out to PROGRESS.md
        self._write_md()

    def complete_league(self, league_name: str, final_pnl: float, final_clv: float):
        data = self.leagues[league_name]
        data["status"] = "✅ Completed"
        data["current_match"] = data["total_matches"]
        data["percent"] = 100.0
        data["pnl"] = final_pnl
        self._write_md()

    def finish_all(self):
        self._write_md(finished=True)

    def _write_md(self, finished: bool = False):
        total_matches_all = sum(d["total_matches"] for d in self.leagues.values())
        done_matches_all = sum(d["current_match"] for d in self.leagues.values())
        overall_pct = (done_matches_all / total_matches_all * 100.0) if total_matches_all > 0 else 0.0
        elapsed_sec = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed_sec, 60)

        total_bets = sum(d["bets"] for d in self.leagues.values())
        total_wins = sum(d["wins"] for d in self.leagues.values())
        total_pnl = sum(d["pnl"] for d in self.leagues.values())
        all_clv_sum = sum(d["clv_sum"] for d in self.leagues.values())
        overall_clv = (all_clv_sum / total_bets * 100.0) if total_bets > 0 else 0.0
        overall_win_rate = (total_wins / total_bets * 100.0) if total_bets > 0 else 0.0

        status_text = "🎉 Finished" if finished else f"🏃 Running ({self.active_league or 'Starting...'})"
        overall_bar = make_ascii_bar(overall_pct, length=24)

        lines = [
            "# ⚽ Multi-League Backtest Live Tracker",
            "",
            f"**Status:** {status_text} | **Elapsed:** {mins}m {secs}s | **Last Updated:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            "",
            "## Overall Progress",
            f"`{overall_bar}` &nbsp; **{done_matches_all} / {total_matches_all} matches**",
            "",
            "### Aggregate Portfolio Metrics",
            f"- **Total Bets Placed:** `{total_bets}`",
            f"- **Win Rate:** `{overall_win_rate:.1f}%` ({total_wins} / {total_bets})",
            f"- **Average CLV:** `{overall_clv:+.2f}%` *(vs Pinnacle Closing No-Vig)*",
            f"- **Current Net PnL:** `${total_pnl:+.2f}`",
            "",
            "## Per-League Status",
            "",
            "| League | Status | Progress | Matches | Bets | Win Rate | Avg CLV | Current PnL |",
            "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"
        ]

        for name, d in self.leagues.items():
            bar = make_ascii_bar(d["percent"], length=12)
            wr = f"{(d['wins'] / d['bets'] * 100.0):.1f}%" if d["bets"] > 0 else "N/A"
            clv = f"{(d['clv_sum'] / d['bets'] * 100.0):+.2f}%" if d["bets"] > 0 else "N/A"
            pnl_str = f"${d['pnl']:+.2f}"
            lines.append(f"| **{name}** | {d['status']} | `{bar}` | {d['current_match']}/{d['total_matches']} | {d['bets']} | {wr} | {clv} | {pnl_str} |")

        lines.extend([
            "",
            "> 🔄 *This file auto-updates in real time as the backtest progresses.*",
            "> You can keep this file open in your editor to monitor the live simulation.",
            ""
        ])

        content = "\n".join(lines)
        try:
            with open(self.md_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

