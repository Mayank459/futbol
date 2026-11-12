"""Dixon-Coles Model and Exact Analytical Scoreline Matrix.

Implements:
1. Exact bivariate goal distribution with Dixon-Coles low-score correction tau(x, y).
2. Analytical extraction of 1X2, BTTS, and Over/Under probabilities with zero sampling noise.
3. Maximum Likelihood Estimation (MLE) fitting with time-decay weighting.
"""

from typing import Dict, Tuple, List, Optional
import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize
from src.core.schemas import AnalyticalMatchProbabilities


def dixon_coles_tau(x: int, y: int, lambda_home: float, mu_away: float, rho: float) -> float:
    """Dixon-Coles adjustment factor for low-scoring match outcomes.
    Corrects underestimation of 0-0, 1-0, 0-1, 1-1 scores.
    """
    if x == 0 and y == 0:
        return 1.0 - (lambda_home * mu_away * rho)
    elif x == 0 and y == 1:
        return 1.0 + (lambda_home * rho)
    elif x == 1 and y == 0:
        return 1.0 + (mu_away * rho)
    elif x == 1 and y == 1:
        return 1.0 - rho
    else:
        return 1.0


def compute_goal_matrix(
    lambda_home: float,
    mu_away: float,
    rho: float = -0.12,
    max_goals: int = 10
) -> np.ndarray:
    """Computes exact joint probability matrix P(Home = x, Away = y).
    Dimension: (max_goals + 1, max_goals + 1).
    """
    matrix = np.zeros((max_goals + 1, max_goals + 1), dtype=float)
    
    # Compute Poisson marginals
    home_probs = poisson.pmf(np.arange(max_goals + 1), lambda_home)
    away_probs = poisson.pmf(np.arange(max_goals + 1), mu_away)

    for x in range(max_goals + 1):
        for y in range(max_goals + 1):
            tau = dixon_coles_tau(x, y, lambda_home, mu_away, rho)
            # Tau can theoretically become slightly negative in extreme edge cases; clamp at 0
            tau = max(0.0, tau)
            matrix[x, y] = tau * home_probs[x] * away_probs[y]

    # Normalize to ensure sum equals exactly 1.0 (capturing residual tail probabilities)
    matrix /= np.sum(matrix)
    return matrix


def calculate_analytical_probabilities(
    lambda_home: float,
    mu_away: float,
    rho: float = -0.12,
    max_goals: int = 10
) -> AnalyticalMatchProbabilities:
    """Analytically extracts exact match outcome probabilities from the Dixon-Coles goal matrix.
    Eliminates Monte Carlo simulation noise completely for standard betting markets.
    """
    matrix = compute_goal_matrix(lambda_home, mu_away, rho, max_goals)

    # 1X2 Probabilities
    home_win = float(np.sum(np.tril(matrix, -1)))  # x > y
    draw = float(np.sum(np.diag(matrix)))          # x == y
    away_win = float(np.sum(np.triu(matrix, 1)))   # x < y

    # BTTS (Both Teams To Score)
    # YES: x >= 1 and y >= 1
    btts_yes = float(np.sum(matrix[1:, 1:]))
    btts_no = float(1.0 - btts_yes)

    # Total Goals Over/Under
    # Construct index grid for total goals
    x_indices, y_indices = np.indices(matrix.shape)
    total_goals = x_indices + y_indices

    over_1_5 = float(np.sum(matrix[total_goals > 1.5]))
    under_1_5 = float(1.0 - over_1_5)

    over_2_5 = float(np.sum(matrix[total_goals > 2.5]))
    under_2_5 = float(1.0 - over_2_5)

    over_3_5 = float(np.sum(matrix[total_goals > 3.5]))
    under_3_5 = float(1.0 - over_3_5)

    return AnalyticalMatchProbabilities(
        home_win=round(home_win, 5),
        draw=round(draw, 5),
        away_win=round(away_win, 5),
        btts_yes=round(btts_yes, 5),
        btts_no=round(btts_no, 5),
        over_1_5=round(over_1_5, 5),
        under_1_5=round(under_1_5, 5),
        over_2_5=round(over_2_5, 5),
        under_2_5=round(under_2_5, 5),
        over_3_5=round(over_3_5, 5),
        under_3_5=round(under_3_5, 5),
        score_matrix=matrix.tolist()
    )


