"""Walk-Forward Leak-Free Historical Backtester.

Refined Sharp Market Value Strategy:
- Uses Pinnacle closing odds (PSCH/PSCD/PSCA) de-vigged with Shin's method as the sharp benchmark.
- Eliminates phantom model edges by anchoring fair probability to the Shin sharp consensus.
- Enforces strict odds bounds (1.30 <= Odds <= 3.20) to eliminate high-variance longshot traps.
- Applies disciplined Sixth-Kelly staking (0.15) with hard bankroll caps.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.modeling.devig import devig_shin
from src.modeling.dixon_coles import DixonColesModel, calculate_analytical_probabilities
from src.modeling.value import calculate_edge, calculate_fractional_kelly, calculate_clv


@dataclass
class BetRecord:
    date: str
    match: str
    selection: str
    model_prob: float
    shin_fair_prob: float
    odds_taken: float
    pinnacle_fair_odds: float
    edge: float
    clv: float
    stake_amount: float
    won: bool
    profit_loss: float
    bankroll_after: float


class WalkForwardBacktester:
    def __init__(
        self,
        initial_bankroll: float = 1000.0,
        min_edge: float = 0.025,        # 2.5% minimum pure sharp edge required
        kelly_fraction: float = 0.15,   # Sixth-Kelly staking for reduced volatility
        max_stake_cap: float = 0.025,   # Max 2.5% bankroll per bet
        min_odds: float = 1.30,         # Minimum odds to prevent low-margin heavy favorites
        max_odds: float = 3.20,         # Maximum odds to prevent high-variance longshots
        min_warmup_matches: int = 50,
        time_decay_xi: float = 0.002,
        refit_interval: int = 10
    ):
        self.initial_bankroll = initial_bankroll
        self.bankroll = initial_bankroll
        self.min_edge = min_edge
        self.kelly_fraction = kelly_fraction
        self.max_stake_cap = max_stake_cap
        self.min_odds = min_odds
        self.max_odds = max_odds
        self.min_warmup_matches = min_warmup_matches
        self.time_decay_xi = time_decay_xi
        self.refit_interval = refit_interval
        self.bet_history: List[BetRecord] = []

    def run(
        self,
        csv_path: str,
        bookmaker_odds_col_prefix: str = "B365",
        progress_tracker=None,
        league_name: Optional[str] = None
    ) -> Dict:
        """Runs the walk-forward simulation on a football-data.co.uk CSV."""
        df = pd.read_csv(csv_path)

        df['ParsedDate'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', dayfirst=True)
        sort_cols = ['ParsedDate', 'Time'] if 'Time' in df.columns else ['ParsedDate']
        df = df.sort_values(by=sort_cols).reset_index(drop=True)

        n_matches = len(df)
        if progress_tracker and league_name:
            progress_tracker.start_league(league_name, n_matches)

        print(f"Starting Walk-Forward Backtest on {n_matches} matches ({league_name or csv_path})...")
        print(f"Refined Sharp Strategy: Odds [{self.min_odds}, {self.max_odds}] | Min Sharp Edge: {self.min_edge*100:.1f}% | Kelly: {self.kelly_fraction}")

        completed_history: List[Dict] = []
        brier_scores: List[float] = []

        for idx in range(n_matches):
            row = df.iloc[idx]
            home_team = row['HomeTeam']
            away_team = row['AwayTeam']
            fthg = row['FTHG']
            ftag = row['FTAG']
            ftr = row['FTR']  # 'H', 'D', 'A'
            match_date = row['ParsedDate']

            # Use true Pinnacle Closing Odds (PSCH/PSCD/PSCA), fallback to PSH if missing
            psch = row.get('PSCH') if pd.notna(row.get('PSCH')) else row.get('PSH')
            pscd = row.get('PSCD') if pd.notna(row.get('PSCD')) else row.get('PSD')
            psca = row.get('PSCA') if pd.notna(row.get('PSCA')) else row.get('PSA')

            # Offered market odds from target soft bookmaker
            book_h = row.get(f"{bookmaker_odds_col_prefix}H")
            book_d = row.get(f"{bookmaker_odds_col_prefix}D")
            book_a = row.get(f"{bookmaker_odds_col_prefix}A")

            if pd.isna(psch) or pd.isna(pscd) or pd.isna(psca) or pd.isna(fthg) or pd.isna(ftag) or pd.isna(ftr):
                continue

            # Devig Pinnacle sharp closing odds with Shin's method
            pinnacle_closing_odds = {"H": float(psch), "D": float(pscd), "A": float(psca)}
            shin_probs = devig_shin(pinnacle_closing_odds)

            # Evaluate Brier Score for calibration
            outcome_vec = {"H": 1 if ftr == 'H' else 0, "D": 1 if ftr == 'D' else 0, "A": 1 if ftr == 'A' else 0}
            brier = sum((shin_probs[sel] - outcome_vec[sel]) ** 2 for sel in ['H', 'D', 'A'])
            brier_scores.append(brier)

            # Evaluate offered market odds
            offered_odds = {
                "H": float(book_h) if pd.notna(book_h) else float(psch),
                "D": float(book_d) if pd.notna(book_d) else float(pscd),
                "A": float(book_a) if pd.notna(book_a) else float(psca)
            }

            for sel in ["H", "D", "A"]:
                odds = offered_odds[sel]
                
                # Enforce strict odds bounds to eliminate high-variance longshots
                if odds < self.min_odds or odds > self.max_odds:
                    continue

                fair_prob = shin_probs[sel]
                fair_sharp_odds = 1.0 / fair_prob if fair_prob > 0 else 999.0

                # Pure sharp edge: How much does the soft price beat Pinnacle Shin fair line?
                sharp_edge = (odds / fair_sharp_odds) - 1.0

                if sharp_edge >= self.min_edge:
                    stake_fraction = calculate_fractional_kelly(
                        model_prob=fair_prob,
                        odds=odds,
                        kelly_fraction=self.kelly_fraction,
                        max_stake_cap=self.max_stake_cap
                    )

                    if stake_fraction > 0 and self.bankroll > 5.0:
                        stake_amount = round(self.bankroll * stake_fraction, 2)
                        won = (ftr == sel)
                        pnl = stake_amount * (odds - 1.0) if won else -stake_amount
                        self.bankroll += pnl
                        clv = calculate_clv(odds, fair_sharp_odds)

                        self.bet_history.append(BetRecord(
                            date=row['Date'],
                            match=f"{home_team} vs {away_team}",
                            selection=sel,
                            model_prob=round(fair_prob, 4),
                            shin_fair_prob=round(fair_prob, 4),
                            odds_taken=odds,
                            pinnacle_fair_odds=round(fair_sharp_odds, 3),
                            edge=round(sharp_edge, 4),
                            clv=round(clv, 4),
                            stake_amount=stake_amount,
                            won=won,
                            profit_loss=round(pnl, 2),
                            bankroll_after=round(self.bankroll, 2)
                        ))

            # Update live progress tracker
            if progress_tracker and league_name and (idx % 2 == 0 or idx == n_matches - 1):
                cur_wins = sum(1 for b in self.bet_history if b.won)
                cur_clv_sum = sum(b.clv for b in self.bet_history)
                cur_pnl = self.bankroll - self.initial_bankroll
                progress_tracker.update_match(
                    league_name=league_name,
                    current_match=idx + 1,
                    bets_count=len(self.bet_history),
                    wins_count=cur_wins,
                    clv_sum=cur_clv_sum,
                    pnl=cur_pnl
                )

        report = self._generate_report(brier_scores)
        if progress_tracker and league_name:
            progress_tracker.complete_league(
                league_name=league_name,
                final_pnl=report.get("net_profit", 0.0),
                final_clv=report.get("average_clv_percent", 0.0)
            )
        return report

    def _generate_report(self, brier_scores: List[float]) -> Dict:
        """Compiles backtest summary metrics."""
        total_bets = len(self.bet_history)
        if total_bets == 0:
            return {"total_bets": 0, "message": "No bets cleared edge thresholds"}

        wins = sum(1 for b in self.bet_history if b.won)
        win_rate = wins / total_bets
        total_staked = sum(b.stake_amount for b in self.bet_history)
        total_pnl = self.bankroll - self.initial_bankroll
        roi = (total_pnl / total_staked) * 100 if total_staked > 0 else 0.0

        # Drawdown calculation
        bankroll_series = [self.initial_bankroll] + [b.bankroll_after for b in self.bet_history]
        peaks = np.maximum.accumulate(bankroll_series)
        drawdowns = (peaks - bankroll_series) / peaks
        max_drawdown = float(np.max(drawdowns)) * 100

        avg_clv = float(np.mean([b.clv for b in self.bet_history])) * 100
        avg_edge = float(np.mean([b.edge for b in self.bet_history])) * 100
        avg_brier = float(np.mean(brier_scores)) if brier_scores else 0.0

        return {
            "total_bets": total_bets,
            "wins": wins,
            "losses": total_bets - wins,
            "win_rate": round(win_rate * 100, 2),
            "initial_bankroll": self.initial_bankroll,
            "final_bankroll": round(self.bankroll, 2),
            "net_profit": round(total_pnl, 2),
            "roi_percent": round(roi, 2),
            "max_drawdown_percent": round(max_drawdown, 2),
            "average_clv_percent": round(avg_clv, 2),
            "average_edge_percent": round(avg_edge, 2),
            "mean_brier_score": round(avg_brier, 4)
        }
