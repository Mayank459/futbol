"""Daily Value-Betting Orchestrator.

Refined Sharp Market Execution on Stake (stake.ac):
1. Pulls today's fixtures and live odds for Stake (stake.ac) and Pinnacle sharp reference.
2. De-vigs Pinnacle sharp closing line using Shin's method (eliminating favorite-longshot bias).
3. Enforces strict odds bounds (1.30 <= Odds <= 3.20) to eliminate high-variance underdog traps.
4. Filters for pure sharp market discrepancies (Stake price beats Pinnacle fair price by >= 2.5%).
5. Applies Sixth-Kelly (0.15) risk management with a hard 2.5% bankroll cap per pick.
6. Emits a clean report or plainly states 'NO VALUE BETS FOUND'.
7. Logs all picks to SQLite for post-match Closing Line Value (CLV) evaluation.
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Optional

from src.core.schemas import BetRecommendation, MarketType
from src.data.odds_client import StakeOddsClient, MatchOddsComparison
from src.modeling.devig import devig_shin
from src.modeling.value import calculate_edge, calculate_fractional_kelly, evaluate_bet_opportunity
from src.modeling.multibet import build_stake_multibet, MultiBetSlip


class DailyOrchestrator:
    def __init__(
        self,
        bankroll: float = 1000.0,
        min_edge: float = 0.025,         # 2.5% minimum pure sharp edge required
        kelly_fraction: float = 0.15,     # Sixth-Kelly staking for reduced volatility
        max_stake_cap: float = 0.025,     # Max 2.5% bankroll per pick
        min_odds: float = 1.30,          # Minimum odds to prevent low-margin favorites
        max_odds: float = 3.20,          # Maximum odds to ban high-variance longshots
        stake_mirror: str = "stake.ac",
        odds_mode: str = "aggregator",
        db_path: str = "data/bets_history.db"
    ):
        self.bankroll = bankroll
        self.min_edge = min_edge
        self.kelly_fraction = kelly_fraction
        self.max_stake_cap = max_stake_cap
        self.min_odds = min_odds
        self.max_odds = max_odds
        self.stake_mirror = stake_mirror
        self.db_path = db_path
        self.odds_client = StakeOddsClient(mode=odds_mode, stake_mirror=stake_mirror)
        self._init_db()

    def _init_db(self):
        """Initializes SQLite database to store picks and track closing lines."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bet_picks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT,
                    competition TEXT,
                    home_team TEXT,
                    away_team TEXT,
                    selection TEXT,
                    stake_odds REAL,
                    pinnacle_fair_odds REAL,
                    model_prob REAL,
                    edge REAL,
                    stake_fraction REAL,
                    stake_amount REAL,
                    stake_mirror TEXT,
                    created_at TIMESTAMP,
                    closing_odds REAL,
                    clv REAL,
                    result TEXT
                )
            """)
            conn.commit()

    def run_daily_scan(self, historical_csv_path: Optional[str] = None) -> Dict:
        """Executes the daily scan for Stake odds."""
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        print("\n" + "=" * 65)
        print(f"RUNNING REFINED VALUE-BETTING SCAN [Target Bookmaker: Stake ({self.stake_mirror})]")
        print(f"Timestamp: {now_str} | Bankroll: ${self.bankroll:.2f}")
        print(f"Rules: Odds [{self.min_odds}, {self.max_odds}] | Min Sharp Edge: {self.min_edge*100:.1f}% | Kelly: {self.kelly_fraction}")
        print("=" * 65)

        fixtures = self.odds_client.get_todays_odds()
        print(f"Fetched {len(fixtures)} fixtures with live Stake ({self.stake_mirror}) and Pinnacle odds.")

        recommendations: List[BetRecommendation] = []
        market_summary: List[Dict] = []
        candidate_picks_for_multibet: List[Dict] = []

        for f in fixtures:
            # Shin de-vigging on Pinnacle sharp reference line
            pinnacle_fair_probs = devig_shin(f.pinnacle_odds)

            match_info = {
                "match": f"{f.home_team} vs {f.away_team}",
                "competition": f.competition,
                "stake_odds": f.stake_odds,
                "pinnacle_odds": f.pinnacle_odds,
                "fair_sharp_probs": {k: f"{v*100:.1f}%" for k, v in pinnacle_fair_probs.items()},
                "picks": []
            }

            for sel in ["home", "draw", "away"]:
                stake_price = f.stake_odds.get(sel, 0.0)

                # Ban high-variance longshots and low-margin heavy favorites
                if stake_price < self.min_odds or stake_price > self.max_odds:
                    continue

                fair_prob = pinnacle_fair_probs.get(sel, 0.33)
                fair_odds = 1.0 / fair_prob if fair_prob > 0 else 999.0
                sharp_edge = (stake_price / fair_odds) - 1.0

                # Candidate for safe multi-betting if win probability is high (>= 60%)
                if fair_prob >= 0.60:
                    candidate_picks_for_multibet.append({
                        "match_id": f.match_id,
                        "competition": f.competition,
                        "home_team": f.home_team,
                        "away_team": f.away_team,
                        "selection": sel,
                        "offered_odds": stake_price,
                        "fair_sharp_odds": fair_odds,
                        "model_probability": fair_prob,
                        "edge": sharp_edge
                    })

                if sharp_edge >= self.min_edge:
                    stake_fraction = calculate_fractional_kelly(
                        model_prob=fair_prob,
                        odds=stake_price,
                        kelly_fraction=self.kelly_fraction,
                        max_stake_cap=self.max_stake_cap
                    )

                    if stake_fraction > 0:
                        stake_amount = round(self.bankroll * stake_fraction, 2)
                        pick = BetRecommendation(
                            match_id=f.match_id,
                            competition=f.competition,
                            home_team=f.home_team,
                            away_team=f.away_team,
                            market=MarketType.ONE_X_TWO,
                            selection=sel,
                            model_probability=round(fair_prob, 4),
                            offered_odds=stake_price,
                            fair_sharp_odds=round(fair_odds, 3),
                            edge=round(sharp_edge, 4),
                            stake_fraction=stake_fraction,
                            suggested_stake_amount=stake_amount,
                            confidence_label="high" if sharp_edge >= 0.05 else "medium",
                            key_factors=[
                                f"Stake price {stake_price} beats Pinnacle Shin fair price {round(fair_odds, 3)} (+{round(sharp_edge*100, 2)}% pure sharp edge)",
                                f"Within strict odds band [{self.min_odds}, {self.max_odds}] to avoid longshot variance",
                                f"Sixth-Kelly stake: {round(stake_fraction*100, 2)}% of bankroll (${stake_amount})"
                            ],
                            risks=[
                                "Soft-book market update lag",
                                "Match-level outcome variance"
                            ]
                        )
                        recommendations.append(pick)
                        match_info["picks"].append(pick.model_dump())
                        self._log_pick_to_db(pick)

            market_summary.append(match_info)

        # Build Multi-Bet Slip from dominating favorites
        multibet_slip = build_stake_multibet(
            candidate_picks=candidate_picks_for_multibet,
            bankroll=self.bankroll,
            max_legs=3,
            min_leg_probability=0.65
        )

        return self._format_daily_slip(recommendations, market_summary, multibet_slip)

    def _log_pick_to_db(self, pick: BetRecommendation):
        """Persists the pick to the database for post-match CLV settlement."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO bet_picks (
                    match_id, competition, home_team, away_team, selection,
                    stake_odds, pinnacle_fair_odds, model_prob, edge,
                    stake_fraction, stake_amount, stake_mirror, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pick.match_id, pick.competition, pick.home_team, pick.away_team,
                pick.selection, pick.offered_odds, pick.fair_sharp_odds,
                pick.model_probability, pick.edge, pick.stake_fraction,
                pick.suggested_stake_amount, self.stake_mirror,
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()

    def _format_daily_slip(
        self,
        picks: List[BetRecommendation],
        summary: List[Dict],
        multibet_slip: Optional[MultiBetSlip] = None
    ) -> Dict:
        """Formats the daily bet slip and the Multi-Bet slip adhering strictly to Section 1."""
        print("\n" + "=" * 65)
        print(f"DAILY VALUE BET SLIP - STAKE ({self.stake_mirror})")
        print("=" * 65)

        if not picks:
            print(">>> NO SINGLE BETS: No individual matches cleared the +EV edge threshold today.")
        else:
            total_staked = sum(p.suggested_stake_amount or 0.0 for p in picks)
            print(f"Identified {len(picks)} High-Conviction Value Single(s):")
            for i, p in enumerate(picks, 1):
                print(f"\n[{i}] {p.home_team} vs {p.away_team} ({p.competition})")
                print(f"    Selection:       {p.selection.upper()} on Stake ({self.stake_mirror})")
                print(f"    Offered Odds:    {p.offered_odds} (Pinnacle Fair Line: {p.fair_sharp_odds})")
                print(f"    Fair Prob:       {p.model_probability*100:.1f}%")
                print(f"    Pure Sharp Edge: +{p.edge*100:.2f}%")
                print(f"    Suggested Stake: ${p.suggested_stake_amount:.2f} ({p.stake_fraction*100:.2f}% of bankroll)")
                print(f"    Confidence:      {p.confidence_label.upper()}")
                for kf in p.key_factors:
                    print(f"     * {kf}")

            print("\n" + "-" * 65)
            print(f"Total Single Allocation: ${total_staked:.2f} ({(total_staked/self.bankroll)*100:.1f}% of bankroll)")

        # Format Multi-Bet Accumulator Slip
        if multibet_slip and multibet_slip.legs:
            print("\n" + "=" * 65)
            print(f"🎯 RECOMMENDED STAKE MULTI-BET SLIP ({multibet_slip.slip_name})")
            print("=" * 65)
            for i, leg in enumerate(multibet_slip.legs, 1):
                print(f"  Leg {i}: {leg.match_name} ({leg.competition})")
                print(f"         Pick: {leg.selection} ({leg.team_selected}) @ {leg.odds} | Win Prob: {leg.win_probability*100:.1f}% [{leg.safety_rating}]")
            print("-" * 65)
            print(f"  Combined Multiplied Odds : {multibet_slip.combined_odds}x (Odds multiplied on Stake)")
            print(f"  Joint Win Probability    : {multibet_slip.combined_probability*100:.1f}%")
            print(f"  Combined Multi Edge      : +{multibet_slip.combined_edge*100:.2f}%")
            print(f"  Suggested Multi Stake    : ${multibet_slip.suggested_stake_amount:.2f} ({multibet_slip.suggested_stake_fraction*100:.2f}% of bankroll)")
            print(f"  Potential Total Payout   : ${multibet_slip.potential_payout:.2f} (Net Profit: +${multibet_slip.net_profit_on_win:.2f})")
            print("=" * 65)

        return {
            "status": "PICKS_GENERATED",
            "total_picks": len(picks),
            "picks": [p.model_dump() for p in picks],
            "multibet_slip": multibet_slip.model_dump() if multibet_slip else None,
            "summary": summary
        }


if __name__ == "__main__":
    orchestrator = DailyOrchestrator(bankroll=1000.0, stake_mirror="stake.ac", odds_mode="mock")
    orchestrator.run_daily_scan()
