import { api } from '../api.js'

export async function renderPredict() {
  const root = document.getElementById("app");
  root.innerHTML = "";

  // Hero Section
  const hero = document.createElement("div");
  hero.className = "hero-section";
  hero.innerHTML = `
    <div class="container">
      <div class="hero-content text-center">
        <h1 class="display-4 fw-bold mb-3">Match Predictor</h1>
        <p class="lead mb-0">Get data-driven predictions for any match using our advanced model</p>
      </div>
    </div>
  `;
  root.appendChild(hero);

  // Main Content
  const mainContent = document.createElement("div");
  mainContent.className = "container";
  mainContent.innerHTML = `
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="predict-card">
          <div class="text-center mb-4">
            <h2 class="h3 fw-bold">Select Teams</h2>
            <p class="text-muted">Choose home and away teams to get match predictions</p>
          </div>
          
          <form id="predict-form">
            <div class="row g-4">
              <div class="col-md-6">
                <label for="home-team" class="form-label fw-semibold">Home Team</label>
                <select id="home-team" class="form-select team-select" required>
                  <option value="">Select home team...</option>
                </select>
                <div id="home-crest" class="text-center mt-2"></div>
              </div>
              
              <div class="col-md-6">
                <label for="away-team" class="form-label fw-semibold">Away Team</label>
                <select id="away-team" class="form-select team-select" required>
                  <option value="">Select away team...</option>
                </select>
                <div id="away-crest" class="text-center mt-2"></div>
              </div>
            </div>
            
            <div class="text-center mt-4">
              <button type="submit" class="btn predict-btn btn-lg">
                <i class="fas fa-calculator me-2"></i>
                Get Prediction
              </button>
            </div>
          </form>
          
          <div id="prediction-result" class="mt-5" style="display: none;"></div>
        </div>
      </div>
    </div>
  `;
  root.appendChild(mainContent);

  // Load teams (restrict to the 5 major competitions)
  let teams = [];
  try {
    const comps = await api.competitions();
    const allowed = (comps || []).filter((c) => {
      const n = (c.name || "").toLowerCase();
      return (
        n.includes("premier") ||
        n.includes("bundesliga") ||
        n.includes("uefa champions") ||
        n.includes("serie") ||
        n.includes("ligue")
      );
    });
    const compIds = allowed.map((c) => c.competition_id).filter(Boolean);
    // Fetch teams per competition and merge
    const seen = new Set();
    for (const cid of compIds) {
      try {
        const list = await api.teams(cid, 500);
        for (const t of list || []) {
          if (!seen.has(t.team_id)) {
            seen.add(t.team_id);
            teams.push(t);
          }
        }
      } catch (_) {
        /* ignore per-comp errors */
      }
    }
    // Sort by name
    teams.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
  } catch (e) {
    console.error("Error loading teams:", e);
    document.getElementById("home-team").innerHTML =
      '<option value="">Error loading teams</option>';
    document.getElementById("away-team").innerHTML =
      '<option value="">Error loading teams</option>';
    return;
  }

  // Populate team dropdowns
  const homeSelect = document.getElementById("home-team");
  const awaySelect = document.getElementById("away-team");

  teams.forEach((team) => {
    const option1 = document.createElement("option");
    option1.value = team.team_id;
    option1.textContent = team.name;
    homeSelect.appendChild(option1);

    const option2 = document.createElement("option");
    option2.value = team.team_id;
    option2.textContent = team.name;
    awaySelect.appendChild(option2);
  });

  // Team selection handlers
  function updateCrest(teamId, crestElement) {
    const team = teams.find((t) => t.team_id == teamId);
    if (team && team.crest_url) {
      crestElement.innerHTML = `
        <img src="${team.crest_url}" alt="${team.name}" class="team-logo" 
             onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png'">
      `;
    } else {
      crestElement.innerHTML = `
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png" 
             alt="Default" class="team-logo">
      `;
    }
  }

  homeSelect.addEventListener("change", (e) => {
    updateCrest(e.target.value, document.getElementById("home-crest"));
  });

  awaySelect.addEventListener("change", (e) => {
    updateCrest(e.target.value, document.getElementById("away-crest"));
  });

  // Form submission
  document
    .getElementById("predict-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();

      const homeTeamId = homeSelect.value;
      const awayTeamId = awaySelect.value;

      if (!homeTeamId || !awayTeamId) {
        alert("Please select both teams");
        return;
      }

      if (homeTeamId === awayTeamId) {
        alert("Please select different teams");
        return;
      }

      const resultDiv = document.getElementById("prediction-result");
      resultDiv.style.display = "block";
      resultDiv.innerHTML =
        '<div class="loading"><div class="spinner"></div></div>';

      try {
        const prediction = await api.predict(homeTeamId, awayTeamId);

        const homeTeam = teams.find((t) => t.team_id == homeTeamId);
        const awayTeam = teams.find((t) => t.team_id == awayTeamId);

        // Handle both API response formats
        const homeProb = prediction.p_home || prediction.home_win_prob || 0;
        const drawProb = prediction.p_draw || prediction.draw_prob || 0;
        const awayProb = prediction.p_away || prediction.away_win_prob || 0;

        resultDiv.innerHTML = `
        <div class="text-center mb-4">
          <h3 class="fw-bold">Match Prediction</h3>
          <div class="d-flex align-items-center justify-content-center gap-3 mb-3">
            <div class="text-center">
              <img src="${
                homeTeam?.crest_url ||
                "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png"
              }" 
                   alt="${homeTeam?.name}" class="team-logo mb-2" 
                   onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png'">
              <div class="fw-semibold">${homeTeam?.name}</div>
            </div>
            <div class="fs-4 fw-bold text-muted">VS</div>
            <div class="text-center">
              <img src="${
                awayTeam?.crest_url ||
                "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png"
              }" 
                   alt="${awayTeam?.name}" class="team-logo mb-2" 
                   onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png'">
              <div class="fw-semibold">${awayTeam?.name}</div>
            </div>
          </div>
        </div>
        
        <div class="row g-3">
          <div class="col-4">
            <div class="stat-card bg-gradient-success text-white">
              <div class="stat-number">${Math.round(homeProb * 100)}%</div>
              <div class="fw-semibold">Home Win</div>
            </div>
          </div>
          <div class="col-4">
            <div class="stat-card bg-gradient-warning text-white">
              <div class="stat-number">${Math.round(drawProb * 100)}%</div>
              <div class="fw-semibold">Draw</div>
            </div>
          </div>
          <div class="col-4">
            <div class="stat-card bg-gradient-danger text-white">
              <div class="stat-number">${Math.round(awayProb * 100)}%</div>
              <div class="fw-semibold">Away Win</div>
            </div>
          </div>
        </div>
        
        <div class="mt-4 text-center">
          <button class="btn btn-outline-primary" onclick="location.reload()">
            <i class="fas fa-redo me-2"></i>
            New Prediction
          </button>
        </div>
      `;
      } catch (e) {
        console.error("Error getting prediction:", e);
        resultDiv.innerHTML = `
        <div class="alert alert-danger text-center">
          <i class="fas fa-exclamation-triangle me-2"></i>
          Error getting prediction. Please try again.
        </div>
      `;
      }
    });
}