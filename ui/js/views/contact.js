export async function renderContact() {
  const root = document.getElementById('app')
  root.innerHTML = `
    <section class="hero-section">
      <div class="container text-center hero-content">
        <h1 class="display-5 fw-bold mb-2">Contact</h1>
        <p class="lead mb-0">Get in touch with the Playmaker team</p>
      </div>
    </section>

    <div class="container py-4">
      <div class="row g-4">
        <div class="col-md-6">
          <div class="analytics-card">
            <h4 class="fw-bold mb-3"><i class="fas fa-envelope text-primary me-2"></i> Reach us</h4>
            <ul class="mb-0">
              <li>Email: <a href="mailto:contact@playmaker.example" class="text-decoration-none">contact@playmaker.example</a></li>
              <li>Issues: <a href="https://github.com/MotiWolff/Playmaker/issues" target="_blank" class="text-decoration-none">GitHub Issues</a></li>
            </ul>
          </div>
        </div>
        <div class="col-md-6">
          <div class="analytics-card">
            <h4 class="fw-bold mb-3"><i class="fas fa-share-alt text-success me-2"></i> Social</h4>
            <p class="text-muted mb-0">Follow our updates and releases via the repository and project board.</p>
          </div>
        </div>
      </div>
    </div>
  `
}


