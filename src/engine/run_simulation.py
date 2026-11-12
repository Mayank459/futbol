import json
from src.engine.paper_trader import PaperTradingEngine

engine = PaperTradingEngine()
live_bets = engine.run_live_matches_simulation()
singles, accas, sgps = engine.run_upcoming_matches_simulation()
summary = engine.get_portfolio_summary()

print("=== PAPER TRADING SIMULATION RESULTS ===")
print(f"Live In-Play Bets:      {len(live_bets)}")
print(f"Upcoming Singles:       {len(singles)}")
print(f"Upcoming Accas:         {len(accas)}")
print(f"Same-Game Parlays:      {len(sgps)}")
print(f"Total Portfolio Bets:   {summary['total_bets']}")
print(f"Total Capital Staked:   ${summary['total_staked']:.2f}")
print(f"Realized PnL (Final):   ${summary['realized_pnl']:+.2f}")
print(f"Unrealized In-Play PnL: ${summary['unrealized_pnl']:+.2f}")
print(f"Total Running PnL:      ${summary['total_pnl']:+.2f} ({summary['roi_pct']:+.2f}% ROI)")

print("\n--- SAMPLE LIVE BETS ---")
for b in live_bets[:6]:
    print(f"[{b.settlement_status}] {b.match_name} ({b.current_match_state}) -> Pick: {b.selection} @ {b.stake_odds} | Stake: ${b.stake_amount} | PnL: ${b.unrealized_or_realized_pnl:+.2f}")

print("\n--- SAMPLE UPCOMING SINGLES ---")
for b in singles[:5]:
    print(f"[{b.settlement_status}] {b.match_name} ({b.kickoff_str}) -> Pick: {b.selection} @ {b.stake_odds} | Stake: ${b.stake_amount} | Potential Profit: +${b.potential_profit:.2f}")

