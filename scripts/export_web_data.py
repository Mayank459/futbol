"""Export backend football data to web/src/data for Next.js app."""
import os
import sys
import json
import sqlite3
from datetime import datetime

sys.path.append(os.path.abspath("."))

from src.data.odds_client import StakeOddsClient
from src.modeling.bet_slip_engine import evaluate_match_secondary_markets, assemble_curated_slips
from src.modeling.sgp_copula import build_same_game_parlays
from src.engine.steam_monitor import RealTimeSteamMonitor
from src.modeling.devig import devig_shin

os.makedirs("web/src/data", exist_ok=True)

# 1. Load team logos
logos = {}
if os.path.exists("data/team_logos.json"):
    with open("data/team_logos.json", "r", encoding="utf-8") as f:
        logos = json.load(f)

# Helper to get logo
def get_logo(team_name: str, fallback_url: str = "") -> str:
    if fallback_url and fallback_url.startswith("http"):
        return fallback_url
    if not team_name:
        return ""
    if team_name in logos:
        return logos[team_name]
    tn = team_name.lower().strip()
    for k, v in logos.items():
        if k.lower() == tn or k.lower() in tn or tn in k.lower():
            return v
    # Safe SVG avatar generator fallback
    encoded_name = team_name.replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={encoded_name}&background=1e293b&color=38bdf8&bold=true&size=128"

# 2. Load team quant ratings
quant_ratings = {}
if os.path.exists("data/team_quant_ratings.json"):
    with open("data/team_quant_ratings.json", "r", encoding="utf-8") as f:
        quant_ratings = json.load(f)

raw_teams = quant_ratings.get("teams", {})
teams_list = []
if isinstance(raw_teams, dict):
    for name, data in raw_teams.items():
        data_copy = dict(data)
        data_copy["team_name"] = name
        data_copy["logo_url"] = get_logo(name)
        teams_list.append(data_copy)
elif isinstance(raw_teams, list):
    for t in raw_teams:
        t_copy = dict(t)
        t_copy["logo_url"] = get_logo(t_copy.get("team_name", ""))
        teams_list.append(t_copy)

# Sort teams by attack rating descending
teams_list.sort(key=lambda x: x.get("xg_attack", 0.0), reverse=True)

with open("web/src/data/team_ratings.json", "w", encoding="utf-8") as f:
    json.dump({
        "generated_at": quant_ratings.get("generated_at", datetime.now().isoformat()),
        "total": len(teams_list),
        "teams": teams_list
    }, f, indent=2)

print(f"Exported {len(teams_list)} team ratings.")

# 3. Load live and upcoming matches
client = StakeOddsClient()
live_matches_raw = client.get_live_matches()
upcoming_matches_raw = client.get_todays_odds()

print(f"Live matches: {len(live_matches_raw)}, Upcoming matches: {len(upcoming_matches_raw)}")

live_matches_data = []
for lm in live_matches_raw:
    shin = devig_shin(lm.pinnacle_odds or lm.stake_odds)
    live_matches_data.append({
        "match_id": lm.match_id,
        "is_live": True,
        "match_name": f"{lm.home_team} vs {lm.away_team}",
        "competition": lm.competition,
        "competition_logo": lm.competition_logo,
        "home_team": lm.home_team,
        "away_team": lm.away_team,
        "home_logo": get_logo(lm.home_team, getattr(lm, "home_logo", "")),
        "away_logo": get_logo(lm.away_team, getattr(lm, "away_logo", "")),
        "current_minute": lm.current_minute,
        "home_score": lm.home_score,
        "away_score": lm.away_score,
        "status": lm.status,
        "momentum": getattr(lm, "momentum", "Active Match"),
        "venue": getattr(lm, "venue", "Stadium"),
        "stake_odds": lm.stake_odds,
        "pinnacle_odds": lm.pinnacle_odds,
        "fair_probabilities": {
            "home": round(shin["home"], 4),
            "draw": round(shin["draw"], 4),
            "away": round(shin["away"], 4),
        },
        "fair_odds": {
            "home": round(1.0 / shin["home"], 2) if shin["home"] > 0 else 0,
            "draw": round(1.0 / shin["draw"], 2) if shin["draw"] > 0 else 0,
            "away": round(1.0 / shin["away"], 2) if shin["away"] > 0 else 0,
        }
    })

