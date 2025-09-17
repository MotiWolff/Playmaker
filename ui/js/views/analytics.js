import { api } from '../api.js'

export async function renderAnalytics() {
  const root = document.getElementById('app')
  root.innerHTML = ''

  // Hero Section
  const hero = document.createElement('div')
  hero.className = 'hero-section'
  hero.innerHTML = `
    <div class="container">
      <div class="hero-content text-center">
        <h1 class="display-4 fw-bold mb-3">Analytics</h1>
        <p class="lead mb-0">Data insights and model performance metrics</p>
      </div>
    </div>
  `
  root.appendChild(hero)

  // Main Content
  const mainContent = document.createElement('div')
  mainContent.className = 'container'
  mainContent.innerHTML = `
    <div class="row g-4">
      <!-- Model Performance -->
      <div class="col-lg-6">
        <div class="analytics-card">
          <h3 class="fw-bold mb-4">
            <i class="fas fa-chart-line text-primary me-2"></i>
            Model Performance
          </h3>
          <div id="model-metrics" class="row g-3">
            <div class="loading"><div class="spinner"></div></div>
          </div>
        </div>
      </div>

      <!-- Competition Stats -->
      <div class="col-lg-6">
        <div class="analytics-card">
          <h3 class="fw-bold mb-4">
            <i class="fas fa-trophy text-warning me-2"></i>
            Competition Coverage
          </h3>
          <div id="competition-stats">
            <div class="loading">
              <div class="spinner"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Predictions -->
      <div class="col-12">
        <div class="analytics-card">
          <h3 class="fw-bold mb-4">
            <i class="fas fa-history text-info me-2"></i>
            Recent Predictions
          </h3>
          <div id="recent-predictions">
            <div class="loading">
              <div class="spinner"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Model Details -->
      <div class="col-12">
        <div class="analytics-card">
          <h3 class="fw-bold mb-4">
            <i class="fas fa-cogs text-secondary me-2"></i>
            Model Information
          </h3>
          <div class="row g-4">
            <div class="col-md-6">
              <h5 class="fw-semibold">Dixon & Coles Model</h5>
              <p class="text-muted">
                Our predictions are based on the Dixon & Coles goals model, which accounts for:
              </p>
              <ul class="list-unstyled">
                <li><i class="fas fa-check text-success me-2"></i>Team strength parameters</li>
                <li><i class="fas fa-check text-success me-2"></i>Home advantage factors</li>
                <li><i class="fas fa-check text-success me-2"></i>Recent form weighting</li>
                <li><i class="fas fa-check text-success me-2"></i>Head-to-head records</li>
              </ul>
            </div>
            <div class="col-md-6">
              <h5 class="fw-semibold">Expected Value Analysis</h5>
              <p class="text-muted">
                We calculate expected value for betting markets to identify profitable opportunities:
              </p>
              <ul class="list-unstyled">
                <li><i class="fas fa-check text-success me-2"></i>Market odds comparison</li>
                <li><i class="fas fa-check text-success me-2"></i>Value bet identification</li>
                <li><i class="fas fa-check text-success me-2"></i>Risk assessment</li>
                <li><i class="fas fa-check text-success me-2"></i>ROI optimization</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
  root.appendChild(mainContent)

  // Load competition stats
  async function loadCompetitionStats() {
    const container = document.getElementById('competition-stats')
    
    try {
      const coverageData = await api.competitionCoverage();
      
      const stats = coverageData
        .map(
          (comp) => `
        <div class="d-flex justify-content-between align-items-center py-3 border-bottom">
          <div class="d-flex align-items-center gap-2">
            <span class="fw-medium">${comp.name}</span>
          </div>
          <div class="text-end">
            <div class="fw-bold text-primary">${comp.coverage}%</div>
            <small class="text-muted">Coverage</small>
            <div class="small text-muted mt-1">
              ${comp.prediction_count}/${comp.fixture_count} fixtures
            </div>
          </div>
        </div>
      `
        )
        .join("");
      
      container.innerHTML = stats || '<div class="text-muted">No competition data available</div>'
    } catch (e) {
      console.error('Error loading competition stats:', e)
      container.innerHTML = '<div class="text-danger">Error loading stats</div>'
    }
  }

  // Load recent predictions (mock data)
  async function loadRecentPredictions() {
    const container = document.getElementById('recent-predictions')
    
    // Mock recent predictions data
    const mockPredictions = [
      { home: 'Arsenal', away: 'Chelsea', homeProb: 0.45, drawProb: 0.30, awayProb: 0.25, result: 'H', accuracy: true },
      { home: 'Liverpool', away: 'Manchester City', homeProb: 0.35, drawProb: 0.35, awayProb: 0.30, result: 'D', accuracy: true },
      { home: 'Tottenham', away: 'Newcastle', homeProb: 0.60, drawProb: 0.25, awayProb: 0.15, result: 'H', accuracy: true },
      { home: 'Brighton', away: 'Aston Villa', homeProb: 0.40, drawProb: 0.30, awayProb: 0.30, result: 'A', accuracy: false },
      { home: 'West Ham', away: 'Fulham', homeProb: 0.50, drawProb: 0.30, awayProb: 0.20, result: 'H', accuracy: true }
    ]
    
    const predictionsHtml = mockPredictions.map(pred => `
      <div class="d-flex justify-content-between align-items-center py-3 border-bottom">
        <div class="d-flex align-items-center gap-3">
          <div class="text-center">
            <div class="fw-semibold">${pred.home}</div>
            <div class="badge ${pred.result === 'H' ? 'bg-success' : 'bg-light text-dark'}">${Math.round(pred.homeProb * 100)}%</div>
          </div>
          <div class="text-muted">vs</div>
          <div class="text-center">
            <div class="fw-semibold">${pred.away}</div>
            <div class="badge ${pred.result === 'A' ? 'bg-success' : 'bg-light text-dark'}">${Math.round(pred.awayProb * 100)}%</div>
          </div>
        </div>
        <div class="text-end">
          <div class="d-flex align-items-center gap-2">
            <span class="badge ${pred.result === 'D' ? 'bg-warning' : 'bg-light text-dark'}">${pred.result === 'D' ? 'Draw' : pred.result}</span>
            <i class="fas ${pred.accuracy ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'}"></i>
          </div>
          <small class="text-muted">${Math.round(pred.drawProb * 100)}% draw</small>
        </div>
      </div>
    `).join('')
    
    container.innerHTML = predictionsHtml
  }

  // Initialize
  loadCompetitionStats()
  loadRecentPredictions()
  // Load real model metrics
  try {
    const metrics = await api.modelMetrics()
    const wrap = document.getElementById('model-metrics')
    const fmtPct = (v) => (v == null ? '—' : `${(v * 100).toFixed(2)}%`)
    const fmtNum = (v) => (v == null ? '—' : Number(v).toFixed(3))
    wrap.innerHTML = `
      <div class="col-4">
        <div class="stat-card">
          <div class="stat-number text-success">${fmtPct(metrics.accuracy)}</div>
          <div class="fw-semibold">Accuracy</div>
          <small class="text-muted">From model_version</small>
        </div>
      </div>
      <div class="col-4">
        <div class="stat-card">
          <div class="stat-number text-info">${fmtNum(metrics.brier)}</div>
          <div class="fw-semibold">Brier Score</div>
          <small class="text-muted">Lower is better</small>
        </div>
      </div>
      <div class="col-4">
        <div class="stat-card">
          <div class="stat-number text-primary">${fmtNum(metrics.log_loss)}</div>
          <div class="fw-semibold">Log Loss</div>
          <small class="text-muted">Lower is better</small>
        </div>
      </div>
    `
  } catch (e) {
    console.warn('Model metrics endpoint unavailable, hiding section')
    const section = document.getElementById('model-metrics')
    if (section) section.parentElement.style.display = 'none'
  }
}
