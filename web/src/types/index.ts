export interface TeamRating {
  team_name: string;
  league: string;
  xg_attack: number;
  xg_defense: number;
  kalman_attack: number;
  kalman_defense: number;
  form_momentum: number;
  logo_url: string;
}

export interface SecondaryMarket {
  market_type: string;
  selection: string;
  label: string;
  odds: number;
  win_probability: number;
  fair_odds: number;
  edge: number;
  safety_rating: "Ultra-Safe" | "Very Safe" | "Moderate" | string;
  uncertainty_hedge: boolean;
}

export interface MatchFixture {
  match_id: string;
  is_live: boolean;
  match_name: string;
  competition: string;
  competition_logo?: string | null;
  home_team: string;
  away_team: string;
  home_logo: string;
  away_logo: string;
  kickoff_time: string;
  kickoff_iso?: string;
  venue: string;
  broadcaster?: string;
  current_minute?: string;
  home_score?: number;
  away_score?: number;
  status?: string;
  momentum?: string;
  stake_odds: {
    home: number;
    draw: number;
    away: number;
  };
  pinnacle_odds?: {
    home: number;
    draw: number;
    away: number;
  };
  fair_probabilities: {
    home: number;
    draw: number;
    away: number;
  };
  fair_odds: {
    home: number;
    draw: number;
    away: number;
  };
  edges?: {
    home: number;
    draw: number;
    away: number;
  };
  is_uncertain_1x2?: boolean;
  best_safety_pick?: {
    market_type: string;
    selection: string;
    label: string;
    odds: number;
    win_probability: number;
    safety_rating: string;
  };
  secondary_markets?: SecondaryMarket[];
}

export interface CuratedSlipLeg {
  match_id: string;
  match_name: string;
  competition: string;
  home_team: string;
  away_team: string;
  home_logo: string;
  away_logo: string;
  kickoff_str: string;
  venue?: string | null;
  market_type: string;
  selection: string;
  odds: number;
  win_probability: number;
  safety_rating: string;
  hedge_description: string;
}

export interface CuratedBetSlip {
  slip_id: string;
  slip_name: string;
  strategy_badge: string;
  strategy_description: string;
  target_bookmaker: string;
  legs: CuratedSlipLeg[];
  combined_odds: number;
  combined_probability: number;
  combined_edge: number;
  suggested_stake_amount: number;
  potential_payout: number;
  net_profit_on_win: number;
  risk_level: string;
  copyable_text: string;
}

export interface SGPLeg {
  description: string;
  marginal_prob: number;
  fair_odds: number;
  market_type: string;
}

export interface SameGameParlay {
  match_id: string;
  match_name: string;
  competition: string;
  home_team: string;
  away_team: string;
  home_logo: string;
  away_logo: string;
  kickoff_str: string;
  combo_name: string;
  narrative: string;
  legs: SGPLeg[];
  exact_joint_probability: number;
  naive_independent_prob: number;
  correlation_boost_pct: number;
  true_fair_odds: number;
  stake_offered_odds: number;
  ev_edge: number;
  suggested_stake_amount: number;
  potential_payout: number;
  net_profit: number;
}

export interface SteamAlert {
  match_id: string;
  match_name: string;
  competition: string;
  kickoff_str: string;
  home_team: string;
  away_team: string;
  home_logo: string;
  away_logo: string;
  selection: string;
  team_selected: string;
  stake_current_odds: number;
  pinnacle_current_odds: number;
  pinnacle_fair_odds: number;
  line_drop_pct: number;
  lag_edge_pct: number;
  urgency_level: "CRITICAL" | "HIGH" | "MODERATE" | string;
  detection_time_utc: string;
  estimated_window_seconds: number;
}

export interface PaperBetRecord {
  bet_id: string;
  category: "LIVE_IN_PLAY" | "UPCOMING_SINGLE" | "UPCOMING_ACCA" | "SAME_GAME_PARLAY" | string;
  match_id: string;
  match_name: string;
  competition: string;
  kickoff_str: string;
  market_type: string;
  selection: string;
  stake_odds: number;
  fair_odds: number;
  model_probability: number;
  edge_pct: number;
  stake_amount: number;
  potential_payout: number;
  potential_profit: number;
  placed_at: string;
  current_match_state: string;
  settlement_status: "IN_PLAY_WINNING" | "IN_PLAY_TIED (PUSH PENDING)" | "PENDING" | "WON (FINAL)" | "LOST (FINAL)" | string;
  unrealized_or_realized_pnl: number;
  notes?: string;
  home_team?: string;
  away_team?: string;
  home_logo?: string;
  away_logo?: string;
}

export interface PortfolioSummary {
  total_bets: number;
  total_capital_staked: number;
  net_pnl: number;
  roi_pct: number;
  win_rate_pct: number;
  avg_clv_pct: number;
  active_in_play: number;
  upcoming_singles: number;
  accumulators: number;
  same_game_parlays: number;
}

export interface ActiveSlipItem {
  id: string;
  matchId: string;
  matchName: string;
  competition: string;
  kickoffStr: string;
  marketType: string;
  selection: string;
  odds: number;
  winProb: number;
  homeTeam: string;
  awayTeam: string;
  homeLogo: string;
  awayLogo: string;
}
