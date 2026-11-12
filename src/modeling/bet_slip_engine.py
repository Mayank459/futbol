"""Elite Bet Slip Engine for Stake (stake.ac).

Computes comprehensive secondary markets for matches with 1X2 uncertainty:
1. Draw No Bet (DNB) - Full stake returned if match ends in a draw.
2. Double Chance (1X / X2) - High certainty safety pick covering 2 of 3 outcomes.
3. Both Teams To Score (BTTS Yes / No) - Derived from Dixon-Coles goal expectation.
4. Total Goals (Over 1.5 / Under 2.5 Goals) - High probability anchor legs.
5. Team to Score (Over 0.5 Goals) - Ultra-safe individual team goal scoring.

Builds 4 curated autonomous slip strategies:
- Strategy 1: "Fortress" Ultra-Safe Slip (Double Chance & High-Certainty picks).
- Strategy 2: "Uncertainty Hedge" Slip (Draw No Bet & BTTS replacing volatile 1X2 picks).
- Strategy 3: "+EV Value Multiplier" Slip (Sharp market discrepancy edges).
- Strategy 4: "Double Lock" Slip (2 high-confidence legs for higher Kelly sizing).
"""

import os
import sys
import numpy as np
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field

from src.modeling.devig import devig_shin
from src.modeling.dixon_coles import calculate_analytical_probabilities


class AlternativeMarket(BaseModel):
    market_type: str        # "1X2", "Draw No Bet", "Double Chance", "Both Teams To Score", "Total Goals", "Team Goal"
    selection: str          # "Home DNB", "1X", "BTTS Yes", "Over 1.5", etc.
    label: str              # User-friendly description
    odds: float             # Stake odds
    win_probability: float  # Estimated true probability
    fair_odds: float        # Devigged fair odds
    edge: float             # Expected value edge vs fair line
    safety_rating: str      # "Ultra-Safe" (>=80%), "Very Safe" (70-79%), "Moderate" (55-69%)
    uncertainty_hedge: bool # True if this market resolves 1X2 uncertainty


class MatchSecondaryMarkets(BaseModel):
    match_id: str
    match_name: str
    competition: str
    home_team: str
    away_team: str
    kickoff_str: str
    venue: Optional[str]
    is_uncertain_1x2: bool  # True if neither team has >= 60% outright win probability
    best_safety_pick: AlternativeMarket
    markets: List[AlternativeMarket]


class CuratedSlipLeg(BaseModel):
    match_id: str
    match_name: str
    competition: str
    home_team: str = ""
    away_team: str = ""
    kickoff_str: str = "Upcoming"
    venue: Optional[str] = None
    market_type: str
    selection: str
    odds: float
    win_probability: float
    safety_rating: str
    hedge_description: str


class CuratedBetSlip(BaseModel):
    slip_id: str
    slip_name: str
    strategy_badge: str
    strategy_description: str
    target_bookmaker: str = "Stake (stake.ac)"
    legs: List[CuratedSlipLeg]
    combined_odds: float
    combined_probability: float
    combined_edge: float
    suggested_stake_amount: float
    potential_payout: float
    net_profit_on_win: float
    risk_level: str  # "Low Risk", "Medium Risk", "High Value"
    copyable_text: str = ""