class DixonColesModel:
    """MLE Estimation and parameter store for Dixon-Coles ratings."""

    def __init__(self, time_decay_xi: float = 0.0018):
        self.time_decay_xi = time_decay_xi
        self.attack_ratings: Dict[str, float] = {}
        self.defense_ratings: Dict[str, float] = {}
        self.home_advantage: float = 0.25
        self.rho: float = -0.12

    def fit(self, matches: List[Dict]) -> None:
        """Fits Dixon-Coles parameters via log-likelihood optimization.
        Each match dict requires:
        - home_team: str
        - away_team: str
        - home_goals: float (or npxg)
        - away_goals: float (or npxg)
        - days_ago: float
        """
        teams = sorted(list(set([m["home_team"] for m in matches] + [m["away_team"] for m in matches])))
        n_teams = len(teams)
        team_idx = {team: i for i, team in enumerate(teams)}

        # Parameters vector:
        # [0:n_teams] -> attack ratings (alpha)
        # [n_teams:2*n_teams] -> defense ratings (beta)
        # [-2] -> home advantage (gamma)
        # [-1] -> correlation parameter (rho)
        init_params = np.concatenate([
            np.repeat(0.05, n_teams),
            np.repeat(-0.05, n_teams),
            [0.25],
            [-0.10]
        ])

        def neg_log_likelihood(params):
            alphas = params[:n_teams]
            betas = params[n_teams:2*n_teams]
            gamma = params[-2]
            rho = params[-1]

            # Constraint: sum of alphas == n_teams (or mean == 0)
            penalty = 1000.0 * (np.sum(alphas) - 0.0) ** 2

            log_lik = 0.0
            for m in matches:
                h_idx = team_idx[m["home_team"]]
                a_idx = team_idx[m["away_team"]]
                
                # Expected goal intensities: exp(alpha_h + beta_a + gamma)
                lam = np.exp(alphas[h_idx] + betas[a_idx] + gamma)
                mu = np.exp(alphas[a_idx] + betas[h_idx])

                x = int(round(m["home_goals"]))
                y = int(round(m["away_goals"]))

                tau = dixon_coles_tau(x, y, lam, mu, rho)
                if tau <= 0:
                    return 1e9

                # Time decay weight
                weight = np.exp(-self.time_decay_xi * m.get("days_ago", 0))

                match_ll = np.log(tau) - lam + x * np.log(lam) - np.log(float(np.math.factorial(x))) \
                           - mu + y * np.log(mu) - np.log(float(np.math.factorial(y)))

                log_lik += weight * match_ll

            return -log_lik + penalty

        # Optimize bounds
        bounds = [( -3.0, 3.0 )] * (2 * n_teams) + [(0.0, 1.0), (-0.4, 0.4)]
        res = minimize(neg_log_likelihood, init_params, bounds=bounds, method="L-BFGS-B")

        if res.success:
            alphas = res.x[:n_teams]
            betas = res.x[n_teams:2*n_teams]
            self.home_advantage = float(res.x[-2])
            self.rho = float(res.x[-1])

            for team, idx in team_idx.items():
                self.attack_ratings[team] = float(alphas[idx])
                self.defense_ratings[team] = float(betas[idx])
        else:
            # Fallback to reasonable defaults if data is insufficient
            for team in teams:
                self.attack_ratings[team] = 0.0
                self.defense_ratings[team] = 0.0

    def predict_match(self, home_team: str, away_team: str) -> Tuple[float, float, float]:
        """Returns (lambda_home, mu_away, rho)."""
        alpha_h = self.attack_ratings.get(home_team, 0.0)
        beta_a = self.defense_ratings.get(away_team, 0.0)
        alpha_a = self.attack_ratings.get(away_team, 0.0)
        beta_h = self.defense_ratings.get(home_team, 0.0)

        lambda_h = np.exp(alpha_h + beta_a + self.home_advantage)
        mu_a = np.exp(alpha_a + beta_h)
        return float(lambda_h), float(mu_a), self.rho

