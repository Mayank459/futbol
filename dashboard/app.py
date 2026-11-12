"""Stake.ac Autonomous Football Betting Agent Dashboard.

Tabs:
1. ⚽ Match Center (Live in-play + Upcoming fixtures sorted by league tier with collapsible expanders).
2. 🎯 Precision Bet Slips & Same-Game Parlays (Fortress Acca, Uncertainty Hedge, +EV Multiplier, Double Lock, and Correlated SGP Copula).
3. ⚡ Quant Lab & Real-Time Steam Monitor (xG Calibrated Ratings, Online Kalman Momentum, and Pinnacle-Stake Latency Arbitrage Alerts).
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timezone
from typing import List, Dict, Tuple

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.orchestrator import DailyOrchestrator
from src.data.odds_client import StakeOddsClient, MatchOddsComparison, LiveMatch
from src.modeling.devig import devig_shin
from src.modeling.bet_slip_engine import (
    evaluate_match_secondary_markets,
    assemble_curated_slips,
    MatchSecondaryMarkets,
    CuratedBetSlip
)
from src.modeling.sgp_copula import build_same_game_parlays, SameGameParlay
from src.engine.steam_monitor import RealTimeSteamMonitor, SteamEvent
from src.engine.paper_trader import PaperTradingEngine, PaperBet

st.set_page_config(
    page_title="Stake.ac Match & Quant Center",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Broadcast Scoreboard & Bet Slip Custom CSS
st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp {
        background-color: #0a0c10;
        color: #e2e8f0;
    }
    
    /* Broadcast Scoreboard Card */
    .broadcast-card {
        background-color: #13161f;
        border: 1px solid #222736;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .broadcast-card:hover {
        border-color: #384252;
        transform: translateY(-1px);
    }
    
    /* Top Header: Centered Competition & Round */
    .card-header-league {
        text-align: center;
        font-size: 1.25em;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.5px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
    }
    
    /* Subheader: Date, Stadium, Broadcast */
    .card-subheader {
        text-align: center;
        font-size: 0.9em;
        color: #8c96a5;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        margin-bottom: 14px;
    }
    
    /* Date Pill in Subheader */
    .date-pill {
        background: #1b2333;
        color: #63b3ed;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.92em;
        border: 1px solid #2b3952;
    }
    
    /* Divider Line */
    .card-divider {
        border: none;
        border-top: 1px solid #222736;
        margin: 0 0 18px 0;
    }
    
    /* Scoreboard 3-Column Grid */
    .scoreboard-row {
        display: grid;
        grid-template-columns: 1fr 160px 1fr;
        align-items: center;
        margin-bottom: 16px;
    }
    .team-home {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 16px;
        font-size: 1.5em;
        font-weight: 700;
        color: #ffffff;
        text-align: right;
    }
    .team-away {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 16px;
        font-size: 1.5em;
        font-weight: 700;
        color: #ffffff;
        text-align: left;
    }
    .team-crest {
        width: 48px;
        height: 48px;
        object-fit: contain;
        filter: drop-shadow(0 2px 6px rgba(0,0,0,0.5));
    }
    .team-crest-fallback {
        width: 46px;
        height: 46px;
        background: #232834;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3em;
    }
    
    /* Center Score & Glowing Neon Clock */
    .center-score {
        text-align: center;
    }
    .score-numbers {
        font-size: 2.8em;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 4px;
        line-height: 1.1;
    }
    .score-clock {
        font-size: 1.2em;
        font-weight: 800;
        color: #00ff66;
        margin-top: 4px;
        letter-spacing: 1px;
        text-shadow: 0 0 10px rgba(0, 255, 102, 0.45);
    }
    .clock-upcoming {
        color: #63b3ed;
        font-size: 0.95em;
        font-weight: 700;
        text-shadow: none;
    }
    
    /* Bottom Stake Odds Bar */
    .odds-bar {
        background-color: #0b0e14;
        border: 1px solid #1a202c;
        border-radius: 8px;
        padding: 10px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.92em;
    }
    .odds-numbers {
        color: #cbd5e0;
        font-family: monospace;
    }
    .odds-val {
        color: #00ff66;
        font-weight: 800;
        font-size: 1.05em;
    }
    .badge-signal {
        background: #0e3318;
        color: #00ff66;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 800;
        font-size: 0.82em;
        letter-spacing: 0.5px;
    }
    
    /* ======================================================== */
    /* ENHANCED BET SLIP STYLING                                */
    /* ======================================================== */
    .slip-container {
        background: linear-gradient(145deg, #131722 0%, #0d1017 100%);
        border: 2px solid #232a38;
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 28px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.55);
    }
    .slip-header-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 1px solid #232a38;
        padding-bottom: 16px;
        margin-bottom: 18px;
    }
    .slip-title {
        font-size: 1.5em;
        font-weight: 900;
        color: #ffffff;
        margin: 6px 0 2px 0;
        letter-spacing: 0.5px;
    }
    .slip-odds-multiplier {
        font-size: 2.2em;
        font-weight: 900;
        color: #00ff66;
        text-shadow: 0 0 16px rgba(0, 255, 102, 0.45);
        line-height: 1;
    }
    
    /* Slip Financial Metrics Grid */
    .slip-metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        background-color: #090c12;
        border: 1px solid #1c2230;
        border-radius: 10px;
        padding: 14px 20px;
        margin-bottom: 22px;
    }
    .metric-cell {
        text-align: center;
    }
    .metric-cell .label {
        font-size: 0.78em;
        color: #8c96a5;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.8px;
    }
    .metric-cell .val {
        font-size: 1.35em;
        font-weight: 900;
        color: #ffffff;
        margin-top: 3px;
    }
    
    /* Ticket-Style Individual Leg Card */
    .leg-card {
        background-color: #161b26;
        border: 1px solid #252d3d;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: border-color 0.15s ease;
    }
    .leg-card:hover {
        border-color: #3b465c;
    }
    .leg-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .leg-badge-num {
        background: #232d42;
        color: #63b3ed;
        font-weight: 800;
        font-size: 0.8em;
        padding: 2px 8px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    .leg-date-pill {
        background: #111e2e;
        color: #38bdf8;
        border: 1px solid #1e3a5f;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.84em;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .leg-matchup-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .leg-teams {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 1.15em;
        font-weight: 700;
        color: #ffffff;
    }
    .leg-mini-crest {
        width: 26px;
        height: 26px;
        object-fit: contain;
    }
    .market-tag {
        font-size: 0.82em;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 5px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .market-tag-dnb {
        background: #2b173d;
        color: #c084fc;
        border: 1px solid #4a2868;
    }
    .market-tag-dc {
        background: #132e3d;
        color: #38bdf8;
        border: 1px solid #1d4d66;
    }
    .market-tag-btts {
        background: #3b2812;
        color: #fbbf24;
        border: 1px solid #63431d;
    }
    .market-tag-goal {
        background: #0f3325;
        color: #34d399;
        border: 1px solid #19543d;
    }
    .market-tag-1x2 {
        background: #1e2533;
        color: #94a3b8;
        border: 1px solid #334155;
    }
    
    .leg-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #0d1017;
        border-radius: 6px;
        padding: 8px 14px;
        border: 1px solid #1e2433;
    }
    .leg-pick-text {
        font-size: 1.05em;
        font-weight: 800;
        color: #00ff66;
    }
    .leg-prob-text {
        font-size: 0.85em;
        color: #cbd5e1;
    }
    
    /* Market Comparison Grid Box */
    .market-box {
        background: #131722;
        border: 1px solid #242c3d;
        border-radius: 10px;
        padding: 14px 16px;
        text-align: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.3);
    }
    .market-box-title {
        font-size: 0.82em;
        color: #8c96a5;
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: 0.5px;
    }
    .market-box-pick {
        font-size: 1.1em;
        font-weight: 800;
        color: #ffffff;
        margin: 6px 0;
    }
    .market-box-odds {
        font-size: 1.3em;
        font-weight: 900;
        color: #00ff66;
    }
    
    /* Steam Alert Banner */
    .steam-banner {
        background: linear-gradient(135deg, #261605 0%, #150c02 100%);
        border: 1px solid #f59e0b;
        border-radius: 10px;
        padding: 14px 20px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# System Constants
STAKE_MIRROR = "stake.ac"
BANKROLL = 1000.0

# Load European Club Logos Cache
LOGOS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "team_logos.json")
CLUB_LOGOS: Dict[str, str] = {}
if os.path.exists(LOGOS_PATH):
    try:
        with open(LOGOS_PATH, "r", encoding="utf-8") as f:
            CLUB_LOGOS = json.load(f)
    except Exception:
        CLUB_LOGOS = {}


def get_club_logo_url(team_name: str) -> str:
    """Resolve club logo URL with fallback matching."""
    t_clean = team_name.lower().strip()
    if t_clean in CLUB_LOGOS:
        return CLUB_LOGOS[t_clean]
    for key, url in CLUB_LOGOS.items():
        if key in t_clean or t_clean in key:
            return url
    return ""


# Load Pre-computed Quant Ratings Cache (xG and Kalman)
QUANT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "team_quant_ratings.json")
QUANT_RATINGS: Dict = {}
if os.path.exists(QUANT_PATH):
    try:
        with open(QUANT_PATH, "r", encoding="utf-8") as f:
            QUANT_RATINGS = json.load(f)
    except Exception:
        QUANT_RATINGS = {}


# Strict League Tier Hierarchy (Elite European leagues and International Break ranked first)
LEAGUE_TIER_ORDER: List[Tuple[str, int, str]] = [
    ("nations league", 0, "UEFA Nations League (International Break)"),
    ("international", 0, "International Matches"),
    ("friendl", 0, "International Friendlies"),
    ("world cup", 0, "FIFA World Cup Qualifiers"),
    ("euro", 0, "UEFA Euro Championship"),
    ("champions league", 1, "UEFA Champions League"),
    ("ucl", 1, "UEFA Champions League"),
    ("europa league", 2, "UEFA Europa League"),
    ("premier league", 3, "English Premier League"),
    ("epl", 3, "English Premier League"),
    ("la liga", 4, "Spanish La Liga"),
    ("laliga", 4, "Spanish La Liga"),
    ("primera división", 4, "Spanish La Liga"),
    ("serie a", 5, "Italian Serie A"),
    ("bundesliga", 6, "German Bundesliga"),
    ("ligue 1", 7, "French Ligue 1"),
    ("conference league", 8, "UEFA Conference League"),
    ("eredivisie", 9, "Dutch Eredivisie"),
    ("primeira liga", 10, "Portuguese Primeira Liga"),
    ("liga portugal", 10, "Portuguese Primeira Liga"),
    ("championship", 11, "English Championship"),
    ("super league", 12, "European Super League"),
    ("super lig", 12, "Turkish Super Lig"),
    ("ekstraklasa", 13, "Polish Ekstraklasa"),
    ("serie b", 14, "Italian Serie B"),
    ("segunda", 15, "Spanish Segunda División"),
    ("2. bundesliga", 16, "German 2. Bundesliga"),
    ("ligue 2", 17, "French Ligue 2"),
    ("primera a", 18, "Colombian Primera A"),
    ("brasileir", 19, "Brazilian Serie A"),
    ("liga mx", 20, "Mexican Liga MX"),
    ("mls", 21, "Major League Soccer"),
    ("pro league", 22, "Pro League"),
    ("i liga", 23, "Polish I Liga"),
    ("1a divisió", 24, "Andorran 1a Divisió"),
    ("rfef", 25, "Spanish RFEF Lower Tier"),
]


def classify_league(comp_name: str) -> Tuple[int, str]:
    """Returns (tier_rank, clean_label) where tier 1 is the best/highest tier."""
    c_lower = comp_name.lower()
    for pattern, rank, label in LEAGUE_TIER_ORDER:
        if pattern in c_lower:
            if "rfef" in c_lower and rank == 4:
                continue
            if "2." in c_lower and rank == 6:
                continue
            return (rank, label)
    return (999, comp_name)


# Sidebar Configuration (Zero-Input, Informative Only)
st.sidebar.image("https://img.icons8.com/fluency/96/football2--v1.png", width=64)
st.sidebar.title("🤖 Stake Quant Agent")
st.sidebar.markdown("**Mode:** `Autonomous Zero-Input`")
st.sidebar.success("🟢 Real-Time API Stream Active")
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Target Site:** `Stake ({STAKE_MIRROR})`")
st.sidebar.markdown("**Sharp Baseline:** `Pinnacle (Shin Fair)`")
st.sidebar.markdown("**Model Engine:** `xG Dixon-Coles + Kalman`")
st.sidebar.markdown(f"**System Bankroll:** `${BANKROLL:,.2f}`")
st.sidebar.markdown(f"**Odds Band:** `[1.20, 3.20]`")
st.sidebar.markdown("---")
expand_all = st.sidebar.toggle("Expand All League Sections", value=False)
st.sidebar.caption(f"🕒 Engine Refresh: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")

# Load Live Data and Odds
client = StakeOddsClient(mode="aggregator", stake_mirror=STAKE_MIRROR)
live_matches = client.get_live_matches()
upcoming_matches = client.get_todays_odds()

# Evaluate Secondary Markets for all upcoming matches
evaluated_secondary = [
    evaluate_match_secondary_markets(
        match_id=m.match_id,
        match_name=f"{m.home_team} vs {m.away_team}",
        competition=m.competition,
        home_team=m.home_team,
        away_team=m.away_team,
        stake_1x2=m.stake_odds,
        pinnacle_1x2=m.pinnacle_odds,
        kickoff_str=m.kickoff_str,
        venue=m.venue
    )
    for m in upcoming_matches
]

# Generate Curated Multi-Bet Slips
curated_slips = assemble_curated_slips(evaluated_secondary, bankroll=BANKROLL)

# Run Real-Time Steam Monitor
steam_monitor = RealTimeSteamMonitor(stake_mirror=STAKE_MIRROR, min_steam_edge=0.02)
steam_events = steam_monitor.scan_for_steam_events()

# Run Paper-Trading Simulation Engine
paper_engine = PaperTradingEngine(bankroll=BANKROLL, stake_mirror=STAKE_MIRROR)
paper_live_bets = paper_engine.run_live_matches_simulation()
paper_singles, paper_accas, paper_sgps = paper_engine.run_upcoming_matches_simulation()
paper_summary = paper_engine.get_portfolio_summary()

# ====================================================================
# TOP-LEVEL NAVIGATION TABS (4 POWER HUBS)
# ====================================================================
tab_matches, tab_slips, tab_pnl, tab_quant = st.tabs([
    "⚽ Live & Upcoming Matches",
    "🎯 Precision Bet Slips & Same-Game Parlays",
    "📊 Paper-Trading PnL & Ledger",
    "⚡ Quant Lab & Real-Time Steam Alerts"
])

# ####################################################################
# TAB 1: MATCHES (LIVE IN-PLAY + UPCOMING BY LEAGUE TIER)
# ####################################################################
with tab_matches:
    st.markdown("## 🔴 Live Matches on the Pitch")

    if not live_matches:
        st.info("No live matches currently in-play on the pitch.")
    else:
        live_by_comp: Dict[str, List[LiveMatch]] = {}
        for lm in live_matches:
            live_by_comp.setdefault(lm.competition, []).append(lm)

        sorted_live_leagues = sorted(live_by_comp.keys(), key=lambda c: classify_league(c)[0])

        for comp in sorted_live_leagues:
            matches = live_by_comp[comp]
            tier_rank, tier_label = classify_league(comp)
            is_expanded = expand_all or (tier_rank <= 10)

            with st.expander(f"🏆 {comp}  •  {len(matches)} In-Play Match{'es' if len(matches) > 1 else ''}", expanded=is_expanded):
                for m in matches:
                    home_logo = m.home_logo or get_club_logo_url(m.home_team)
                    away_logo = m.away_logo or get_club_logo_url(m.away_team)
                    home_logo_html = f'<img src="{home_logo}" class="team-crest" alt="crest"/>' if home_logo else '<div class="team-crest-fallback">⚽</div>'
                    away_logo_html = f'<img src="{away_logo}" class="team-crest" alt="crest"/>' if away_logo else '<div class="team-crest-fallback">⚽</div>'

                    st.markdown(f"""
                    <div class="broadcast-card">
                        <div class="card-header-league">
                            <svg viewBox="0 0 24 24" width="20" height="20" fill="#ff3344" style="vertical-align:middle; margin-right:6px;"><path d="M13 2L3 14h7v8l10-12h-7z"/></svg>
                            <span>{m.competition}</span>
                        </div>
                        <div class="card-subheader">
                            <span class="date-pill">📅 {datetime.now(timezone.utc).strftime('%a %d %b • %H:%M UTC')}</span>
                            <span>🏟️ {m.venue or 'Main Stadium'}</span>
                            <span>📺 Live Broadcast / Stake Stream</span>
                        </div>
                        <hr class="card-divider"/>
                        <div class="scoreboard-row">
                            <div class="team-home">
                                <span>{m.home_team}</span>
                                {home_logo_html}
                            </div>
                            <div class="center-score">
                                <div class="score-numbers">{m.home_score} - {m.away_score}</div>
                                <div class="score-clock">{m.current_minute}</div>
                            </div>
                            <div class="team-away">
                                {away_logo_html}
                                <span>{m.away_team}</span>
                            </div>
                        </div>
                        <div class="odds-bar">
                            <div class="odds-numbers">
                                <b>Stake Live Odds:</b> &nbsp;
                                Home: <span class="odds-val">{m.stake_odds['home']}</span> &nbsp;|&nbsp;
                                Draw: <span class="odds-val">{m.stake_odds['draw']}</span> &nbsp;|&nbsp;
                                Away: <span class="odds-val">{m.stake_odds['away']}</span>
                            </div>
                            <span class="badge-signal">IN-PLAY ON STAKE</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("## 📅 Upcoming European Matches on Stake")
    st.caption("Sorted strictly from best league to least. Click any league expander to collapse or reveal fixtures:")

    upcoming_by_comp: Dict[str, List[MatchOddsComparison]] = {}
    for um in upcoming_matches:
        upcoming_by_comp.setdefault(um.competition, []).append(um)

    sorted_upcoming_leagues = sorted(upcoming_by_comp.keys(), key=lambda c: classify_league(c)[0])

    for comp in sorted_upcoming_leagues:
        matches = upcoming_by_comp[comp]
        tier_rank, tier_label = classify_league(comp)
        is_open = expand_all or (tier_rank <= 3)

        with st.expander(f"🏆 {comp}  •  {len(matches)} Fixtures on Stake", expanded=is_open):
            for f in matches:
                shin_probs = devig_shin(f.pinnacle_odds)
                fair_home = round(1.0 / shin_probs["home"], 2)
                fair_draw = round(1.0 / shin_probs["draw"], 2)
                fair_away = round(1.0 / shin_probs["away"], 2)

                home_edge = (f.stake_odds["home"] / fair_home) - 1.0
                away_edge = (f.stake_odds["away"] / fair_away) - 1.0

                signal_badge = '<span style="color:#8c96a5; font-size:0.85em;">Balanced Market</span>'
                if home_edge >= 0.025:
                    signal_badge = f'<span class="badge-signal">🔥 +EV HOME VALUE (+{home_edge*100:.1f}%)</span>'
                elif away_edge >= 0.025:
                    signal_badge = f'<span class="badge-signal">🔥 +EV AWAY VALUE (+{away_edge*100:.1f}%)</span>'
                elif shin_probs["home"] >= 0.70:
                    signal_badge = '<span class="badge-signal" style="background:#142838; color:#63b3ed;">⭐ DOMINATING FAVORITE</span>'

                home_logo = get_club_logo_url(f.home_team)
                away_logo = get_club_logo_url(f.away_team)
                home_logo_html = f'<img src="{home_logo}" class="team-crest" alt="crest"/>' if home_logo else '<div class="team-crest-fallback">⚽</div>'
                away_logo_html = f'<img src="{away_logo}" class="team-crest" alt="crest"/>' if away_logo else '<div class="team-crest-fallback">⚽</div>'

                st.markdown(f"""
                <div class="broadcast-card">
                    <div class="card-header-league">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="#ff3344" style="vertical-align:middle; margin-right:6px;"><path d="M13 2L3 14h7v8l10-12h-7z"/></svg>
                        <span>{f.competition}</span>
                    </div>
                    <div class="card-subheader">
                        <span class="date-pill">📅 {f.kickoff_str}</span>
                        <span>🏟️ {f.venue or 'Home Stadium'}</span>
                        <span>📺 Live on Stake ({STAKE_MIRROR})</span>
                    </div>
                    <hr class="card-divider"/>
                    <div class="scoreboard-row">
                        <div class="team-home">
                            <span>{f.home_team}</span>
                            {home_logo_html}
                        </div>
                        <div class="center-score">
                            <div class="score-numbers" style="font-size:2.0em; color:#e2e8f0;">VS</div>
                            <div class="score-clock clock-upcoming">{f.kickoff_str}</div>
                        </div>
                        <div class="team-away">
                            {away_logo_html}
                            <span>{f.away_team}</span>
                        </div>
                    </div>
                    <div class="odds-bar">
                        <div class="odds-numbers">
                            <b>Stake Odds:</b> &nbsp;
                            Home: <span class="odds-val">{f.stake_odds['home']}</span> &nbsp;|&nbsp;
                            Draw: <span class="odds-val">{f.stake_odds['draw']}</span> &nbsp;|&nbsp;
                            Away: <span class="odds-val">{f.stake_odds['away']}</span>
                            &nbsp;&nbsp;<span style="color:#718096;">[Pinnacle Fair: {fair_home} / {fair_draw} / {fair_away}]</span>
                        </div>
                        {signal_badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ####################################################################
# TAB 2: PRECISION BET SLIPS & SAME-GAME PARLAYS (SGPs)
# ####################################################################
with tab_slips:
    st.markdown("## 🎯 Precision Bet Slips (Target: Stake `stake.ac`)")
    st.markdown(
        "Mathematically optimized accumulator slips. When 1X2 outright win is uncertain, the model dynamically hedges into "
        "**Draw No Bet (stake refunded on draw)**, **Double Chance (1X/X2)**, **Both Teams To Score (BTTS)**, and **Team Goals (Over 0.5)**."
    )

    # 1. DISPLAY CURATED STRATEGY SLIPS WITH RICH TICKET FORMAT
    for s in curated_slips:
        if "ULTRA-SAFE" in s.strategy_badge:
            border_color = "#00ff66"
            glow_class = "rgba(0, 255, 102, 0.4)"
        elif "UNCERTAINTY" in s.strategy_badge:
            border_color = "#c084fc"
            glow_class = "rgba(192, 132, 252, 0.4)"
        elif "MAXIMUM" in s.strategy_badge:
            border_color = "#f59e0b"
            glow_class = "rgba(245, 158, 11, 0.4)"
        else:
            border_color = "#38bdf8"
            glow_class = "rgba(56, 189, 248, 0.4)"
        
        st.markdown(f"""
        <div class="slip-container" style="border-color: {border_color}; box-shadow: 0 8px 30px {glow_class};">
            <div class="slip-header-row">
                <div>
                    <span class="badge-signal" style="background:#172033; color:{border_color}; border: 1px solid {border_color}; font-size:0.85em;">
                        {s.strategy_badge}
                    </span>
                    <h3 class="slip-title">{s.slip_name}</h3>
                    <p style="color:#8c96a5; font-size:0.92em; margin:4px 0 0 0;">{s.strategy_description}</p>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.8em; color:#8c96a5; text-transform:uppercase; font-weight:700;">Multiplied Odds</div>
                    <div class="slip-odds-multiplier" style="color:{border_color};">{s.combined_odds:.2f}x</div>
                    <div style="font-size:0.82em; color:#63b3ed; margin-top:2px; font-weight:700;">Target: Stake ({STAKE_MIRROR})</div>
                </div>
            </div>
            
            <div class="slip-metrics-grid">
                <div class="metric-cell">
                    <div class="label">Joint Win Prob</div>
                    <div class="val" style="color:#00ff66;">{s.combined_probability*100:.1f}%</div>
                </div>
                <div class="metric-cell">
                    <div class="label">Kelly Stake</div>
                    <div class="val">${s.suggested_stake_amount:.2f}</div>
                </div>
                <div class="metric-cell">
                    <div class="label">Potential Return</div>
                    <div class="val" style="color:{border_color};">${s.potential_payout:.2f}</div>
                </div>
                <div class="metric-cell">
                    <div class="label">Net Profit</div>
                    <div class="val" style="color:#ffffff;">+${s.net_profit_on_win:.2f}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # High-Fidelity Legs Ticket List
        for idx, leg in enumerate(s.legs, 1):
            h_team = getattr(leg, "home_team", "") or (leg.match_name.split(" vs ")[0] if " vs " in leg.match_name else "Home")
            a_team = getattr(leg, "away_team", "") or (leg.match_name.split(" vs ")[1] if " vs " in leg.match_name else "Away")
            k_date = getattr(leg, "kickoff_str", "Upcoming")

            home_logo = get_club_logo_url(h_team)
            away_logo = get_club_logo_url(a_team)
            home_logo_html = f'<img src="{home_logo}" class="leg-mini-crest" alt=""/>' if home_logo else '⚽'
            away_logo_html = f'<img src="{away_logo}" class="leg-mini-crest" alt=""/>' if away_logo else '⚽'

            # Market Badge Class
            if "Draw No Bet" in leg.market_type:
                tag_class = "market-tag market-tag-dnb"
            elif "Double Chance" in leg.market_type:
                tag_class = "market-tag market-tag-dc"
            elif "Both Teams" in leg.market_type:
                tag_class = "market-tag market-tag-btts"
            elif "Goal" in leg.market_type:
                tag_class = "market-tag market-tag-goal"
            else:
                tag_class = "market-tag market-tag-1x2"

            st.markdown(f"""
            <div class="leg-card">
                <div class="leg-header">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span class="leg-badge-num">LEG #{idx}</span>
                        <span style="color:#8c96a5; font-size:0.88em; font-weight:700;">{leg.competition}</span>
                    </div>
                    <span class="leg-date-pill">📅 {k_date}</span>
                </div>
                <div class="leg-matchup-row">
                    <div class="leg-teams">
                        {home_logo_html}
                        <span>{h_team}</span>
                        <span style="color:#64748b; font-size:0.85em; font-weight:600;">vs</span>
                        <span>{a_team}</span>
                        {away_logo_html}
                    </div>
                    <span class="{tag_class}">{leg.market_type}</span>
                </div>
                <div class="leg-footer">
                    <div>
                        <span style="color:#8c96a5; font-size:0.82em; text-transform:uppercase; margin-right:6px;">Pick:</span>
                        <b class="leg-pick-text">{leg.selection} @ {leg.odds:.2f}</b>
                        &nbsp;&nbsp;<span style="color:#64748b; font-size:0.85em;">|</span>&nbsp;&nbsp;
                        <span style="color:#94a3b8; font-size:0.85em;">🛡️ {leg.hedge_description}</span>
                    </div>
                    <div class="leg-prob-text">
                        Win Prob: <b style="color:#00ff66;">{leg.win_probability*100:.1f}%</b> ({leg.safety_rating})
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"📋 Copy Formatted Stake.ac Slip ({s.slip_name})"):
            st.code(s.copyable_text, language="text")

    st.divider()

    # 2. SAME-GAME PARLAY (SGP) CORRELATED COPULA BUILDER
    st.markdown("## ⚡ Correlated Same-Game Parlay (SGP) Copula Builder")
    st.caption("Combines multiple correlated events on the SAME MATCH (Match Winner + Over/Under + BTTS) using our exact analytical bivariate copula:")

    sgp_match_options = [
        f"{m.match_name} • 📅 {m.kickoff_str} ({m.competition})"
        for m in evaluated_secondary
    ]
    sgp_selected_name = st.selectbox("Select Match to Build Correlated Same-Game Parlay (SGP):", options=sgp_match_options, index=0)
    sgp_match_eval = next(m for m in evaluated_secondary if f"{m.match_name} • 📅 {m.kickoff_str} ({m.competition})" == sgp_selected_name)

    # Estimate goal intensities
    shin_match = devig_shin(m.pinnacle_odds if hasattr(m, 'pinnacle_odds') else m.stake_odds)
    p_h, p_a = shin_match.get("home", 0.5), shin_match.get("away", 0.25)
    ratio = (p_h / max(0.01, p_a)) ** 0.5
    mu_a = 2.75 / (1.0 + ratio)
    lambda_h = 2.75 - mu_a

    generated_sgps = build_same_game_parlays(
        match_id=sgp_match_eval.match_id,
        match_name=sgp_match_eval.match_name,
        competition=sgp_match_eval.competition,
        home_team=sgp_match_eval.home_team,
        away_team=sgp_match_eval.away_team,
        lambda_h=lambda_h,
        mu_a=mu_a,
        kickoff_str=sgp_match_eval.kickoff_str,
        bankroll=BANKROLL
    )

    sgp_cols = st.columns(len(generated_sgps))
    for i, sgp in enumerate(generated_sgps):
        with sgp_cols[i]:
            st.markdown(f"""
            <div class="slip-container" style="padding:18px; border-color:#06b6d4; height:100%;">
                <span class="badge-signal" style="background:#082f49; color:#38bdf8; border:1px solid #0284c7;">SGP COMBO</span>
                <h4 style="color:#ffffff; margin:8px 0 4px 0;">{sgp.combo_name}</h4>
                <p style="color:#94a3b8; font-size:0.85em; min-height:38px;">{sgp.narrative}</p>
                <div style="background:#0b1320; border-radius:8px; padding:10px; margin-bottom:12px; border:1px solid #1e293b;">
                    <div style="font-size:0.75em; color:#8c96a5; text-transform:uppercase;">Stake Multiplied Odds</div>
                    <div style="font-size:1.8em; font-weight:900; color:#38bdf8;">{sgp.stake_offered_odds:.2f}x</div>
                    <div style="font-size:0.8em; color:#00ff66;">Exact Joint Prob: <b>{sgp.exact_joint_probability*100:.1f}%</b></div>
                    <div style="font-size:0.75em; color:#64748b;">Naive Prob: {sgp.naive_independent_prob*100:.1f}% (Boost: {sgp.correlation_boost_pct:+0.1f}%)</div>
                </div>
                <div style="font-size:0.85em; margin-bottom:8px;">
                    <b>Legs:</b>
            """, unsafe_allow_html=True)
            for leg in sgp.legs:
                st.markdown(f"<div style='font-size:0.82em; color:#cbd5e1;'>• <b>{leg.market}:</b> {leg.selection}</div>", unsafe_allow_html=True)
            st.markdown(f"""
                <hr style='border-color:#1e293b; margin:10px 0;'/>
                <div style='font-size:0.85em; display:flex; justify-content:space-between;'>
                    <span>Rec. Stake: <b>${sgp.suggested_stake_amount:.2f}</b></span>
                    <span style='color:#00ff66;'>Return: <b>${sgp.potential_payout:.2f}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # 3. MATCH-BY-MATCH ALTERNATIVE MARKETS EXPLORER (WITH DATES)
    st.markdown("## 🔍 Match-by-Match Uncertainty & Alternative Markets Explorer")
    st.caption("Inspect secondary bets (Draw No Bet, Double Chance, BTTS, Over/Under) with match dates when 1X2 outright win is uncertain:")

    # Match Selector Dropdown showing Date & Teams
    match_options = [
        f"{m.match_name} • 📅 {m.kickoff_str} ({m.competition})"
        for m in evaluated_secondary
    ]
    selected_name = st.selectbox("Select Fixture to Inspect Secondary Markets:", options=match_options, index=0)

    selected_eval = next(
        m for m in evaluated_secondary
        if f"{m.match_name} • 📅 {m.kickoff_str} ({m.competition})" == selected_name
    )

    # Uncertainty Badge Banner with Date
    home_logo = get_club_logo_url(selected_eval.home_team)
    away_logo = get_club_logo_url(selected_eval.away_team)
    home_logo_html = f'<img src="{home_logo}" class="leg-mini-crest" alt=""/>' if home_logo else '⚽'
    away_logo_html = f'<img src="{away_logo}" class="leg-mini-crest" alt=""/>' if away_logo else '⚽'

    st.markdown(f"""
    <div style="background:#131722; border:1px solid #242c3d; border-radius:10px; padding:16px 20px; margin-bottom:18px; display:flex; justify-content:space-between; align-items:center;">
        <div style="display:flex; align-items:center; gap:14px;">
            {home_logo_html}
            <span style="font-size:1.3em; font-weight:800; color:#ffffff;">{selected_eval.home_team}</span>
            <span style="color:#64748b; font-size:1.1em; font-weight:700;">vs</span>
            <span style="font-size:1.3em; font-weight:800; color:#ffffff;">{selected_eval.away_team}</span>
            {away_logo_html}
        </div>
        <div style="display:flex; gap:12px; align-items:center;">
            <span class="leg-date-pill" style="font-size:0.95em; padding:5px 12px;">📅 {selected_eval.kickoff_str}</span>
            <span style="color:#8c96a5; font-size:0.9em;">🏟️ {selected_eval.venue or 'Home Stadium'}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if selected_eval.is_uncertain_1x2:
        st.warning(
            f"⚠️ **1X2 Outright Uncertain:** Neither {selected_eval.home_team} nor {selected_eval.away_team} has a >=60% outright win probability. "
            f"The engine recommends hedging into **{selected_eval.best_safety_pick.label}** ({selected_eval.best_safety_pick.win_probability*100:.1f}% win prob) to eliminate draw risk."
        )
    else:
        st.success(
            f"⭐ **Dominating Favorite Detected:** Recommended Safety Pick: **{selected_eval.best_safety_pick.label}** "
            f"({selected_eval.best_safety_pick.win_probability*100:.1f}% win prob @ {selected_eval.best_safety_pick.odds:.2f})."
        )

    # Grid of Available Alternative Markets
    cols = st.columns(3)
    for i, mk in enumerate(selected_eval.markets):
        with cols[i % 3]:
            hedge_tag = '<span style="color:#d6bcfa; font-size:0.75em; font-weight:700;">[DRAW HEDGE]</span>' if mk.uncertainty_hedge else ''
            st.markdown(f"""
            <div class="market-box">
                <div class="market-box-title">{mk.market_type} {hedge_tag}</div>
                <div class="market-box-pick">{mk.selection}</div>
                <div class="market-box-odds">{mk.odds:.2f}</div>
                <div style="font-size:0.85em; color:#a0aec0; margin-top:4px;">
                    Win Prob: <b style="color:#ffffff;">{mk.win_probability*100:.1f}%</b>
                </div>
                <div style="font-size:0.78em; color:#8c96a5; margin-top:2px;">
                    Safety: <b style="color:#00ff66;">{mk.safety_rating}</b> | Fair: {mk.fair_odds:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ####################################################################
# TAB 3: PAPER-TRADING LIVE PNL & SIMULATION LEDGER
# ####################################################################
with tab_pnl:
    st.markdown("## 📊 Paper-Trading Live PnL & Settlement Ledger")
    st.caption("Live simulation tracking hypothetical returns on all model recommendations (Singles, Accas, SGPs) with fractional Kelly staking on Stake.")

    # High-Impact Financial Overview Grid
    pnl_color = "#00ff66" if paper_summary["total_pnl"] >= 0 else "#ef4444"
    st.markdown(f"""
    <div class="slip-metrics-grid" style="grid-template-columns: repeat(4, 1fr); background:#0c0f17; border: 2px solid #232d42; padding:18px 24px; margin-bottom:24px;">
        <div class="metric-cell">
            <div class="label">Total Capital Staked</div>
            <div class="val" style="color:#ffffff;">${paper_summary['total_staked']:,.2f}</div>
        </div>
        <div class="metric-cell">
            <div class="label">Total Active Bets</div>
            <div class="val" style="color:#63b3ed;">{paper_summary['total_bets']} Bets</div>
        </div>
        <div class="metric-cell">
            <div class="label">Running Portfolio PnL</div>
            <div class="val" style="color:{pnl_color}; text-shadow:0 0 12px rgba(0,255,102,0.4);">${paper_summary['total_pnl']:+,.2f}</div>
        </div>
        <div class="metric-cell">
            <div class="label">Overall Portfolio ROI</div>
            <div class="val" style="color:{pnl_color};">{paper_summary['roi_pct']:+.2f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sub-tabs for granular category tracking
    sub_live, sub_singles, sub_accas, sub_sgps, sub_report = st.tabs([
        f"🔴 Live In-Play Bets ({len(paper_live_bets)})",
        f"📅 Upcoming Singles ({len(paper_singles)})",
        f"🎯 Multi-Bet Accas ({len(paper_accas)})",
        f"⚡ Same-Game Parlays ({len(paper_sgps)})",
        "📄 Full Structured Markdown Ledger"
    ])

    with sub_live:
        st.markdown("### 🔴 Real-Time In-Play Performance")
        st.caption("Positions actively running on live matches. PnL reflects current live score and match minute:")
        for b in paper_live_bets:
            pnl_c = "#00ff66" if b.unrealized_or_realized_pnl > 0 else ("#a0aec0" if b.unrealized_or_realized_pnl == 0 else "#ef4444")
            st.markdown(f"""
            <div class="leg-card" style="margin-bottom:10px;">
                <div class="leg-header">
                    <div>
                        <span class="leg-badge-num">{b.competition}</span> &nbsp;
                        <b style="color:#ffffff; font-size:1.1em;">{b.match_name}</b>
                    </div>
                    <span class="leg-date-pill" style="background:#2b1212; color:#f87171; border-color:#5c2222;">
                        🔴 {b.current_match_state}
                    </span>
                </div>
                <div class="leg-footer" style="margin-top:8px;">
                    <div>
                        Pick: <b class="leg-pick-text">{b.selection} @ {b.stake_odds:.2f}</b> &nbsp;|&nbsp;
                        Stake: <b>${b.stake_amount:.2f}</b> &nbsp;|&nbsp;
                        <span style="color:#8c96a5;">{b.notes}</span>
                    </div>
                    <div style="font-size:1.05em; font-weight:800; color:{pnl_c};">
                        PnL: ${b.unrealized_or_realized_pnl:+.2f} &nbsp;<span style="font-size:0.8em; color:#8c96a5;">({b.settlement_status})</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with sub_singles:
        st.markdown("### 📅 Upcoming Value Singles & Hedges")
        st.caption("Simulated fractional Kelly bets on top upcoming European fixtures:")
        single_data = []
        for s in paper_singles:
            single_data.append({
                "Match": s.match_name,
                "Kickoff Date": s.kickoff_str,
                "League": s.competition,
                "Market": s.market_type,
                "Pick & Odds": f"{s.selection} @ {s.stake_odds:.2f}",
                "Win Prob": f"{s.model_probability*100:.1f}%",
                "Stake": f"${s.stake_amount:.2f}",
                "Potential Profit": f"+${s.potential_profit:.2f}",
                "Status": s.settlement_status
            })
        st.dataframe(pd.DataFrame(single_data), use_container_width=True)

    with sub_accas:
        st.markdown("### 🎯 Curated Multi-Bet Accas (Cross-League Parlays)")
        for a in paper_accas:
            st.markdown(f"""
            <div class="slip-container" style="padding:16px 20px; margin-bottom:14px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <h4 style="color:#ffffff; margin:0;">{a.match_name}</h4>
                        <p style="color:#8c96a5; font-size:0.88em; margin:2px 0 0 0;">{a.notes}</p>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:1.6em; font-weight:900; color:#00ff66;">{a.stake_odds:.2f}x</span>
                    </div>
                </div>
                <div class="leg-footer" style="margin-top:10px;">
                    <div>Picks: <b style="color:#cbd5e1;">{a.selection}</b></div>
                    <div>Stake: <b>${a.stake_amount:.2f}</b> &nbsp;|&nbsp; Potential Return: <b style="color:#00ff66;">${a.potential_payout:.2f}</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with sub_sgps:
        st.markdown("### ⚡ Correlated Same-Game Parlays (SGPs)")
        sgp_data = []
        for p in paper_sgps:
            sgp_data.append({
                "Fixture": p.match_name,
                "Kickoff Date": p.kickoff_str,
                "SGP Combo": p.selection.split(":")[0],
                "Selections": p.selection.split(":")[1] if ":" in p.selection else p.selection,
                "Multiplied Odds": f"{p.stake_odds:.2f}x",
                "Joint Win Prob": f"{p.model_probability*100:.1f}%",
                "Stake": f"${p.stake_amount:.2f}",
                "Potential Return": f"${p.potential_payout:.2f}"
            })
        st.dataframe(pd.DataFrame(sgp_data), use_container_width=True)

    with sub_report:
        st.markdown("### 📄 Full Structured Markdown Ledger & Training Report")
        st.caption("Auto-generated structured documentation tracking every position and model learning delta:")
        report_path = "LIVE_AND_UPCOMING_PAPER_TRADING_PNL_LEDGER.md"
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                report_text = f.read()
            st.download_button(
                label="📥 Download Full Markdown Ledger Report",
                data=report_text,
                file_name="LIVE_AND_UPCOMING_PAPER_TRADING_PNL_LEDGER.md",
                mime="text/markdown"
            )
            st.markdown(report_text)


# ####################################################################
# TAB 4: QUANT LAB & REAL-TIME STEAM MONITOR
# ####################################################################
with tab_quant:
    st.markdown("## ⚡ Quant Lab: Real-Time Steam Monitor & Advanced Models")
    st.caption("Continuously tracking Pinnacle line velocity, Stake execution lag, continuous xG ratings, and dynamic Kalman momentum.")

    # 1. STEAM ARBITRAGE ALERTS
    st.markdown("### 🔥 Real-Time Pinnacle-Stake Execution Lag Alerts")
    if not steam_events:
        st.info("No significant latency discrepancies detected between Pinnacle and Stake right now.")
    else:
        st.caption(f"Found {len(steam_events)} active line latency window(s) where Stake odds lag behind Pinnacle sharp movement:")
        for ev in steam_events:
            color = "#ef4444" if ev.urgency_level == "CRITICAL" else ("#f59e0b" if ev.urgency_level == "HIGH" else "#38bdf8")
            st.markdown(f"""
            <div class="steam-banner" style="border-color:{color};">
                <div>
                    <span style="background:{color}; color:#000000; font-weight:900; font-size:0.78em; padding:2px 8px; border-radius:4px; text-transform:uppercase;">
                        {ev.urgency_level} • WINDOW ~{ev.estimated_window_seconds}s
                    </span> &nbsp;
                    <b style="color:#ffffff; font-size:1.1em;">{ev.match_name}</b> &nbsp;
                    <span style="color:#8c96a5; font-size:0.9em;">({ev.competition} • 📅 {ev.kickoff_str})</span>
                    <div style="margin-top:4px; font-size:0.9em; color:#cbd5e1;">
                        Pick: <b style="color:#00ff66; font-size:1.05em;">{ev.team_selected} ({ev.selection}) @ {ev.stake_current_odds:.2f}</b> on Stake &nbsp;|&nbsp; 
                        Pinnacle Fair: <b>{ev.pinnacle_fair_odds:.2f}</b> (Sharp Line: {ev.pinnacle_current_odds:.2f})
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.8em; color:#8c96a5; text-transform:uppercase;">Latency Edge</div>
                    <div style="font-size:1.5em; font-weight:900; color:#00ff66;">+{ev.lag_edge_pct:.1f}%</div>
                    <div style="font-size:0.78em; color:#a0aec0;">Detected: {ev.detection_time_utc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # 2. XG CALIBRATED DIXON-COLES & KALMAN RATINGS
    st.markdown("### 🧠 Continuous Shot-Quality xG & Online Kalman Momentum Ratings")
    st.caption("Variance-reduced team ratings calibrated across 1,752 Big 5 matches without discrete scoreline noise:")

    if QUANT_RATINGS and "teams" in QUANT_RATINGS:
        q_teams = QUANT_RATINGS["teams"]
        col_att, col_def, col_mom = st.columns(3)

        # Top 5 Attack by xG
        with col_att:
            st.markdown("#### ⚡ Top 5 Attack Power (xG)")
            sorted_att = sorted(q_teams.items(), key=lambda x: x[1]["xg_attack"], reverse=True)[:5]
            for rank, (team, vals) in enumerate(sorted_att, 1):
                logo = get_club_logo_url(team)
                logo_html = f'<img src="{logo}" style="width:24px; height:24px; object-fit:contain;" alt=""/>' if logo else '⚽'
                st.markdown(f"""
                <div style="background:#131722; border:1px solid #242c3d; border-radius:10px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="color:#64748b; font-weight:800; font-size:0.85em;">#{rank}</span>
                        {logo_html}
                        <b style="color:#ffffff; font-size:0.98em;">{team}</b>
                    </div>
                    <span style="color:#00ff66; font-weight:900; font-family:monospace; font-size:1.05em;">{vals['xg_attack']:+.3f}</span>
                </div>
                """, unsafe_allow_html=True)

        # Top 5 Defense (Lowest Vulnerability)
        with col_def:
            st.markdown("#### 🛡️ Top 5 Defense Solidity (Low xG Conceded)")
            sorted_def = sorted(q_teams.items(), key=lambda x: x[1]["xg_defense"])[:5]
            for rank, (team, vals) in enumerate(sorted_def, 1):
                logo = get_club_logo_url(team)
                logo_html = f'<img src="{logo}" style="width:24px; height:24px; object-fit:contain;" alt=""/>' if logo else '⚽'
                st.markdown(f"""
                <div style="background:#131722; border:1px solid #242c3d; border-radius:10px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="color:#64748b; font-weight:800; font-size:0.85em;">#{rank}</span>
                        {logo_html}
                        <b style="color:#ffffff; font-size:0.98em;">{team}</b>
                    </div>
                    <span style="color:#38bdf8; font-weight:900; font-family:monospace; font-size:1.05em;">{vals['xg_defense']:+.3f}</span>
                </div>
                """, unsafe_allow_html=True)

        # Top 5 Kalman Form Momentum (Surging Teams)
        with col_mom:
            st.markdown("#### 📈 Top 5 Surging Teams (Kalman Momentum)")
            sorted_mom = sorted(q_teams.items(), key=lambda x: x[1]["form_momentum"], reverse=True)[:5]
            for rank, (team, vals) in enumerate(sorted_mom, 1):
                logo = get_club_logo_url(team)
                logo_html = f'<img src="{logo}" style="width:24px; height:24px; object-fit:contain;" alt=""/>' if logo else '⚽'
                st.markdown(f"""
                <div style="background:#131722; border:1px solid #242c3d; border-radius:10px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="color:#64748b; font-weight:800; font-size:0.85em;">#{rank}</span>
                        {logo_html}
                        <b style="color:#ffffff; font-size:0.98em;">{team}</b>
                    </div>
                    <span style="color:#c084fc; font-weight:900; font-family:monospace; font-size:1.05em;">+{vals['form_momentum']:.3f}</span>
                </div>
                """, unsafe_allow_html=True)

st.markdown("---")
st.caption("🛡️ Autonomous Zero-Input Multi-Bet Agent running continuously targeting Stake (`stake.ac`).")
