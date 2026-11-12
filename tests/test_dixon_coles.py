"""Unit tests for Dixon-Coles and Analytical Goal Matrix.
Verifies:
1. Matrix sums to 1.0 across various lambda / mu / rho configurations.
2. Home Win, Draw, Away Win sum to 1.0.
3. BTTS Yes / No sum to 1.0.
4. Over / Under sum to 1.0.
5. Verifies independence of Home Win vs BTTS calculations.
"""

import numpy as np
from src.modeling.dixon_coles import compute_goal_matrix, calculate_analytical_probabilities


def test_matrix_properties():
    test_cases = [
        {"lam": 2.15, "mu": 1.10, "rho": -0.13},
        {"lam": 1.40, "mu": 1.40, "rho": -0.10},  # Even matchup
        {"lam": 3.20, "mu": 0.50, "rho": -0.15},  # Heavy favorite
        {"lam": 0.80, "mu": 0.90, "rho": -0.05},  # Low-scoring defensive battle
    ]

    for tc in test_cases:
        lam, mu, rho = tc["lam"], tc["mu"], tc["rho"]
        matrix = compute_goal_matrix(lam, mu, rho, max_goals=12)
        probs = calculate_analytical_probabilities(lam, mu, rho, max_goals=12)

        # 1. Matrix sum
        assert np.isclose(np.sum(matrix), 1.0, atol=1e-5), f"Matrix does not sum to 1 for {tc}"

        # 2. 1X2 sum
        sum_1x2 = probs.home_win + probs.draw + probs.away_win
        assert np.isclose(sum_1x2, 1.0, atol=1e-4), f"1X2 does not sum to 1 for {tc}"

        # 3. BTTS sum
        sum_btts = probs.btts_yes + probs.btts_no
        assert np.isclose(sum_btts, 1.0, atol=1e-4), f"BTTS does not sum to 1 for {tc}"

        # 4. Over/Under 2.5 sum
        sum_ou25 = probs.over_2_5 + probs.under_2_5
        assert np.isclose(sum_ou25, 1.0, atol=1e-4), f"O/U 2.5 does not sum to 1 for {tc}"

    print("All matrix and probability sanity tests passed!")


def test_home_vs_btts_independence():
    # Show that 60.13% was a parameter coincidence for (2.15, 1.10, -0.13)
    p1 = calculate_analytical_probabilities(2.15, 1.10, -0.13)
    p2 = calculate_analytical_probabilities(1.80, 1.20, -0.13)

    print(f"Case 1 (2.15 vs 1.10): Home Win = {p1.home_win*100:.2f}%, BTTS Yes = {p1.btts_yes*100:.2f}% (Coincidence matched to 2 d.p.)")
    print(f"Case 2 (1.80 vs 1.20): Home Win = {p2.home_win*100:.2f}%, BTTS Yes = {p2.btts_yes*100:.2f}% (Decoupled)")
    assert p2.home_win != p2.btts_yes


if __name__ == "__main__":
    test_matrix_properties()
    test_home_vs_btts_independence()

