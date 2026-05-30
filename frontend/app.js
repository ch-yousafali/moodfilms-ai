// ─── MoodFilms — app.js ──────────────────────────────────────────────────────
// Communicates with /api/recommend on the FastAPI backend.
// Manages the 4-step flow: Industry → Query → Fallback → Mood

const API_BASE = "/api";  // Served by FastAPI on the same origin — no CORS

const QUICK_PICKS = [
  "Inception", "The Godfather", "Pulp Fiction",
  "3 Idiots", "Parasite", "Interstellar"
];

// ─── State ──────────────────────────────────────────────────────────────────
let selectedIndustry = "Hollywood";
let currentStep = "industry";

// ─── Helpers ────────────────────────────────────────────────────────────────
function $(id) { return document.getElementById(id); }

function showStep(name) {
  document.querySelectorAll(".step").forEach(s => s.classList.remove("active"));
  const target = $(`step-${name}`);
  if (target) target.classList.add("active");
  currentStep = name;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showLoading(visible) {
  $("loading").classList.toggle("hidden", !visible);
  $("results-grid").classList.toggle("hidden", visible);
  $("error-msg").classList.add("hidden");
}

function showError(msg) {
  const el = $("error-msg");
  el.textContent = msg;
  el.classList.remove("hidden");
  $("loading").classList.add("hidden");
}

// ─── Quick Picks ────────────────────────────────────────────────────────────
function renderQuickPicks() {
  const wrap = $("quick-picks");
  QUICK_PICKS.forEach(title => {
    const btn = document.createElement("button");
    btn.className = "quick-chip";
    btn.textContent = title;
    btn.onclick = () => {
      $("query-input").value = title;
      doSearch("direct", title);
    };
    wrap.appendChild(btn);
  });
}

// ─── Render Results ──────────────────────────────────────────────────────────
function renderResults(items, headingText) {
  const grid = $("results-grid");
  grid.innerHTML = "";
  $("results-title").textContent = headingText || "";

  if (!items || !items.length) {
    grid.innerHTML = `<p style="color:var(--text-muted);font-size:0.85rem;letter-spacing:0.06em;">No results found. Try a different title or mood.</p>`;
    return;
  }

  items.forEach(m => {
    const card = document.createElement("div");
    card.className = "movie-card";

    const posterHTML = m.poster
      ? `<img class="movie-poster" src="${m.poster}" alt="${m.title}" loading="lazy" />`
      : `<div class="movie-poster-placeholder">No Poster</div>`;

    card.innerHTML = `
      ${posterHTML}
      <div class="movie-body">
        <div class="movie-title">${m.title}</div>
        <div class="movie-meta">
          <span class="movie-rating">${m.tmdb_rating ? m.tmdb_rating + " / 10" : ""}</span>
          <span class="movie-year">${m.year || ""}</span>
        </div>
        <p class="movie-overview">${m.overview || ""}</p>
      </div>
    `;
    grid.appendChild(card);
  });
}

// ─── API Call ────────────────────────────────────────────────────────────────
async function doSearch(mode, query = null, mood = null) {
  showStep("results");
  showLoading(true);

  const body = {
    industry: selectedIndustry,
    mode,
    query: query || null,
    mood: mood || null
  };

  try {
    const res = await fetch(`${API_BASE}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();

    showLoading(false);

    if (data.error) {
      showError(data.error);
      return;
    }

    let heading = "";
    if (mode === "random") heading = "Popular right now";
    else if (mode === "mood") heading = `${mood} films`;
    else if (query) heading = `Films like "${query}"`;

    renderResults(data.results, heading);

  } catch (err) {
    showLoading(false);
    showError(`Could not fetch recommendations. ${err.message}`);
  }
}

// ─── Setup Event Listeners ───────────────────────────────────────────────────
function setup() {
  renderQuickPicks();

  // Step 1 — Industry selection
  document.querySelectorAll(".industry-btn").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll(".industry-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedIndustry = btn.dataset.value;
    };
  });

  $("to-step-query").onclick = () => showStep("query");

  // Step 2 — Direct search
  $("search-btn").onclick = () => {
    const q = $("query-input").value.trim();
    if (!q) return;
    doSearch("direct", q);
  };

  $("query-input").onkeydown = (e) => {
    if (e.key === "Enter") {
      const q = $("query-input").value.trim();
      if (q) doSearch("direct", q);
    }
  };

  // Step 2 — Branch buttons
  $("btn-not-sure").onclick = () => showStep("fallback");
  $("btn-random").onclick = () => doSearch("random");

  // Step 3 — Fallback search
  $("fallback-btn").onclick = () => {
    const q = $("fallback-input").value.trim();
    if (!q) return;
    doSearch("fallback", q);
  };

  $("fallback-input").onkeydown = (e) => {
    if (e.key === "Enter") {
      const q = $("fallback-input").value.trim();
      if (q) doSearch("fallback", q);
    }
  };

  // Step 3 → Step 4
  $("btn-show-mood").onclick = () => showStep("mood");
  $("back-to-query").onclick = () => showStep("query");

  // Step 4 — Mood chips
  document.querySelectorAll(".mood-btn").forEach(btn => {
    btn.onclick = () => doSearch("mood", null, btn.dataset.mood);
  });

  $("back-to-fallback").onclick = () => showStep("fallback");

  // Results — go back
  $("back-to-main").onclick = () => showStep("query");
}

window.addEventListener("DOMContentLoaded", setup);
