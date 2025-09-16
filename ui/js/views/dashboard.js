import { api } from '../api.js'
import { fixtureCard } from '../components/fixtureCard.js'

export async function renderDashboard() {
  const root = document.getElementById('app')
  root.innerHTML = ''

  // Hero Section
  const hero = document.createElement('div')
  hero.className = 'hero-section'
  hero.innerHTML = `
    <div class="container">
      <div class="hero-content text-center">
        <h1 class="display-4 fw-bold mb-3">Professional Football Predictions</h1>
        <p class="lead mb-0">Dixon & Coles goals model with Expected Value (EV) analysis. Explore competitions, upcoming fixtures and data-driven probabilities.</p>
      </div>
    </div>
  `
  root.appendChild(hero)

  // Competition Selection
  const compSection = document.createElement('div')
  compSection.className = 'container mb-5'
  compSection.innerHTML = `
    <div class="text-center mb-4">
      <h2 class="h3 fw-bold">Select Competition</h2>
      <p class="text-muted">Choose a league to view upcoming fixtures and predictions</p>
    </div>
  `
  
  const chipsWrap = document.createElement('div')
  chipsWrap.className = 'd-flex justify-content-center flex-wrap gap-3'
  
  let comps = []
  try { 
    comps = await api.competitions() 
  } catch (e) {
    console.error('Error loading competitions:', e)
  }
  
  let selected = comps.find(c => (c.name || '').toLowerCase().includes('premier league')) || comps[0] || null

  function renderChips() {
    chipsWrap.innerHTML = ''
    comps.forEach(c => {
      const btn = document.createElement('button')
      btn.type = 'button'
      btn.className = `competition-btn ${selected && selected.competition_id === c.competition_id ? 'active' : ''}`
      btn.innerHTML = `
        ${c.emblem_url ? `<img src="${c.emblem_url}" alt="${c.name}" onerror="this.style.display='none'"/>` : ''}
        <div class="fw-semibold">${c.name}</div>
      `
      btn.setAttribute('aria-label', `Select ${c.name}`)
      btn.onclick = () => {
        selected = c
        renderChips()
        loadFixtures()
      }
      chipsWrap.appendChild(btn)
    })
  }
  
  compSection.appendChild(chipsWrap)
  root.appendChild(compSection)

  // Fixtures Section
  const fixturesSection = document.createElement('div')
  fixturesSection.className = 'container'
  fixturesSection.innerHTML = `
    <div class="text-center mb-4">
      <h2 class="h3 fw-bold">Upcoming Fixtures</h2>
      <p class="text-muted">Match predictions with win probabilities</p>
    </div>
    <div id="fixtures-container">
      <div class="loading">
        <div class="spinner"></div>
      </div>
    </div>
  `
  root.appendChild(fixturesSection)

  async function loadFixtures() {
    const container = document.getElementById('fixtures-container')
    if (!selected) {
      container.innerHTML = '<div class="text-center text-muted">Please select a competition</div>'
      return
    }

    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>'
    
    try {
      const fixtures = await api.upcomingWithOdds(selected.competition_id)
      if (fixtures.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">No upcoming fixtures found</div>'
        return
      }

      const grid = document.createElement('div')
      grid.className = 'row g-4'
      grid.innerHTML = fixtures.map(f => `<div class="col-lg-6 col-xl-4">${fixtureCard(f)}</div>`).join('')
      
      const legend = document.createElement('div')
      legend.className = 'text-center text-muted small mt-4'
      legend.innerHTML = `
        <div class="d-flex justify-content-center gap-4 flex-wrap">
          <span><span class="badge bg-success me-1">H</span> Home Win</span>
          <span><span class="badge bg-warning me-1">D</span> Draw</span>
          <span><span class="badge bg-danger me-1">A</span> Away Win</span>
        </div>
      `
      
      container.innerHTML = ''
      container.appendChild(grid)
      container.appendChild(legend)
    } catch (e) {
      console.error('Error loading fixtures:', e)
      container.innerHTML = '<div class="text-center text-danger">Error loading fixtures. Please try again.</div>'
    }
  }

  // Initialize
  renderChips()
  if (selected) {
    loadFixtures()
  }
}