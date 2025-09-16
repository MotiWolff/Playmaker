import { api } from '../api.js'

export async function renderTeams() {
  const root = document.getElementById('app')
  root.innerHTML = ''

  // Hero Section
  const hero = document.createElement('div')
  hero.className = 'hero-section'
  hero.innerHTML = `
    <div class="container">
      <div class="hero-content text-center">
        <h1 class="display-4 fw-bold mb-3">Teams</h1>
        <p class="lead mb-0">Explore all teams and their information across different competitions</p>
      </div>
    </div>
  `
  root.appendChild(hero)

  // Main Content
  const mainContent = document.createElement('div')
  mainContent.className = 'container'
  mainContent.innerHTML = `
    <div class="text-center mb-5">
      <h2 class="h3 fw-bold">Select Competition</h2>
      <p class="text-muted">Choose a league to view teams</p>
    </div>
    
    <div id="competition-buttons" class="d-flex justify-content-center flex-wrap gap-3 mb-5">
      <div class="loading">
        <div class="spinner"></div>
      </div>
    </div>
    
    <div id="teams-container">
      <div class="text-center text-muted">
        <i class="fas fa-futbol fa-3x mb-3"></i>
        <p>Select a competition to view teams</p>
      </div>
    </div>
  `
  root.appendChild(mainContent)

  // Load competitions
  let competitions = []
  let selectedComp = null
  
  try {
    competitions = await api.competitions()
  } catch (e) {
    console.error('Error loading competitions:', e)
    document.getElementById('competition-buttons').innerHTML = '<div class="text-center text-danger">Error loading competitions</div>'
    return
  }

  // Render competition buttons
  function renderCompetitionButtons() {
    const container = document.getElementById('competition-buttons')
    container.innerHTML = ''
    
    competitions.forEach(comp => {
      const btn = document.createElement('button')
      btn.type = 'button'
      btn.className = `competition-btn ${selectedComp && selectedComp.competition_id === comp.competition_id ? 'active' : ''}`
      btn.innerHTML = `
        ${comp.emblem_url ? `<img src="${comp.emblem_url}" alt="${comp.name}" onerror="this.style.display='none'"/>` : ''}
        <div class="fw-semibold">${comp.name}</div>
      `
      btn.onclick = () => {
        selectedComp = comp
        renderCompetitionButtons()
        loadTeams()
      }
      container.appendChild(btn)
    })
  }

  // Load teams for selected competition
  async function loadTeams() {
    const container = document.getElementById('teams-container')
    
    if (!selectedComp) {
      container.innerHTML = `
        <div class="text-center text-muted">
          <i class="fas fa-futbol fa-3x mb-3"></i>
          <p>Select a competition to view teams</p>
        </div>
      `
      return
    }

    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>'
    
    try {
      const teams = await api.teams(selectedComp.competition_id)
      
      if (teams.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">No teams found for this competition</div>'
        return
      }

      const grid = document.createElement('div')
      grid.className = 'row g-4'
      
      teams.forEach(team => {
        const teamCard = document.createElement('div')
        teamCard.className = 'col-lg-3 col-md-4 col-sm-6'
        teamCard.innerHTML = `
          <div class="team-card">
            <img src="${team.crest_url || 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png'}" 
                 alt="${team.name}" class="team-logo" 
                 onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png'">
            <h5 class="fw-bold mb-2">${team.name}</h5>
            <p class="text-muted small mb-0">${team.short_name || team.name}</p>
          </div>
        `
        grid.appendChild(teamCard)
      })
      
      container.innerHTML = ''
      container.appendChild(grid)
      
      // Add stats
      const stats = document.createElement('div')
      stats.className = 'row g-3 mt-4'
      stats.innerHTML = `
        <div class="col-md-4">
          <div class="stat-card">
            <div class="stat-number text-primary">${teams.length}</div>
            <div class="fw-semibold">Total Teams</div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="stat-card">
            <div class="stat-number text-success">${teams.filter(t => t.crest_url).length}</div>
            <div class="fw-semibold">With Logos</div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="stat-card">
            <div class="stat-number text-info">${selectedComp.name}</div>
            <div class="fw-semibold">Competition</div>
          </div>
        </div>
      `
      container.appendChild(stats)
      
    } catch (e) {
      console.error('Error loading teams:', e)
      container.innerHTML = `
        <div class="text-center text-danger">
          <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
          <p>Error loading teams. Please try again.</p>
        </div>
      `
    }
  }

  // Initialize
  renderCompetitionButtons()
}
