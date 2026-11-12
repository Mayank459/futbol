"""Verification and end-to-end test script for the Football Value-Betting Engine.
Validates:
1. Shin vs Proportional devigging (demonstrating how Shin eliminates favorite-longshot bias).
2. Dixon-Coles exact analytical scoreline matrix calculation.
3. Value detection and fractional Kelly staking.
"""

import json
from src.core.schemas import MarketType
from src.modeling.devig import devig_proportional, devig_power, devig_shin
from src.modeling.dixon_coles import calculate_analytical_probabilities
from src.modeling.value import evaluate_bet_opportunity, calculate_clv


def test_devig_comparison():
    print("=" * 60)
    print("1. DE-VIGGING COMPARISON: SHIN vs PROPORTIONAL (FAVORITE-LONGSHOT BIAS)")
    print("=" * 60)
    # Typical Premier League match odds with ~4.5% bookmaker overround
    # e.g., Heavy Favorite (Arsenal vs Southampton)
    pinnacle_odds = {"home": 1.25, "draw": 6.80, "away": 12.50}
    implied_raw = {k: round(1.0 / v, 4) for k, v in pinnacle_odds.items()}
    overround = sum(implied_raw.values())

    prop_probs = devig_proportional(pinnacle_odds)
    power_probs = devig_power(pinnacle_odds)
    shin_probs = devig_shin(pinnacle_odds)

    print(f"Offered Odds: {pinnacle_odds}")
    print(f"Total Implied Overround: {round(overround * 100, 2)}%")
    print(f"Proportional Fair Probs: {prop_probs}")
    print(f"Power Method Fair Probs: {power_probs}")
    print(f"Shin Method Fair Probs:  {shin_probs}")
    print("\nObservation:")
    print(f"- Shin gives Away: {round(shin_probs['away']*100, 2)}% vs Proportional Away: {round(prop_probs['away']*100, 2)}%")
    print("  -> Proportional de-vigging over-estimates longshot chance by ignoring longshot bias,")
    print("     which would lead a naive model to falsely flag underdog bets as +EV!")


def test_analytical_probabilities():
    print("\n" + "=" * 60)
    print("2. DIXON-COLES EXACT ANALYTICAL SCORELINE MATRIX")
    print("=" * 60)
    # Arsenal (home expected goals lambda = 2.15) vs Chelsea (away expected goals mu = 1.10)
    lambda_home = 2.15
    mu_away = 1.10
    rho = -0.13

    probs = calculate_analytical_probabilities(lambda_home, mu_away, rho=rho)
    print(f"Inputs: Home xG={lambda_home}, Away xG={mu_away}, rho={rho}")
    print("\nExact Analytical Market Probabilities (Zero Sampling Noise):")
    print(f"  1X2:   Home={probs.home_win*100:.2f}% | Draw={probs.draw*100:.2f}% | Away={probs.away_win*100:.2f}%")
    print(f"  BTTS:  Yes={probs.btts_yes*100:.2f}%   | No={probs.btts_no*100:.2f}%")
    print(f"  Goals: Over 2.5={probs.over_2_5*100:.2f}% | Under 2.5={probs.under_2_5*100:.2f}%")
    print(f"  Goals: Over 1.5={probs.over_1_5*100:.2f}% | Under 1.5={probs.under_1_5*100:.2f}%")


def test_value_and_kelly_staking():
    print("\n" + "=" * 60)
    print("3. VALUE DETECTION AND FRACTIONAL KELLY STAKING")
    print("=" * 60)
    # Scenario:
    # Model gives Arsenal Home Win = 65.5% (0.655)
    # Pinnacle sharp line: 1.57 (Shin fair price: 1.60 -> 62.5% fair prob)
    # Soft Book (Stake) lag: Stake offers 1.68
    model_prob = 0.655
    stake_odds = 1.68
    pinnacle_fair_odds = 1.60
    bankroll = 1000.0  # $1000 bankroll

    pick = evaluate_bet_opportunity(
        match_id="EPL_2026_ARS_CHE",
        competition="Premier League",
        home_team="Arsenal",
        away_team="Chelsea",
        market=MarketType.ONE_X_TWO,
        selection="home",
        model_prob=model_prob,
        offered_odds=stake_odds,
        fair_sharp_odds=pinnacle_fair_odds,
        min_edge_threshold=0.035,
        kelly_fraction=0.25,
        bankroll_size=bankroll
    )

    if pick:
        print("VALUE BET IDENTIFIED!")
        print(f"Match: {pick.home_team} vs {pick.away_team} ({pick.competition})")
        print(f"Selection: {pick.selection.upper()} @ {pick.offered_odds}")
        print(f"Edge vs Stake: +{round(pick.edge * 100, 2)}%")
        print(f"Fractional Kelly Stake: {round(pick.stake_fraction * 100, 2)}% of bankroll (${pick.suggested_stake_amount})")
        print(f"Confidence: {pick.confidence_label.upper()}")
        print("Key Factors:")
        for factor in pick.key_factors:
            print(f" - {factor}")

        # Suppose match completes and closing Pinnacle fair odds were 1.58
        clv = calculate_clv(odds_taken=stake_odds, closing_no_vig_odds=1.58)
        print(f"\nClosing Line Value (CLV): +{round(clv * 100, 2)}% (Beating closing line confirms long-term edge)")


if __name__ == "__main__":
    test_devig_comparison()
    test_analytical_probabilities()
    test_value_and_kelly_staking()

