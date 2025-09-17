import { DEFAULT_FOOTBALL_ICON } from './imgFallback.js'

export function fixtureCard(fixture) {
  const homeCrest = fixture.home_crest_url || DEFAULT_FOOTBALL_ICON
  const awayCrest = fixture.away_crest_url || DEFAULT_FOOTBALL_ICON
  
  const formatDate = (dateStr) => {
    if (!dateStr) return 'TBD'
    const date = new Date(dateStr)
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  }

  const formatTime = (dateStr) => {
    if (!dateStr) return 'TBD'
    const date = new Date(dateStr)
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Handle both prediction object and direct probability fields
  const prediction = fixture.prediction || {}
  const homeWinProb = Math.round((prediction.p_home || fixture.home_win_prob || 0) * 100)
  const drawProb = Math.round((prediction.p_draw || fixture.draw_prob || 0) * 100)
  const awayWinProb = Math.round((prediction.p_away || fixture.away_win_prob || 0) * 100)

  return `
    <div class="fixture-card">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <div class="text-muted small">
          <i class="fas fa-calendar-alt me-1"></i>
          ${formatDate(fixture.match_utc)}
        </div>
        <div class="text-muted small">
          <i class="fas fa-clock me-1"></i>
          ${formatTime(fixture.match_utc)}
        </div>
      </div>
      
      <div class="text-center mb-3">
        <span class="badge bg-primary">${fixture.competition_name || 'Match'}</span>
      </div>
      
      <div class="d-flex align-items-center justify-content-between mb-4">
        <div class="text-center flex-grow-1">
          <img src="${homeCrest}" 
               alt="${fixture.home.name} crest" 
               class="team-crest mb-2" 
               onerror="this.onerror=null;this.src='${DEFAULT_FOOTBALL_ICON}'">
          <div class="fw-semibold">${fixture.home.name}</div>
        </div>
        
        <div class="text-center mx-3">
          <div class="fs-4 fw-bold text-muted">VS</div>
        </div>
        
        <div class="text-center flex-grow-1">
          <img src="${awayCrest}" 
               alt="${fixture.away.name} crest" 
               class="team-crest mb-2" 
               onerror="this.onerror=null;this.src='${DEFAULT_FOOTBALL_ICON}'">
          <div class="fw-semibold">${fixture.away.name}</div>
        </div>
      </div>
      
      <div class="row g-2">
        <div class="col-4">
          <div class="text-center">
            <div class="prediction-bar bg-success mb-1" style="height: ${Math.max(homeWinProb * 0.1, 4)}px;"></div>
            <div class="small fw-semibold text-success">${homeWinProb}%</div>
            <div class="small text-muted">Home</div>
          </div>
        </div>
        <div class="col-4">
          <div class="text-center">
            <div class="prediction-bar bg-warning mb-1" style="height: ${Math.max(drawProb * 0.1, 4)}px;"></div>
            <div class="small fw-semibold text-warning">${drawProb}%</div>
            <div class="small text-muted">Draw</div>
          </div>
        </div>
        <div class="col-4">
          <div class="text-center">
            <div class="prediction-bar bg-danger mb-1" style="height: ${Math.max(awayWinProb * 0.1, 4)}px;"></div>
            <div class="small fw-semibold text-danger">${awayWinProb}%</div>
            <div class="small text-muted">Away</div>
          </div>
        </div>
      </div>
    </div>
  `
}