# 🎬 MoodFilms AI

> An AI-powered movie recommendation engine that understands your mood, not just your genre.

MoodFilms AI takes a conversational input — a feeling, a vibe, a movie you loved — and uses **Google Gemini 1.5 Flash** to extract cinematic intent, then queries the **TMDB API** to return real, poster-rich movie recommendations. Supports Hollywood, Bollywood, and international cinema.

---

## ✦ Features

- **Mood-based discovery** — describe how you feel and get matched films, not just genre filters
- **Conversational fallback** — "Not Sure" mode guides you through mood chips and past favorites
- **Industry filter** — Hollywood, Bollywood, or Other
- **Three query modes** — direct input, random quick picks, or guided conversational flow
- **Cinematic dark-mode UI** — single-page frontend with poster cards and smooth UX
- **Secure backend** — API keys never exposed to the frontend

---

## ⚙️ Architecture

```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────────┐
│    Frontend     │────────▶│   FastAPI Backend     │────────▶│  Google Gemini      │
│  (index.html)   │  Prompt │     (main.py)         │ Context │  1.5 Flash          │
│                 │◀────────│                       │◀────────│  (Intent Extractor) │
└─────────────────┘ Results │  • API key handling   │  Titles └─────────────────────┘
                            │  • Routing & logic    │                   │
                            └──────────────────────┘                   │ Film titles
                                        │                               ▼
                                        │ Dynamic query      ┌─────────────────────┐
                                        └───────────────────▶│     TMDB API        │
                                                             │  (Posters, metadata)│
                                                             └─────────────────────┘
```

**Stack:**
- **Frontend** — HTML, CSS, Vanilla JS (single-page, no framework)
- **Backend** — Python, FastAPI, Uvicorn
- **AI Layer** — Google Gemini 1.5 Flash via REST API
- **Data Layer** — TMDB API v4

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [TMDB API key](https://www.themoviedb.org/settings/api) (free)
- A [Google Gemini API key](https://aistudio.google.com/app/apikey) (free tier available)

### 1. Clone the repository

```bash
git clone https://github.com/ch-yousafali/moodfilms-ai.git
cd moodfilms-ai
```

### 2. Set up the Python environment

```bash
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
TMDB_API_KEY=your_tmdb_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent
```

> **Never commit your `.env` file.** It is already excluded in `.gitignore`.

### 4. Run the backend

```bash
uvicorn backend.main:app --reload
```

Backend runs at `http://localhost:8000`

### 5. Open the frontend

Open `frontend/index.html` directly in your browser, or serve it with a static server:

```bash
npx serve frontend
```

---

## 📡 API Reference

### `POST /api/recommend`

Returns a curated list of movie recommendations based on user input.

**Request body:**
```json
{
  "industry": "Hollywood",
  "query": "something intense and psychological",
  "mood": "anxious",
  "mode": "direct"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `industry` | `string` | `Hollywood`, `Bollywood`, or `Other` |
| `query` | `string` | Free-text user input or mood description |
| `mood` | `string` | Optional mood chip selection |
| `mode` | `string` | `direct`, `random`, or `conversational` |

**Response:**
```json
[
  {
    "title": "Black Swan",
    "year": 2010,
    "poster_url": "https://image.tmdb.org/...",
    "overview": "A ballet dancer...",
    "rating": 7.9
  }
]
```

---

## 📁 Project Structure

```
moodfilms-ai/
├── backend/
│   ├── main.py              # FastAPI app, Gemini integration, TMDB queries
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Single-page UI
│   ├── styles.css           # Dark-mode cinematic styling
│   └── app.js               # Frontend logic, API calls, rendering
├── .env                     # Local secrets (not committed)
├── .gitignore
└── README.md
```

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TMDB_API_KEY` | ✅ | The Movie Database API key |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `GEMINI_API_URL` | ✅ | Gemini endpoint URL |

---

## 🛣️ Roadmap

- [ ] User session memory (remember past picks)
- [ ] Streaming recommendations as Gemini responds
- [ ] Watchlist with local storage
- [ ] Trailer embed via YouTube API
- [ ] Deploy frontend to Vercel + backend to Railway

---

## 👤 Author

**Yousuf Ali**
- GitHub: [@ch-yousafali](https://github.com/ch-yousafali)
- LinkedIn: [linkedin.com/in/yousuf-ali](https://linkedin.com/in/yousuf-ali)

---

## 📄 License

MIT — free to use, modify, and distribute.