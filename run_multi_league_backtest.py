"""Multi-League Walk-Forward Backtest across Europe's Big 5 Leagues (2023/24).
Refined Sharp Market Strategy (Odds <= 3.20, Sixth-Kelly 0.15, Min Edge 2.5%).
"""

import os
import sys
from tabulate import tabulate
from src.backtest.engine import WalkForwardBacktester
from src.backtest.progress import LiveProgressTracker


def run_all_leagues():
    leagues = [
        {"name": "Premier League", "file": "data/EPL_2324.csv"},
        {"name": "La Liga", "file": "data/LaLiga_2324.csv"},
        {"name": "Serie A", "file": "data/SerieA_2324.csv"},
        {"name": "Bundesliga", "file": "data/Bundesliga_2324.csv"},
        {"name": "Ligue 1", "file": "data/Ligue1_2324.csv"}
    ]

    tracker = LiveProgressTracker(
        league_names=[l["name"] for l in leagues],
        md_path="PROGRESS.md"
    )

    all_reports = []
    total_bets_all = 0
    total_wins_all = 0
    total_staked_all = 0.0
    total_pnl_all = 0.0
    all_clvs = []

    print("\n" + "=" * 65)
    print("RUNNING REFINED MULTI-LEAGUE BACKTEST (EUROPEAN BIG 5 - 23/24)")
    print("Strategy: Pure Sharp Discrepancy | Odds [1.30, 3.20] | Kelly: 0.15")
    print("=" * 65)
    sys.stdout.flush()

    for l in leagues:
        if not os.path.exists(l["file"]):
            continue

        bt = WalkForwardBacktester(
            initial_bankroll=1000.0,
            min_edge=0.025,
            kelly_fraction=0.15,
            max_stake_cap=0.025,
            min_odds=1.30,
            max_odds=3.20
        )

        res = bt.run(
            csv_path=l["file"],
            bookmaker_odds_col_prefix="B365",
            progress_tracker=tracker,
            league_name=l["name"]
        )

        if res.get("total_bets", 0) > 0:
            total_bets_all += res["total_bets"]
            total_wins_all += res["wins"]
            total_pnl_all += res["net_profit"]
            staked = sum(b.stake_amount for b in bt.bet_history)
            total_staked_all += staked
            all_clvs.extend([b.clv for b in bt.bet_history])

            all_reports.append([
                l["name"],
                res["total_bets"],
                f"{res['win_rate']}%",
                f"+{res['average_clv_percent']}%",
                f"+{res['average_edge_percent']}%",
                f"{res['roi_percent']:+.2f}%",
                f"${res['net_profit']:+.2f}",
                f"{res['max_drawdown_percent']:.1f}%",
                f"{res['mean_brier_score']:.4f}"
            ])

    tracker.finish_all()

    headers = ["League", "Bets", "Win Rate", "Avg CLV", "Avg Edge", "ROI", "Net PnL", "Max DD", "Brier Score"]
    print("\n" + tabulate(all_reports, headers=headers, tablefmt="github"))

    agg_win_rate = (total_wins_all / total_bets_all * 100) if total_bets_all > 0 else 0.0
    agg_roi = (total_pnl_all / total_staked_all * 100) if total_staked_all > 0 else 0.0
    agg_clv = (sum(all_clvs) / len(all_clvs) * 100) if all_clvs else 0.0

    print("\n" + "=" * 65)
    print("PORTFOLIO AGGREGATE SUMMARY (REFINED STRATEGY)")
    print("=" * 65)
    print(f"  Total Bets Placed             : {total_bets_all}")
    print(f"  Aggregate Win Rate            : {agg_win_rate:.2f}% ({total_wins_all}/{total_bets_all})")
    print(f"  Aggregate Average CLV         : +{agg_clv:.2f}%")
    print(f"  Total Capital Staked          : ${total_staked_all:.2f}")
    print(f"  Total Net Profit              : ${total_pnl_all:+.2f}")
    print(f"  Aggregate Portfolio ROI       : {agg_roi:+.2f}%")
    print("=" * 65)


if __name__ == "__main__":
    run_all_leagues()