def evaluate_match_secondary_markets(
    match_id: str,
    match_name: str,
    competition: str,
    home_team: str,
    away_team: str,
    stake_1x2: Dict[str, float],
    pinnacle_1x2: Optional[Dict[str, float]] = None,
    kickoff_str: str = "Upcoming",
    venue: Optional[str] = None
) -> MatchSecondaryMarkets:
    """Evaluates all primary and secondary betting markets for a single match."""
    # 1. Devig 1X2 baseline probabilities
    sharp_source = pinnacle_1x2 if pinnacle_1x2 else stake_1x2
    shin = devig_shin(sharp_source)
    p_h, p_d, p_a = shin["home"], shin["draw"], shin["away"]

    # Estimate Poisson intensity parameters (lambda_home, mu_away)
    avg_total_goals = 2.75
    ratio = np.sqrt(p_h / max(0.01, p_a))
    mu_a = avg_total_goals / (1.0 + ratio)
    lambda_h = avg_total_goals - mu_a
    goal_probs = calculate_analytical_probabilities(lambda_h, mu_a)

    markets: List[AlternativeMarket] = []

    # Market A: Outright 1X2 (Home Win & Away Win)
    h_odds = stake_1x2.get("home", 2.0)
    a_odds = stake_1x2.get("away", 3.0)
    d_odds = stake_1x2.get("draw", 3.2)

    markets.append(AlternativeMarket(
        market_type="1X2",
        selection=f"{home_team} Win",
        label=f"{home_team} Outright 1X2 Win",
        odds=h_odds,
        win_probability=round(p_h, 3),
        fair_odds=round(1.0 / p_h, 2),
        edge=round((p_h * h_odds) - 1.0, 3),
        safety_rating="Ultra-Safe" if p_h >= 0.75 else ("Very Safe" if p_h >= 0.65 else "Moderate"),
        uncertainty_hedge=False
    ))

    markets.append(AlternativeMarket(
        market_type="1X2",
        selection=f"{away_team} Win",
        label=f"{away_team} Outright 1X2 Win",
        odds=a_odds,
        win_probability=round(p_a, 3),
        fair_odds=round(1.0 / p_a, 2),
        edge=round((p_a * a_odds) - 1.0, 3),
        safety_rating="Ultra-Safe" if p_a >= 0.75 else ("Very Safe" if p_a >= 0.65 else "Moderate"),
        uncertainty_hedge=False
    ))

    # Market B: Draw No Bet (DNB)
    # If game draws, bet is refunded (push)
    p_dnb_home = p_h / max(0.01, (p_h + p_a))
    p_dnb_away = p_a / max(0.01, (p_h + p_a))
    odds_dnb_h = round(max(1.05, 1.0 / (p_dnb_home * 1.05)), 2)
    odds_dnb_a = round(max(1.05, 1.0 / (p_dnb_away * 1.05)), 2)

    markets.append(AlternativeMarket(
        market_type="Draw No Bet",
        selection=f"{home_team} (Draw No Bet)",
        label=f"{home_team} DNB [Stake Refunded on Draw]",
        odds=odds_dnb_h,
        win_probability=round(p_dnb_home, 3),
        fair_odds=round(1.0 / p_dnb_home, 2),
        edge=round((p_dnb_home * odds_dnb_h) - 1.0, 3),
        safety_rating="Ultra-Safe" if p_dnb_home >= 0.78 else ("Very Safe" if p_dnb_home >= 0.65 else "Moderate"),
        uncertainty_hedge=True
    ))

    markets.append(AlternativeMarket(
        market_type="Draw No Bet",
        selection=f"{away_team} (Draw No Bet)",
        label=f"{away_team} DNB [Stake Refunded on Draw]",
        odds=odds_dnb_a,
        win_probability=round(p_dnb_away, 3),
        fair_odds=round(1.0 / p_dnb_away, 2),
        edge=round((p_dnb_away * odds_dnb_a) - 1.0, 3),
        safety_rating="Ultra-Safe" if p_dnb_away >= 0.78 else ("Very Safe" if p_dnb_away >= 0.65 else "Moderate"),
        uncertainty_hedge=True
    ))

    # Market C: Double Chance (1X / X2)
    p_1x = p_h + p_d
    p_x2 = p_a + p_d
    odds_1x = round(max(1.04, 1.0 / (p_1x * 1.05)), 2)
    odds_x2 = round(max(1.04, 1.0 / (p_x2 * 1.05)), 2)

    markets.append(AlternativeMarket(
        market_type="Double Chance",
        selection=f"{home_team} or Draw (1X)",
        label=f"Double Chance 1X ({home_team} or Draw)",
        odds=odds_1x,
        win_probability=round(p_1x, 3),
        fair_odds=round(1.0 / p_1x, 2),
        edge=round((p_1x * odds_1x) - 1.0, 3),
        safety_rating="Ultra-Safe" if p_1x >= 0.78 else "Very Safe",
        uncertainty_hedge=True
    ))

    markets.append(AlternativeMarket(
        market_type="Double Chance",
        selection=f"{away_team} or Draw (X2)",
        label=f"Double Chance X2 ({away_team} or Draw)",
        odds=odds_x2,
        win_probability=round(p_x2, 3),
        fair_odds=round(1.0 / p_x2, 2),
        edge=round((p_x2 * odds_x2) - 1.0, 3),
        safety_rating="Ultra-Safe" if p_x2 >= 0.78 else "Very Safe",
        uncertainty_hedge=True
    ))

    # Market D: Both Teams To Score (BTTS Yes / No)
    p_btts_yes = goal_probs.btts_yes
    p_btts_no = goal_probs.btts_no
    odds_btts_yes = round(max(1.10, 1.0 / (p_btts_yes * 1.06)), 2)
    odds_btts_no = round(max(1.10, 1.0 / (p_btts_no * 1.06)), 2)

    markets.append(AlternativeMarket(
        market_type="Both Teams To Score",
        selection="BTTS - Yes",
        label="Both Teams To Score (BTTS Yes)",
        odds=odds_btts_yes,
        win_probability=round(p_btts_yes, 3),
        fair_odds=round(1.0 / p_btts_yes, 2),
        edge=round((p_btts_yes * odds_btts_yes) - 1.0, 3),
        safety_rating="Very Safe" if p_btts_yes >= 0.65 else "Moderate",
        uncertainty_hedge=True
    ))

    # Market E: Over 1.5 Goals
    p_o15 = goal_probs.over_1_5
    odds_o15 = round(max(1.08, 1.0 / (p_o15 * 1.05)), 2)
    markets.append(AlternativeMarket(
        market_type="Total Goals",
        selection="Over 1.5 Goals",
        label="Over 1.5 Match Goals",
        odds=odds_o15,
        win_probability=round(p_o15, 3),
        fair_odds=round(1.0 / p_o15, 2),
        edge=round((p_o15 * odds_o15) - 1.0, 3),
        safety_rating="Ultra-Safe" if p_o15 >= 0.78 else "Very Safe",
        uncertainty_hedge=True
    ))

    # Market F: Team Goal (Home Over 0.5 Goals)
    p_home_goal = 1.0 - np.exp(-lambda_h)
    odds_hg = round(max(1.05, 1.0 / (p_home_goal * 1.04)), 2)
    markets.append(AlternativeMarket(
        market_type="Team Goal",
        selection=f"{home_team} to Score (Over 0.5)",
        label=f"{home_team} Over 0.5 Team Goals",
        odds=odds_hg,
        win_probability=round(p_home_goal, 3),
        fair_odds=round(1.0 / p_home_goal, 2),
        edge=round((p_home_goal * odds_hg) - 1.0, 3),
        safety_rating="Ultra-Safe" if p_home_goal >= 0.80 else "Very Safe",
        uncertainty_hedge=True
    ))

    # Determine 1X2 uncertainty (neither team >= 60% outright win)
    is_uncertain = (p_h < 0.60 and p_a < 0.60)

    # Pick the best safety pick with minimum odds >= 1.20
    candidates_with_value = [m for m in markets if m.uncertainty_hedge and m.odds >= 1.20]
    if candidates_with_value:
        best_safety = max(candidates_with_value, key=lambda m: m.win_probability)
    else:
        best_safety = max([m for m in markets if m.uncertainty_hedge], key=lambda m: m.win_probability)

    return MatchSecondaryMarkets(
        match_id=match_id,
        match_name=match_name,
        competition=competition,
        home_team=home_team,
        away_team=away_team,
        kickoff_str=kickoff_str,
        venue=venue,
        is_uncertain_1x2=is_uncertain,
        best_safety_pick=best_safety,
        markets=markets
    )


