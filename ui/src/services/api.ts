export interface CompetitionLite { competition_id: number; name: string; emblem_url?: string | null }
export interface ApiTeamLite { team_id: number; name: string }
export interface ApiPredictionLite { p_home: number; p_draw: number; p_away: number }
export interface ApiOddsLite { home_odds?: number | null; draw_odds?: number | null; away_odds?: number | null }
export interface ApiFixtureWithOdds {
  fixture_id: number;
  match_utc: string;
  competition_id?: number | null;
  competition_name?: string | null;
  home: ApiTeamLite;
  away: ApiTeamLite;
  home_crest_url?: string | null;
  away_crest_url?: string | null;
  prediction?: ApiPredictionLite | null;
  odds?: ApiOddsLite | null;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = {
  async getCompetitions(): Promise<CompetitionLite[]> {
    const r = await fetch(`${API_BASE_URL}/competitions`)
    if (!r.ok) throw new Error('competitions failed')
    return r.json()
  },
  async getStats(): Promise<any> {
    const r = await fetch(`${API_BASE_URL}/stats`)
    if (!r.ok) throw new Error('stats failed')
    return r.json()
  },
  async getUpcomingWithOdds(params?: { competition_id?: number[]; limit?: number; offset?: number }): Promise<ApiFixtureWithOdds[]> {
    const qs = new URLSearchParams()
    if (params?.competition_id) params.competition_id.forEach(id => qs.append('competition_id', String(id)))
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.offset) qs.set('offset', String(params.offset))
    const url = `${API_BASE_URL}/fixtures/upcoming_with_odds${qs.toString() ? `?${qs.toString()}` : ''}`
    const r = await fetch(url)
    if (!r.ok) throw new Error('fixtures failed')
    return r.json()
  },
  async getLeagues(): Promise<Record<string, { name: string }>> {
    const r = await fetch(`${API_BASE_URL}/leagues`)
    if (!r.ok) throw new Error('leagues failed')
    return r.json()
  },
  async getTeams(): Promise<Array<{ team_id: number; name: string; short_name: string; crest_url?: string }>> {
    const r = await fetch(`${API_BASE_URL}/teams`)
    if (!r.ok) throw new Error('teams failed')
    return r.json()
  },
  async predictByIds(home_team_id: number, away_team_id: number): Promise<ApiPredictionLite> {
    const qs = new URLSearchParams({ home_team_id: String(home_team_id), away_team_id: String(away_team_id) })
    const r = await fetch(`${API_BASE_URL}/predict?${qs.toString()}`)
    if (!r.ok) throw new Error('predict failed')
    return r.json()
  }
}
