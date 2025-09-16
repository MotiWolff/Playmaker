const API_BASE_URL = '${API_BASE_URL}'

export const api = {
  async competitions() {
    const response = await fetch(`${API_BASE_URL}/competitions`)
    if (!response.ok) throw new Error('Failed to fetch competitions')
    return response.json()
  },

  async teams(competitionId = null, limit = 500) {
    const url = competitionId 
      ? `${API_BASE_URL}/teams?competition_id=${competitionId}&limit=${limit}`
      : `${API_BASE_URL}/teams?limit=${limit}`
    const response = await fetch(url)
    if (!response.ok) throw new Error('Failed to fetch teams')
    return response.json()
  },

  async upcomingWithOdds(competitionId) {
    const response = await fetch(`${API_BASE_URL}/fixtures/upcoming_with_odds?competition_id=${competitionId}`)
    if (!response.ok) throw new Error('Failed to fetch fixtures')
    return response.json()
  },

  async modelMetrics() {
    const response = await fetch(`${API_BASE_URL}/model_metrics`)
    if (!response.ok) throw new Error('Failed to fetch model metrics')
    return response.json()
  },

  async predict(homeTeamId, awayTeamId) {
    const response = await fetch(`${API_BASE_URL}/predict?home_team_id=${homeTeamId}&away_team_id=${awayTeamId}`)
    if (!response.ok) throw new Error('Failed to get prediction')
    return response.json()
  }
}