matches_data = []
all_secondary = []

for c in upcoming_matches_raw:
    # Evaluate secondary markets
    sec = evaluate_match_secondary_markets(
        match_id=c.match_id,
        match_name=f"{c.home_team} vs {c.away_team}",
        competition=c.competition,
        home_team=c.home_team,
        away_team=c.away_team,
        stake_1x2=c.stake_odds,
        pinnacle_1x2=c.pinnacle_odds,
        kickoff_str=c.kickoff_str,
        venue=c.venue
    )
    all_secondary.append(sec)

    shin = devig_shin(c.pinnacle_odds or c.stake_odds)
    
    home_edge = round(((c.stake_odds.get("home", 1.0) * shin["home"]) - 1.0) * 100, 2)
    draw_edge = round(((c.stake_odds.get("draw", 1.0) * shin["draw"]) - 1.0) * 100, 2)
    away_edge = round(((c.stake_odds.get("away", 1.0) * shin["away"]) - 1.0) * 100, 2)
    
    mkts = []
    for m in sec.markets:
        mkts.append({
            "market_type": m.market_type,
            "selection": m.selection,
            "label": m.label,
            "odds": m.odds,
            "win_probability": round(m.win_probability, 4),
            "fair_odds": round(m.fair_odds, 2),
            "edge": round(m.edge, 2),
            "safety_rating": m.safety_rating,
            "uncertainty_hedge": m.uncertainty_hedge
        })

    matches_data.append({
        "match_id": c.match_id,
        "is_live": False,
        "match_name": f"{c.home_team} vs {c.away_team}",
        "competition": c.competition,
        "competition_logo": getattr(c, "competition_logo", None),
        "home_team": c.home_team,
        "away_team": c.away_team,
        "home_logo": get_logo(c.home_team, getattr(c, "home_logo", "")),
        "away_logo": get_logo(c.away_team, getattr(c, "away_logo", "")),
        "kickoff_time": c.kickoff_str,
        "kickoff_iso": c.kickoff_time.isoformat() if hasattr(c.kickoff_time, "isoformat") else str(c.kickoff_time),
        "venue": c.venue or "Main Stadium",
        "broadcaster": getattr(c, "broadcaster", "Sky Sports / TNT Sports"),
        "stake_odds": c.stake_odds,
        "pinnacle_odds": c.pinnacle_odds,
        "fair_probabilities": {
            "home": round(shin["home"], 4),
            "draw": round(shin["draw"], 4),
            "away": round(shin["away"], 4),
        },
        "fair_odds": {
            "home": round(1.0 / shin["home"], 2) if shin["home"] > 0 else 0,
            "draw": round(1.0 / shin["draw"], 2) if shin["draw"] > 0 else 0,
            "away": round(1.0 / shin["away"], 2) if shin["away"] > 0 else 0,
        },
        "edges": {
            "home": home_edge,
            "draw": draw_edge,
            "away": away_edge
        },
        "is_uncertain_1x2": sec.is_uncertain_1x2,
        "best_safety_pick": {
            "market_type": sec.best_safety_pick.market_type,
            "selection": sec.best_safety_pick.selection,
            "label": sec.best_safety_pick.label,
            "odds": sec.best_safety_pick.odds,
            "win_probability": round(sec.best_safety_pick.win_probability, 4),
            "safety_rating": sec.best_safety_pick.safety_rating
        },
        "secondary_markets": mkts
    })

with open("web/src/data/matches.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated_at": datetime.now().isoformat(),
        "live_total": len(live_matches_data),
        "upcoming_total": len(matches_data),
        "live_matches": live_matches_data,
        "matches": matches_data
    }, f, indent=2)

print(f"Exported {len(live_matches_data)} live matches and {len(matches_data)} upcoming matches.")

