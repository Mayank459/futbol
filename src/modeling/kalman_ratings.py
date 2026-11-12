"""Dynamic Online Kalman Filter for Team Attack & Defense Ratings.

Tracks team form continuously week-by-week using State-Space formulation.
Formulation:
1. State vector for each team i:
   x_i = [alpha_i, beta_i]^T (attack strength, defense vulnerability)
2. State Evolution (Random Walk with Drift):
   x_i(t) = x_i(t-1) + w_t,  w_t ~ N(0, Q)
   Process noise Q allows latent form to evolve as squads change and tactics shift.
3. Measurement Model:
   y_h = alpha_h + beta_a + gamma + v_h,  v_h ~ N(0, R)
   y_a = alpha_a + beta_h + v_a,          v_a ~ N(0, R)
   where y = ln(xG + 0.1) is observed log-xG intensity.
4. Kalman Innovation Update:
   Calculates Kalman gain K_t, updates ratings and uncertainty covariance P_t.
   Tracks Form Momentum / Form Surge (dRating/dt) for each team.
"""

from typing import Dict, Tuple, List, Optional
import numpy as np
import pandas as pd


class TeamKalmanState:
    def __init__(self, name: str, init_alpha: float = 0.0, init_beta: float = 0.0, init_var: float = 0.15):
        self.name = name
        # State vector: [alpha (attack), beta (defense vulnerability)]
        self.x = np.array([init_alpha, init_beta], dtype=float)
        # Covariance matrix P
        self.P = np.eye(2, dtype=float) * init_var
        # History for tracking momentum / velocity
        self.history: List[Tuple[float, float]] = [(init_alpha, init_beta)]

    @property
    def attack(self) -> float:
        return float(self.x[0])

    @property
    def defense(self) -> float:
        return float(self.x[1])

    @property
    def momentum(self) -> float:
        """Rate of change over last 3 updates (positive = surging attack / form)."""
        if len(self.history) < 2:
            return 0.0
        recent = self.history[-1][0] - self.history[-min(4, len(self.history))][0]
        return float(recent)


class OnlineKalmanFilter:
    def __init__(
        self,
        process_noise_q: float = 0.005,  # Form volatility week-to-week
        measurement_noise_r: float = 0.25, # Noise in individual match outcomes
        home_advantage: float = 0.22
    ):
        self.Q = np.eye(2) * process_noise_q
        self.R = measurement_noise_r
        self.gamma = home_advantage
        self.teams: Dict[str, TeamKalmanState] = {}

    def get_or_create_team(self, team_name: str) -> TeamKalmanState:
        if team_name not in self.teams:
            self.teams[team_name] = TeamKalmanState(name=team_name)
        return self.teams[team_name]

    def update_match(self, home_team: str, away_team: str, home_xg: float, away_xg: float) -> None:
        """Applies Kalman measurement update from a completed match."""
        h_state = self.get_or_create_team(home_team)
        a_state = self.get_or_create_team(away_team)

        # 1. Prediction step (propagate covariance with process noise)
        h_state.P += self.Q
        a_state.P += self.Q

        # 2. Predicted log-xG
        pred_log_h = h_state.attack + a_state.defense + self.gamma
        pred_log_a = a_state.attack + h_state.defense

        # Observed log-xG (clamped at epsilon)
        obs_log_h = np.log(max(0.1, home_xg))
        obs_log_a = np.log(max(0.1, away_xg))

        # Residuals / Innovations
        innov_h = obs_log_h - pred_log_h
        innov_a = obs_log_a - pred_log_a

        # 3. Measurement Update for Home Attack and Away Defense
        # Innovation variance S_h = Var(alpha_h) + Var(beta_a) + R
        S_h = h_state.P[0, 0] + a_state.P[1, 1] + self.R
        K_h_att = h_state.P[0, 0] / S_h
        K_a_def = a_state.P[1, 1] / S_h

        h_state.x[0] += K_h_att * innov_h
        a_state.x[1] += K_a_def * innov_h

        h_state.P[0, 0] *= (1.0 - K_h_att)
        a_state.P[1, 1] *= (1.0 - K_a_def)

        # 4. Measurement Update for Away Attack and Home Defense
        S_a = a_state.P[0, 0] + h_state.P[1, 1] + self.R
        K_a_att = a_state.P[0, 0] / S_a
        K_h_def = h_state.P[1, 1] / S_a

        a_state.x[0] += K_a_att * innov_a
        h_state.x[1] += K_h_def * innov_a

        a_state.P[0, 0] *= (1.0 - K_a_att)
        h_state.P[1, 1] *= (1.0 - K_h_def)

        # Record history
        h_state.history.append((h_state.attack, h_state.defense))
        a_state.history.append((a_state.attack, a_state.defense))

    def predict_match(self, home_team: str, away_team: str) -> Tuple[float, float]:
        """Returns dynamically predicted expected goals (lambda_home, mu_away)."""
        h_state = self.get_or_create_team(home_team)
        a_state = self.get_or_create_team(away_team)

        lambda_h = np.exp(h_state.attack + a_state.defense + self.gamma)
        mu_a = np.exp(a_state.attack + h_state.defense)
        return float(lambda_h), float(mu_a)

    def train_on_season_dataframe(self, df: pd.DataFrame) -> None:
        """Processes matches chronologically to dynamically calibrate all team states."""
        # Ensure xG columns exist
        if "HomeXG" not in df.columns:
            if "HST" in df.columns and "HS" in df.columns:
                df["HomeXG"] = 0.330 * df["HST"].fillna(4.0) + 0.025 * (df["HS"].fillna(12.0) - df["HST"].fillna(4.0))
            else:
                df["HomeXG"] = df["FTHG"].fillna(1.4)

        if "AwayXG" not in df.columns:
            if "AST" in df.columns and "AS" in df.columns:
                df["AwayXG"] = 0.330 * df["AST"].fillna(3.5) + 0.025 * (df["AS"].fillna(10.0) - df["AST"].fillna(3.5))
            else:
                df["AwayXG"] = df["FTAG"].fillna(1.1)

        for _, row in df.iterrows():
            self.update_match(
                home_team=str(row["HomeTeam"]),
                away_team=str(row["AwayTeam"]),
                home_xg=float(row["HomeXG"]),
                away_xg=float(row["AwayXG"])
            )

