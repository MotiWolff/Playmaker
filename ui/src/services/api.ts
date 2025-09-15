import { MatchPrediction, Team, Stats, League } from '../types';

const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async getLeagues(): Promise<Record<string, League>> {
    const response = await fetch(`${this.baseUrl}/leagues`);
    if (!response.ok) {
      throw new Error('Failed to fetch leagues');
    }
    return response.json();
  }

  async getTeams(league: string = 'PL'): Promise<Team[]> {
    const response = await fetch(`${this.baseUrl}/teams?league=${league}`);
    if (!response.ok) {
      throw new Error('Failed to fetch teams');
    }
    return response.json();
  }

  async getPredictions(league: string = 'PL'): Promise<MatchPrediction[]> {
    const response = await fetch(`${this.baseUrl}/predictions?league=${league}`);
    if (!response.ok) {
      throw new Error('Failed to fetch predictions');
    }
    return response.json();
  }

  async getPredictionsByMatchday(matchday: number): Promise<MatchPrediction[]> {
    const response = await fetch(`${this.baseUrl}/predictions/matchday/${matchday}`);
    if (!response.ok) {
      throw new Error('Failed to fetch predictions for matchday');
    }
    return response.json();
  }

  async predictMatch(homeTeam: string, awayTeam: string): Promise<MatchPrediction> {
    const response = await fetch(`${this.baseUrl}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ home_team: homeTeam, away_team: awayTeam }),
    });

    if (!response.ok) {
      throw new Error('Failed to predict match');
    }

    return response.json();
  }

  async getStats(league: string = 'PL'): Promise<Stats> {
    const response = await fetch(`${this.baseUrl}/stats?league=${league}`);
    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }
    return response.json();
  }
}

export default new ApiService();