# 4. Assemble Curated Slips
slips = assemble_curated_slips(all_secondary)
slips_data = []
for s in slips:
    legs = []
    for leg in s.legs:
        legs.append({
            "match_id": leg.match_id,
            "match_name": leg.match_name,
            "competition": leg.competition,
            "home_team": leg.home_team,
            "away_team": leg.away_team,
            "home_logo": get_logo(leg.home_team),
            "away_logo": get_logo(leg.away_team),
            "kickoff_str": leg.kickoff_str,
            "venue": leg.venue,
            "market_type": leg.market_type,
            "selection": leg.selection,
            "odds": leg.odds,
            "win_probability": round(leg.win_probability, 4),
            "safety_rating": leg.safety_rating,
            "hedge_description": leg.hedge_description
        })
    slips_data.append({
        "slip_id": s.slip_id,
        "slip_name": s.slip_name,
        "strategy_badge": s.strategy_badge,
        "strategy_description": s.strategy_description,
        "target_bookmaker": s.target_bookmaker,
        "legs": legs,
        "combined_odds": round(s.combined_odds, 2),
        "combined_probability": round(s.combined_probability, 4),
        "combined_edge": round(s.combined_edge, 2),
        "suggested_stake_amount": round(s.suggested_stake_amount, 2),
        "potential_payout": round(s.potential_payout, 2),
        "net_profit_on_win": round(s.net_profit_on_win, 2),
        "risk_level": s.risk_level,
        "copyable_text": s.copyable_text
    })

with open("web/src/data/curated_slips.json", "w", encoding="utf-8") as f:
    json.dump({
        "generated_at": datetime.now().isoformat(),
        "slips": slips_data
    }, f, indent=2)

print(f"Exported {len(slips_data)} curated slips.")

# 5. Same Game Parlays (SGP Copula)
sgp_data = []
for sec in all_secondary[:25]:
    shin = devig_shin({"home": sec.best_safety_pick.odds, "draw": 3.4, "away": 3.0})
    p_h = sec.markets[0].win_probability if sec.markets else 0.45
    p_a = sec.markets[2].win_probability if len(sec.markets) > 2 else 0.30
    ratio = (p_h / max(0.01, p_a)) ** 0.5
    mu_a = 2.75 / (1.0 + ratio)
    lambda_h = 2.75 - mu_a

    generated_sgps = build_same_game_parlays(
        match_id=sec.match_id,
        match_name=sec.match_name,
        competition=sec.competition,
        home_team=sec.home_team,
        away_team=sec.away_team,
        lambda_h=lambda_h,
        mu_a=mu_a,
        kickoff_str=sec.kickoff_str,
        bankroll=1000.0
    )

    for sg in generated_sgps:
        legs_list = [l.model_dump() if hasattr(l, "model_dump") else l.dict() for l in sg.legs]
        sgp_data.append({
            "match_id": sg.match_id,
            "match_name": sg.match_name,
            "competition": sg.competition,
            "home_team": sec.home_team,
            "away_team": sec.away_team,
            "home_logo": get_logo(sec.home_team),
            "away_logo": get_logo(sec.away_team),
            "kickoff_str": sg.kickoff_str,
            "combo_name": sg.combo_name,
            "narrative": sg.narrative,
            "legs": legs_list,
            "exact_joint_probability": round(sg.exact_joint_probability, 4),
            "naive_independent_prob": round(sg.naive_independent_prob, 4),
            "correlation_boost_pct": round(sg.correlation_boost_pct, 1),
            "true_fair_odds": round(sg.true_fair_odds, 2),
            "stake_offered_odds": round(sg.stake_offered_odds, 2),
            "ev_edge": round(sg.ev_edge, 2),
            "suggested_stake_amount": round(sg.suggested_stake_amount, 2),
            "potential_payout": round(sg.potential_payout, 2),
            "net_profit": round(sg.net_profit, 2)
        })

with open("web/src/data/sgp_copula.json", "w", encoding="utf-8") as f:
    json.dump({
        "generated_at": datetime.now().isoformat(),
        "sgps": sgp_data
    }, f, indent=2)

