from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import requests
from typing import List, Optional

load_dotenv()

app = FastAPI(title="MoodFilms API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Keys ────────────────────────────────────────────────────────────────
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "ENTER_YOUR_TMDB_API_KEY_HERE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "ENTER_YOUR_GEMINI_API_KEY_HERE")

# ─── TMDB Endpoints ──────────────────────────────────────────────────────────
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# ─── Gemini system prompt ─────────────────────────────────────────────────────
GEMINI_SYSTEM = """You are a strict movie recommendation assistant. Your ONLY job is to extract or suggest movie titles.

Rules:
- Only respond to movie-related queries.
- If the user asks about anything unrelated to movies (politics, coding, weather, personal questions, etc.), respond with exactly: {"movies": [], "error": "off_topic"}
- Extract movie titles from the user's message, or suggest similar movies if they mention one.
- Always return ONLY a valid JSON object with this shape: {"movies": ["Title1", "Title2", "Title3"]}
- No explanation. No markdown. No extra text. Just the JSON.
"""

# ─── Industry → TMDB language/region mapping ─────────────────────────────────
INDUSTRY_MAP = {
    "Hollywood": {"language": "en", "region": "US"},
    "Bollywood": {"language": "hi", "region": "IN"},
    "Other": {"language": None, "region": None},
}

# ─── Mood → TMDB genre mapping ────────────────────────────────────────────────
MOOD_GENRE_MAP = {
    "Melancholic": "18",
    "Thrilled": "28",
    "Adventurous": "12",
    "Thoughtful": "99",
    "Romantic": "10749",
    "Funny": "35",
}


# ─── Pydantic Models ──────────────────────────────────────────────────────────
class RecommendRequest(BaseModel):
    mode: str
    industry: str = "Hollywood"
    query: Optional[str] = None
    mood: Optional[str] = None


# ─── Helpers ──────────────────────────────────────────────────────────────────
def build_movie_payload(movie: dict) -> dict:
    return {
        "title": movie.get("title", "Unknown"),
        "overview": movie.get("overview", ""),
        "poster": TMDB_IMAGE_BASE + movie["poster_path"] if movie.get("poster_path") else None,
        "tmdb_rating": round(float(movie.get("vote_average", 0)), 1),
        "year": (movie.get("release_date") or "")[:4],
    }


def tmdb_get(path: str, params: dict) -> dict:
    if not TMDB_API_KEY or TMDB_API_KEY == "ENTER_YOUR_TMDB_API_KEY_HERE":
        raise RuntimeError("TMDB_API_KEY is not configured.")
    params["api_key"] = TMDB_API_KEY
    resp = requests.get(f"{TMDB_BASE}{path}", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def tmdb_search(title: str, industry: str) -> Optional[dict]:
    industry_cfg = INDUSTRY_MAP.get(industry, {})
    params = {"query": title}
    if industry_cfg.get("language"):
        params["language"] = industry_cfg["language"]
    data = tmdb_get("/search/movie", params)
    results = data.get("results", [])
    return results[0] if results else None


def tmdb_similar(movie_id: int) -> List[dict]:
    data = tmdb_get(f"/movie/{movie_id}/similar", {})
    return data.get("results", [])[:10]


def tmdb_popular(industry: str) -> List[dict]:
    industry_cfg = INDUSTRY_MAP.get(industry, {})
    params = {}
    if industry_cfg.get("language"):
        params["language"] = industry_cfg["language"]
    if industry_cfg.get("region"):
        params["region"] = industry_cfg["region"]
    data = tmdb_get("/movie/popular", params)
    return data.get("results", [])[:10]


def tmdb_by_mood(mood: str, industry: str) -> List[dict]:
    genre_id = MOOD_GENRE_MAP.get(mood)
    industry_cfg = INDUSTRY_MAP.get(industry, {})
    params = {"sort_by": "popularity.desc"}
    if genre_id:
        params["with_genres"] = genre_id
    if industry_cfg.get("language"):
        params["with_original_language"] = industry_cfg["language"]
    data = tmdb_get("/discover/movie", params)
    return data.get("results", [])[:10]


def call_gemini(text: str) -> dict:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "ENTER_YOUR_GEMINI_API_KEY_HERE":
        return {"movies": [text]}

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": GEMINI_SYSTEM + "\n\nUser input: " + text}],
            }
        ],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 256},
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception:
        return {"movies": [text]}


# ─── API Routes (must be defined BEFORE static mount) ────────────────────────
@app.post("/api/recommend")
def recommend(req: RecommendRequest):
    try:
        if req.mode == "random":
            movies = tmdb_popular(req.industry)
            return {"results": [build_movie_payload(m) for m in movies]}

        if req.mode == "mood" and req.mood:
            movies = tmdb_by_mood(req.mood, req.industry)
            return {"results": [build_movie_payload(m) for m in movies]}

        if req.mode in ("direct", "fallback") and req.query:
            gemini_result = call_gemini(req.query)

            if gemini_result.get("error") == "off_topic":
                return {"results": [], "error": "I can only help with movie recommendations."}

            titles = gemini_result.get("movies", [])
            if not titles:
                return {"results": []}

            movie = tmdb_search(titles[0], req.industry)
            if not movie:
                return {"results": []}

            similar = tmdb_similar(movie["id"])
            return {"results": [build_movie_payload(m) for m in similar]}

        return {"results": []}

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}


# ─── Serve frontend (AFTER API routes) ───────────────────────────────────────
FRONTEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
