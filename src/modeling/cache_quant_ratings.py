"""Pre-computes and caches xG and Kalman team ratings per league across all Big 5 leagues."""

import glob
import json
import os
import pandas as pd
from src.modeling.xg_dixon_coles import XGDixonColesModel
from src.modeling.kalman_ratings import OnlineKalmanFilter

files = glob.glob("data/*_2324.csv")

quant_data = {
    "generated_at": pd.Timestamp.now().isoformat(),
    "teams": {}
}

for f in files:
    league_name = os.path.basename(f).replace("_2324.csv", "")
    df = pd.read_csv(f)

    # Train xG Dixon-Coles per league (connected graph)
    xg_model = XGDixonColesModel()
    xg_model.fit_from_dataframe(df)

    # Train Online Kalman Filter per league
    kf = OnlineKalmanFilter()
    kf.train_on_season_dataframe(df)

    for team in xg_model.teams:
        att_xg = xg_model.attack_ratings.get(team, 0.0)
        def_xg = xg_model.defense_ratings.get(team, 0.0)

        kalman_state = kf.teams.get(team)
        k_att = kalman_state.attack if kalman_state else att_xg
        k_def = kalman_state.defense if kalman_state else def_xg
        k_mom = kalman_state.momentum if kalman_state else 0.0

        quant_data["teams"][team] = {
            "league": league_name,
            "xg_attack": round(att_xg, 3),
            "xg_defense": round(def_xg, 3),
            "kalman_attack": round(k_att, 3),
            "kalman_defense": round(k_def, 3),
            "form_momentum": round(k_mom, 3)
        }

os.makedirs("data", exist_ok=True)
with open("data/team_quant_ratings.json", "w", encoding="utf-8") as f:
    json.dump(quant_data, f, indent=2)

print(f"Successfully cached quant ratings for {len(quant_data['teams'])} European teams in data/team_quant_ratings.json")