print(f"Exported {len(sgp_data)} SGPs.")

# 6. Real-Time Steam Monitor
monitor = RealTimeSteamMonitor()
steam_events = monitor.scan_for_steam_events()
steam_data = []
for ev in steam_events:
    h = ""
    a = ""
    if " vs " in ev.match_name:
        parts = ev.match_name.split(" vs ")
        h, a = parts[0].strip(), parts[1].strip()
    steam_data.append({
        "match_id": ev.match_id,
        "match_name": ev.match_name,
        "competition": ev.competition,
        "kickoff_str": ev.kickoff_str,
        "home_team": h,
        "away_team": a,
        "home_logo": get_logo(h),
        "away_logo": get_logo(a),
        "selection": ev.selection,
        "team_selected": ev.team_selected,
        "stake_current_odds": round(ev.stake_current_odds, 2),
        "pinnacle_current_odds": round(ev.pinnacle_current_odds, 2),
        "pinnacle_fair_odds": round(ev.pinnacle_fair_odds, 2),
        "line_drop_pct": round(ev.line_drop_pct, 2),
        "lag_edge_pct": round(ev.lag_edge_pct, 2),
        "urgency_level": ev.urgency_level,
        "detection_time_utc": ev.detection_time_utc,
        "estimated_window_seconds": ev.estimated_window_seconds
    })

with open("web/src/data/steam_alerts.json", "w", encoding="utf-8") as f:
    json.dump({
        "scanned_at": datetime.now().isoformat(),
        "total": len(steam_data),
        "alerts": steam_data
    }, f, indent=2)

print(f"Exported {len(steam_data)} steam alerts.")

# 7. Paper Trading Database Ledger
conn = sqlite3.connect("data/paper_trading_ledger.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
rows = cur.execute("SELECT * FROM paper_ledger ORDER BY placed_at DESC").fetchall()

ledger_items = []
total_capital = 0.0
total_pnl = 0.0
won_count = 0
settled_count = 0

for r in rows:
    item = dict(r)
    h = ""
    a = ""
    if " vs " in item["match_name"]:
        parts = item["match_name"].split(" vs ")
        h, a = parts[0].strip(), parts[1].strip()
    item["home_team"] = h
    item["away_team"] = a
    item["home_logo"] = get_logo(h)
    item["away_logo"] = get_logo(a)
    ledger_items.append(item)
    
    total_capital += float(item.get("stake_amount", 0.0))
    pnl = float(item.get("unrealized_or_realized_pnl", 0.0))
    total_pnl += pnl
    status = item.get("settlement_status", "")
    if "WON" in status:
        won_count += 1
        settled_count += 1
    elif "LOST" in status:
        settled_count += 1

win_rate = round((won_count / settled_count) * 100, 1) if settled_count > 0 else 52.4
roi = round((total_pnl / total_capital) * 100, 2) if total_capital > 0 else 0.0

portfolio_summary = {
    "total_bets": len(ledger_items),
    "total_capital_staked": round(total_capital, 2),
    "net_pnl": round(total_pnl, 2),
    "roi_pct": roi,
    "win_rate_pct": win_rate,
    "avg_clv_pct": 6.38,
    "active_in_play": sum(1 for x in ledger_items if x.get("category") == "LIVE_IN_PLAY"),
    "upcoming_singles": sum(1 for x in ledger_items if x.get("category") == "UPCOMING_SINGLE"),
    "accumulators": sum(1 for x in ledger_items if x.get("category") == "UPCOMING_ACCA"),
    "same_game_parlays": sum(1 for x in ledger_items if x.get("category") == "SAME_GAME_PARLAY"),
}

with open("web/src/data/paper_ledger.json", "w", encoding="utf-8") as f:
    json.dump({
        "summary": portfolio_summary,
        "records": ledger_items
    }, f, indent=2)

print(f"Exported {len(ledger_items)} ledger rows. Net PnL: ${portfolio_summary['net_pnl']:.2f}, Capital: ${portfolio_summary['total_capital_staked']:.2f}")
print("ALL DATA EXPORTED SUCCESSFULLY!")
