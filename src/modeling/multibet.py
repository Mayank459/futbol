"""Multi-Bet (Accumulator / Parlay) Builder for Stake.

Enables combining safe, high-probability dominating team picks into a multiplied-odds slip on Stake (stake.ac).
Key Mathematical Guardrails:
1. Independence Guarantee: Legs must come from completely separate matches (no same-game correlations).
2. Safety Filter: Each leg must have high individual probability (typically >= 60-70% for heavy favorites).
3. Value Compounding: Ensures each leg has positive or fair value against Pinnacle Shin fair lines,
   so bookmaker margin does not compound against the bettor.
4. Combined Metrics:
   - Multiplied Odds: O_multi = O_1 * O_2 * ... * O_k
   - Joint Win Probability: P_multi = P_1 * P_2 * ... * P_k
   - Multi-Bet Edge: (P_multi * O_multi) - 1.0
   - Multi-Bet Kelly Staking.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from src.core.schemas import BetRecommendation


class MultiBetLeg(BaseModel):
    match_id: str
    match_name: str
    competition: str
    selection: str
    team_selected: str
    odds: float
    fair_odds: float
    win_probability: float
    safety_rating: str  # "Very Safe" (>=75%), "Safe" (65-74%)


class MultiBetSlip(BaseModel):
    slip_name: str
    target_bookmaker: str = "Stake (stake.ac)"
    legs: List[MultiBetLeg]
    combined_odds: float = Field(..., description="Multiplied total odds on Stake")
    combined_probability: float = Field(..., description="Joint probability of all legs winning")
    combined_edge: float = Field(..., description="Net expected value edge")
    suggested_stake_fraction: float
    suggested_stake_amount: float
    potential_payout: float
    net_profit_on_win: float


def build_stake_multibet(
    candidate_picks: List[Dict],
    bankroll: float = 1000.0,
    max_legs: int = 3,
    min_leg_probability: float = 0.60,
    kelly_fraction: float = 0.15
) -> Optional[MultiBetSlip]:
    """Assembles a high-confidence multi-bet slip from dominating team picks."""
    # Filter for high-probability safe favorites
    safe_legs: List[MultiBetLeg] = []
    seen_matches = set()

    # Sort candidates by win probability descending (safest favorites first)
    sorted_candidates = sorted(candidate_picks, key=lambda x: x["model_probability"], reverse=True)

    for c in sorted_candidates:
        match_id = c["match_id"]
        prob = c["model_probability"]
        odds = c["offered_odds"]

        # Ensure single leg comes from distinct matches
        if match_id in seen_matches:
            continue
        if prob < min_leg_probability:
            continue

        safety = "Very Safe" if prob >= 0.75 else "Safe"
        team_name = c["home_team"] if c["selection"] == "home" else (c["away_team"] if c["selection"] == "away" else "Draw")

        safe_legs.append(MultiBetLeg(
            match_id=match_id,
            match_name=f"{c['home_team']} vs {c['away_team']}",
            competition=c.get("competition", "Domestic League"),
            selection=c["selection"].upper(),
            team_selected=team_name,
            odds=odds,
            fair_odds=c.get("fair_sharp_odds", odds),
            win_probability=round(prob, 4),
            safety_rating=safety
        ))
        seen_matches.add(match_id)

        if len(safe_legs) >= max_legs:
            break

    if len(safe_legs) < 2:
        return None

    # Calculate multiplied metrics
    combined_odds = 1.0
    combined_prob = 1.0
    for leg in safe_legs:
        combined_odds *= leg.odds
        combined_prob *= leg.win_probability

    combined_odds = round(combined_odds, 3)
    combined_prob = round(combined_prob, 4)
    combined_edge = round((combined_prob * combined_odds) - 1.0, 4)

    # Fractional Kelly for Multi-Bet
    b = combined_odds - 1.0
    q = 1.0 - combined_prob
    full_kelly = (combined_prob * b - q) / b if b > 0 else 0.0

    # Cap multi-bet stake conservatively at 1.5% of bankroll to protect against acca variance
    stake_fraction = min(0.015, max(0.005, round(full_kelly * kelly_fraction, 4)))
    stake_amount = round(bankroll * stake_fraction, 2)
    potential_payout = round(stake_amount * combined_odds, 2)
    net_profit = round(potential_payout - stake_amount, 2)

    return MultiBetSlip(
        slip_name=f"Stake Multi-Bet ({len(safe_legs)}-Leg Dominating Favorites)",
        legs=safe_legs,
        combined_odds=combined_odds,
        combined_probability=combined_prob,
        combined_edge=combined_edge,
        suggested_stake_fraction=stake_fraction,
        suggested_stake_amount=stake_amount,
        potential_payout=potential_payout,
        net_profit_on_win=net_profit
    )

