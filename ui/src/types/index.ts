export interface MatchPrediction {
  match_id: string;
  home_team: string;
  away_team: string;
  home_team_short: string;
  away_team_short: string;
  home_team_logo: string;
  away_team_logo: string;
  home_prob: number;
  draw_prob: number;
  away_prob: number;
  prediction: string;
  confidence: number;
  betting_value: string;
  fair_odds: number;
  match_date: string;
  match_time: string;
  matchday: number;
}

export interface Team {
  id: number;
  name: string;
  short_name: string;
  logo_url: string;
}

export interface Stats {
  total_fixtures: number;
  confident_predictions: number;
  home_wins: number;
  draws: number;
  away_wins: number;
  high_value_bets: number;
  medium_value_bets: number;
  average_confidence: number;
}

export interface League {
  name: string;
  country: string;
  season: number;
}

export interface TeamStats {
  team_name: string;
  elo_rating: number;
  recent_form: number[];
  goals_for_avg: number;
  goals_against_avg: number;
  win_percentage: number;
}

export interface Match {
  matchId: number;
  date: string;
  homeTeam: string;
  awayTeam: string;
  result: 'H' | 'D' | 'A';
  eloHome: number;
  eloAway: number;
  eloDiff: number;
}

export interface ModelInfo {
  model_type: string;
  features: string[];
  n_features: number;
  best_params?: any;
  top_features?: Array<{
    feature: string;
    importance: number;
  }>;
}

export interface ModelPerformance {
  overall_accuracy: number;
  log_loss: number;
  brier_score: number;
  class_performance: {
    home_wins: {
      precision: number;
      recall: number;
      f1: number;
    };
    draws: {
      precision: number;
      recall: number;
      f1: number;
    };
    away_wins: {
      precision: number;
      recall: number;
      f1: number;
    };
  };
  feature_importance: Array<{
    feature: string;
    importance: number;
  }>;
}

export type PredictionOutcome = 'home' | 'draw' | 'away';