import { renderDashboard } from './views/dashboard.js'
import { renderPredict } from './views/predict.js'
import { renderTeams } from './views/teams.js'
import { renderAnalytics } from './views/analytics.js'

const routes = {
  '/': renderDashboard,
  '/predict': renderPredict,
  '/teams': renderTeams,
  '/analytics': renderAnalytics
}

export function initRouter() {
  // Handle initial load
  const path = window.location.hash.slice(1) || '/'
  renderRoute(path)

  // Handle navigation
  window.addEventListener('hashchange', () => {
    const path = window.location.hash.slice(1) || '/'
    renderRoute(path)
  })

  // Handle nav link clicks
  document.addEventListener('click', (e) => {
    if (e.target.matches('[data-link]')) {
      e.preventDefault()
      const path = e.target.getAttribute('href').slice(1)
      window.location.hash = path
    }
  })
}

function renderRoute(path) {
  const app = document.getElementById('app')
  
  // Update active nav link
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active')
    if (link.getAttribute('href') === `#${path}`) {
      link.classList.add('active')
    }
  })

  // Render the route
  const routeHandler = routes[path]
  if (routeHandler) {
    routeHandler().catch(error => {
      console.error('Error rendering route:', error)
      app.innerHTML = `
        <div class="container py-5">
          <div class="text-center">
            <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
            <h2 class="text-danger">Error Loading Page</h2>
            <p class="text-muted">Something went wrong. Please try again.</p>
            <button class="btn btn-primary" onclick="location.reload()">
              <i class="fas fa-redo me-2"></i>
              Reload Page
            </button>
          </div>
        </div>
      `
    })
  } else {
    // 404 page
    app.innerHTML = `
      <div class="container py-5">
        <div class="text-center">
          <i class="fas fa-search fa-3x text-muted mb-3"></i>
          <h2>Page Not Found</h2>
          <p class="text-muted">The page you're looking for doesn't exist.</p>
          <a href="#/" class="btn btn-primary">
            <i class="fas fa-home me-2"></i>
            Go Home
          </a>
        </div>
      </div>
    `
  }
}