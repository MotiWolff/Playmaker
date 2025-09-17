export async function renderAbout() {
  const root = document.getElementById('app')
  root.innerHTML = `
    <section class="hero-section">
      <div class="container text-center hero-content">
        <h1 class="display-5 fw-bold mb-2">About Playmaker</h1>
        <p class="lead mb-0">Professional football analytics and predictions</p>
      </div>
    </section>

    <div class="container py-4">
      <div class="row g-4">
        <div class="col-12">
          <div class="analytics-card">
            <h3 class="fw-bold mb-3"><i class="fas fa-bullseye text-primary me-2"></i> Our Mission</h3>
            <p class="text-muted mb-0">
              Playmaker provides high-quality football insights by combining curated data, feature engineering, and
              rigorously evaluated models. Our stack spans data ingestion, canonical storage in PostgreSQL, optional
              indexing/search in Elasticsearch, and an API/UI for exploration and decision making.
            </p>
          </div>
        </div>

        <div class="col-md-6">
          <div class="analytics-card">
            <h4 class="fw-bold mb-3"><i class="fas fa-diagram-project text-success me-2"></i> Architecture</h4>
            <ul class="mb-0">
              <li>Data loader/cleaner → canonical tables</li>
              <li>Model pipeline → features, training, predictions</li>
              <li>FastAPI → read-only endpoints consumed by UI</li>
              <li>UI → modern, responsive interface for insights</li>
            </ul>
          </div>
        </div>

        <div class="col-md-6">
          <div class="analytics-card">
            <h4 class="fw-bold mb-3"><i class="fas fa-shield-alt text-warning me-2"></i> Principles</h4>
            <ul class="mb-0">
              <li>Clear boundaries and explicit contracts</li>
              <li>Type hints and guard clauses in Python</li>
              <li>Config via environment variables</li>
              <li>Reproducible, observable pipelines</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  `
}


