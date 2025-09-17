export async function renderFAQ() {
  const root = document.getElementById('app')
  root.innerHTML = `
    <section class="hero-section">
      <div class="container text-center hero-content">
        <h1 class="display-5 fw-bold mb-2">FAQ</h1>
        <p class="lead mb-0">Common questions about data, models, and usage</p>
      </div>
    </section>

    <div class="container py-4">
      <div class="analytics-card">
        <div class="accordion" id="faq">
          <div class="accordion-item">
            <h2 class="accordion-header" id="q1">
              <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#a1" aria-expanded="true" aria-controls="a1">
                Where does the data come from?
              </button>
            </h2>
            <div id="a1" class="accordion-collapse collapse show" aria-labelledby="q1" data-bs-parent="#faq">
              <div class="accordion-body text-muted">
                Data is ingested via the data_loader service from football APIs, normalized by data_cleaner, and stored in PostgreSQL. Some content is indexed in Elasticsearch.
              </div>
            </div>
          </div>

          <div class="accordion-item">
            <h2 class="accordion-header" id="q2">
              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#a2" aria-expanded="false" aria-controls="a2">
                How are predictions generated?
              </button>
            </h2>
            <div id="a2" class="accordion-collapse collapse" aria-labelledby="q2" data-bs-parent="#faq">
              <div class="accordion-body text-muted">
                The model service builds features from historical data, trains models, and writes predictions. The API joins predictions with fixtures and odds. You can regenerate future predictions via the admin endpoint.
              </div>
            </div>
          </div>

          <div class="accordion-item">
            <h2 class="accordion-header" id="q3">
              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#a3" aria-expanded="false" aria-controls="a3">
                Why do I sometimes see placeholders or missing badges?
              </button>
            </h2>
            <div id="a3" class="accordion-collapse collapse" aria-labelledby="q3" data-bs-parent="#faq">
              <div class="accordion-body text-muted">
                Some crest/league images are not available from source data. The UI provides graceful fallbacks to keep the layout stable.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
}