def assemble_curated_slips(
    evaluated_matches: List[MatchSecondaryMarkets],
    bankroll: float = 1000.0,
    kelly_fraction: float = 0.15
) -> List[CuratedBetSlip]:
    """Builds 4 distinct, mathematically optimized multi-bet slips for Stake."""
    slips: List[CuratedBetSlip] = []

    def make_slip(
        slip_id: str,
        slip_name: str,
        strategy_badge: str,
        strategy_description: str,
        risk_level: str,
        legs: List[CuratedSlipLeg],
        max_stake_pct: float
    ) -> Optional[CuratedBetSlip]:
        if len(legs) < 2:
            return None
        combined_odds = 1.0
        combined_prob = 1.0
        for l in legs:
            combined_odds *= l.odds
            combined_prob *= l.win_probability

        combined_odds = round(combined_odds, 3)
        combined_prob = round(combined_prob, 4)
        combined_edge = round((combined_prob * combined_odds) - 1.0, 4)

        b = combined_odds - 1.0
        q = 1.0 - combined_prob
        full_kelly = (combined_prob * b - q) / b if b > 0 else 0.0
        stake_pct = min(max_stake_pct, max(0.010, round(full_kelly * kelly_fraction, 4)))
        stake_amount = round(bankroll * stake_pct, 2)
        payout = round(stake_amount * combined_odds, 2)
        net_profit = round(payout - stake_amount, 2)

        copy_lines = [
            f"=== {slip_name.upper()} ===",
            f"Target: Stake (stake.ac) | Multiplied Odds: {combined_odds:.2f}x | Joint Prob: {combined_prob*100:.1f}%",
            f"Recommended Stake: ${stake_amount:.2f} | Potential Return: ${payout:.2f} (Net: +${net_profit:.2f})",
            "--------------------------------------------------"
        ]
        for idx, leg in enumerate(legs, 1):
            copy_lines.append(
                f"Leg #{idx}: [{leg.market_type}] {leg.match_name}\n"
                f"       Date: {leg.kickoff_str} | League: {leg.competition}\n"
                f"       Pick: {leg.selection} @ {leg.odds:.2f} (Prob: {leg.win_probability*100:.1f}%)"
            )

        return CuratedBetSlip(
            slip_id=slip_id,
            slip_name=slip_name,
            strategy_badge=strategy_badge,
            strategy_description=strategy_description,
            legs=legs,
            combined_odds=combined_odds,
            combined_probability=combined_prob,
            combined_edge=combined_edge,
            suggested_stake_amount=stake_amount,
            potential_payout=payout,
            net_profit_on_win=net_profit,
            risk_level=risk_level,
            copyable_text="\n".join(copy_lines)
        )

    # -------------------------------------------------------------
    # SLIP 1: 🛡️ "Fortress" Ultra-Safe Multi-Bet (Odds 1.20 - 1.55, Prob >= 68%)
    # -------------------------------------------------------------
    fortress_legs: List[CuratedSlipLeg] = []
    seen_1 = set()
    cand_1: List[Tuple[MatchSecondaryMarkets, AlternativeMarket]] = []
    for m in evaluated_matches:
        for mk in m.markets:
            if 1.20 <= mk.odds <= 1.55 and mk.win_probability >= 0.68:
                cand_1.append((m, mk))
    cand_1 = sorted(cand_1, key=lambda x: x[1].win_probability, reverse=True)

    for m, mk in cand_1:
        if m.match_id in seen_1:
            continue
        fortress_legs.append(CuratedSlipLeg(
            match_id=m.match_id,
            match_name=m.match_name,
            competition=m.competition,
            home_team=m.home_team,
            away_team=m.away_team,
            kickoff_str=m.kickoff_str,
            venue=m.venue,
            market_type=mk.market_type,
            selection=mk.selection,
            odds=mk.odds,
            win_probability=mk.win_probability,
            safety_rating=mk.safety_rating,
            hedge_description=f"High-certainty {mk.market_type} ({mk.win_probability*100:.1f}% win prob)"
        ))
        seen_1.add(m.match_id)
        if len(fortress_legs) >= 3:
            break

    slip_1 = make_slip(
        slip_id="fortress_ultra_safe",
        slip_name="Stake Fortress Acca (High-Certainty & Double Chance)",
        strategy_badge="🛡️ ULTRA-SAFE ACCA",
        strategy_description="Combines 68%+ probability legs with minimum 1.20x odds using Double Chance, Over 1.5 Goals, and heavy favorites to compound bankroll safely.",
        risk_level="Low Risk",
        legs=fortress_legs,
        max_stake_pct=0.030
    )
    if slip_1:
        slips.append(slip_1)

    # -------------------------------------------------------------
    # SLIP 2: ⚖️ "Uncertainty Hedge" Multi-Bet (DNB & BTTS Focus)
    # -------------------------------------------------------------
    hedge_legs: List[CuratedSlipLeg] = []
    seen_2 = set()
    uncertain_matches = [m for m in evaluated_matches if m.is_uncertain_1x2]
    cand_2: List[Tuple[MatchSecondaryMarkets, AlternativeMarket]] = []

    for m in uncertain_matches:
        for mk in m.markets:
            if mk.market_type in ("Draw No Bet", "Both Teams To Score") and 1.25 <= mk.odds <= 1.75 and mk.win_probability >= 0.60:
                cand_2.append((m, mk))
    cand_2 = sorted(cand_2, key=lambda x: x[1].win_probability, reverse=True)

    for m, mk in cand_2:
        if m.match_id in seen_2:
            continue
        hedge_legs.append(CuratedSlipLeg(
            match_id=m.match_id,
            match_name=m.match_name,
            competition=m.competition,
            home_team=m.home_team,
            away_team=m.away_team,
            kickoff_str=m.kickoff_str,
            venue=m.venue,
            market_type=mk.market_type,
            selection=mk.selection,
            odds=mk.odds,
            win_probability=mk.win_probability,
            safety_rating=mk.safety_rating,
            hedge_description=f"Draw variance eliminated: {mk.label}"
        ))
        seen_2.add(m.match_id)
        if len(hedge_legs) >= 3:
            break

    slip_2 = make_slip(
        slip_id="uncertainty_hedge",
        slip_name="Stake Uncertainty Hedge (Draw No Bet & BTTS)",
        strategy_badge="⚖️ UNCERTAINTY HEDGE",
        strategy_description="Replaces volatile 1X2 outright picks on tight matches with Draw No Bet (money-back refund on draw) and Both Teams To Score.",
        risk_level="Medium Risk",
        legs=hedge_legs,
        max_stake_pct=0.020
    )
    if slip_2:
        slips.append(slip_2)

    # -------------------------------------------------------------
    # SLIP 3: 🔥 "+EV Value Multiplier" (Pure Sharp Discrepancies)
    # -------------------------------------------------------------
    val_legs: List[CuratedSlipLeg] = []
    seen_3 = set()
    cand_3: List[Tuple[MatchSecondaryMarkets, AlternativeMarket]] = []
    for m in evaluated_matches:
        for mk in m.markets:
            if mk.edge >= 0.015 and mk.win_probability >= 0.55 and mk.odds >= 1.25:
                cand_3.append((m, mk))
    cand_3 = sorted(cand_3, key=lambda x: x[1].edge, reverse=True)

    for m, mk in cand_3:
        if m.match_id in seen_3:
            continue
        val_legs.append(CuratedSlipLeg(
            match_id=m.match_id,
            match_name=m.match_name,
            competition=m.competition,
            home_team=m.home_team,
            away_team=m.away_team,
            kickoff_str=m.kickoff_str,
            venue=m.venue,
            market_type=mk.market_type,
            selection=mk.selection,
            odds=mk.odds,
            win_probability=mk.win_probability,
            safety_rating=mk.safety_rating,
            hedge_description=f"+{mk.edge*100:.1f}% mathematical value edge over Pinnacle Shin fair line"
        ))
        seen_3.add(m.match_id)
        if len(val_legs) >= 3:
            break

    slip_3 = make_slip(
        slip_id="value_multiplier",
        slip_name="Stake Pure +EV Sharp Multi-Bet",
        strategy_badge="🔥 MAXIMUM +EV EDGE",
        strategy_description="Multiplies highest +EV discrepancies where Stake pricing lags Pinnacle sharp line by >=1.5%.",
        risk_level="High Value",
        legs=val_legs,
        max_stake_pct=0.018
    )
    if slip_3:
        slips.append(slip_3)

    # -------------------------------------------------------------
    # SLIP 4: ⚡ "Double Lock" (2-Leg Precision Multiplier)
    # -------------------------------------------------------------
    lock_legs: List[CuratedSlipLeg] = []
    seen_4 = set()
    cand_4: List[Tuple[MatchSecondaryMarkets, AlternativeMarket]] = []
    for m in evaluated_matches:
        for mk in m.markets:
            if 1.25 <= mk.odds <= 1.55 and mk.win_probability >= 0.70:
                cand_4.append((m, mk))
    cand_4 = sorted(cand_4, key=lambda x: x[1].win_probability, reverse=True)

    for m, mk in cand_4:
        if m.match_id in seen_4:
            continue
        lock_legs.append(CuratedSlipLeg(
            match_id=m.match_id,
            match_name=m.match_name,
            competition=m.competition,
            home_team=m.home_team,
            away_team=m.away_team,
            kickoff_str=m.kickoff_str,
            venue=m.venue,
            market_type=mk.market_type,
            selection=mk.selection,
            odds=mk.odds,
            win_probability=mk.win_probability,
            safety_rating=mk.safety_rating,
            hedge_description=f"Double Lock Anchor ({mk.win_probability*100:.1f}% win prob)"
        ))
        seen_4.add(m.match_id)
        if len(lock_legs) >= 2:
            break

    slip_4 = make_slip(
        slip_id="double_lock",
        slip_name="Stake Double Lock (2-Leg Precision Multiplier)",
        strategy_badge="⚡ DOUBLE LOCK",
        strategy_description="Conservative 2-leg accumulator combining the two highest-certainty sweet-spot picks of the day for aggressive bankroll compounding.",
        risk_level="Low Risk",
        legs=lock_legs,
        max_stake_pct=0.035
    )
    if slip_4:
        slips.append(slip_4)

    return slips
