"""Runs the Walk-Forward Backtester on real Premier League historical data.
"""

from src.backtest.engine import WalkForwardBacktester


def main():
    backtester = WalkForwardBacktester(
        initial_bankroll=1000.0,
        min_edge=0.035,        # 3.5% minimum edge
        kelly_fraction=0.25,   # Quarter-Kelly staking
        max_stake_cap=0.03,    # 3% bankroll cap per bet
        min_warmup_matches=50
    )

    report = backtester.run(
        csv_path="data/EPL_2324.csv",
        bookmaker_odds_col_prefix="B365"
    )

    print("\n" + "=" * 55)
    print("WALK-FORWARD HISTORICAL BACKTEST RESULTS (EPL 23/24)")
    print("=" * 55)
    for k, v in report.items():
        print(f"  {k:24}: {v}")
    print("=" * 55)

    if backtester.bet_history:
        print("\nSample of Executed Bets (First 5):")
        for b in backtester.bet_history[:5]:
            status = "WON" if b.won else "LOST"
            print(f"[{b.date}] {b.match} -> Pick {b.selection} @ {b.odds_taken} (Fair: {b.pinnacle_fair_odds}) | Stake: ${b.stake_amount} | {status} (PnL: ${b.profit_loss:+.2f}) | CLV: {b.clv*100:+.2f}%")


if __name__ == "__main__":
    main()

