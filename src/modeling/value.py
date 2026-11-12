"""Value Detection, Staking, and Closing Line Value (CLV) Engine.

Calculates:
1. Expected Value (+EV)
2. Fractional Kelly Criterion with risk constraints
3. Closing Line Value (CLV)
"""

from typing import Optional, Dict
from src.core.schemas import BetRecommendation, MarketType


def calculate_edge(model_prob: float, odds: float) -> float:
    """Calculates Expected Value (EV) percentage:
    Edge = (Model Probability * Offered Odds) - 1.0
    """
    return (model_prob * odds) - 1.0


def calculate_fractional_kelly(
    model_prob: float,
    odds: float,
    kelly_fraction: float = 0.25,
    max_stake_cap: float = 0.03
) -> float:
    """Calculates fractional Kelly stake size as a proportion of total bankroll.

    Formula:
    Full Kelly f* = (p * b - q) / b = Edge / (Odds - 1)
    Fractional Kelly = f* * kelly_fraction

    Bounded between 0.0 and max_stake_cap (e.g., max 3% of bankroll per bet).
    """
    if odds <= 1.0 or model_prob <= 0.0:
        return 0.0

    b = odds - 1.0
    q = 1.0 - model_prob
    full_kelly = (model_prob * b - q) / b

    if full_kelly <= 0.0:
        return 0.0

    suggested_stake = full_kelly * kelly_fraction
    return min(max_stake_cap, round(suggested_stake, 4))


def evaluate_bet_opportunity(
    match_id: str,
    competition: str,
    home_team: str,
    away_team: str,
    market: MarketType,
    selection: str,
    model_prob: float,
    offered_odds: float,
    fair_sharp_odds: float,
    min_edge_threshold: float = 0.035,  # 3.5% minimum edge
    kelly_fraction: float = 0.25,
    bankroll_size: Optional[float] = None
) -> Optional[BetRecommendation]:
    """Evaluates whether an offered bet satisfies value criteria."""
    edge = calculate_edge(model_prob, offered_odds)

    # Bet only if model clears the required threshold
    if edge < min_edge_threshold:
        return None

    # Compare against sharp market: the offered odds must also beat fair sharp odds
    sharp_edge = (offered_odds / fair_sharp_odds) - 1.0
    if sharp_edge <= 0.0:
        # Stake odds do not beat Pinnacle fair odds - likely model disagreement rather than market value
        return None

    stake_fraction = calculate_fractional_kelly(model_prob, offered_odds, kelly_fraction=kelly_fraction)
    if stake_fraction <= 0.0:
        return None

    stake_amount = round(bankroll_size * stake_fraction, 2) if bankroll_size else None

    # Confidence label based on edge and agreement with sharp price
    if edge >= 0.08 and sharp_edge >= 0.04:
        confidence = "high"
    elif edge >= 0.05:
        confidence = "medium"
    else:
        confidence = "low"

    key_factors = [
        f"Offered odds {offered_odds} beat sharp fair price {round(fair_sharp_odds, 3)} (+{round(sharp_edge*100, 2)}% vs sharp close)",
        f"Model probability: {round(model_prob*100, 1)}% vs Implied: {round((1.0/offered_odds)*100, 1)}%",
        f"Estimated edge: +{round(edge*100, 2)}%"
    ]

    risks = [
        "Soft-book pricing discrepancy or market lag",
        f"Subject to variance; Kelly stake capped at {round(stake_fraction*100, 2)}% of bankroll"
    ]

    return BetRecommendation(
        match_id=match_id,
        competition=competition,
        home_team=home_team,
        away_team=away_team,
        market=market,
        selection=selection,
        model_probability=round(model_prob, 4),
        offered_odds=offered_odds,
        fair_sharp_odds=round(fair_sharp_odds, 3),
        edge=round(edge, 4),
        stake_fraction=stake_fraction,
        suggested_stake_amount=stake_amount,
        confidence_label=confidence,
        key_factors=key_factors,
        risks=risks
    )


def calculate_clv(odds_taken: float, closing_no_vig_odds: float) -> float:
    """Closing Line Value (CLV).
    Measures the true statistical edge independent of individual match outcomes.
    CLV = (Odds Taken / Closing No-Vig Odds) - 1.0
    """
    if closing_no_vig_odds <= 0.0:
        return 0.0
    return (odds_taken / closing_no_vig_odds) - 1.0

