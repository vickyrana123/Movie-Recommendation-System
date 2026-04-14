"""
recommender.py
==============
Lightweight movie recommendation engine — zero PyTorch, zero ChromaDB.
Optimized for speed: parallel fetching, session caching, reduced API calls.
"""

import os
import time
import pickle
import requests
import numpy as np
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w500"
CACHE_FILE   = "./movie_cache.pkl"

# Persistent HTTP session — reuses connection, much faster than new requests each time
_session = requests.Session()
_session.headers.update({"Accept": "application/json"})

_movie_store: dict = {}
_vectorizer        = None
_matrix            = None
_matrix_ids: list  = []


def _load_cache():
    global _movie_store
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "rb") as f:
                _movie_store = pickle.load(f)
        except Exception:
            _movie_store = {}

def _save_cache():
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(_movie_store, f)
    except Exception:
        pass

def _rebuild_matrix():
    global _vectorizer, _matrix, _matrix_ids
    if not _movie_store:
        _vectorizer = None; _matrix = None; _matrix_ids = []
        return
    _matrix_ids = list(_movie_store.keys())
    docs = [_movie_store[mid]["document"] for mid in _matrix_ids]
    _vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=10000,   # reduced from 15000 → faster rebuild
        sublinear_tf=True
    )
    _matrix = _vectorizer.fit_transform(docs)

_load_cache()
_rebuild_matrix()


# ── TMDb helpers ──────────────────────────────────────────────────────────────
def _tmdb_get(path: str, **params) -> dict:
    try:
        r = _session.get(
            f"{TMDB_BASE}/{path}",
            params={"api_key": TMDB_API_KEY, **params},
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


@lru_cache(maxsize=2048)
def search_movie_tmdb(query: str) -> list:
    data = _tmdb_get("search/movie", query=query)
    return data.get("results", [])


@lru_cache(maxsize=2048)
def fetch_full_movie(movie_id: int) -> dict:
    details = _tmdb_get(f"movie/{movie_id}", append_to_response="credits,keywords")
    if not details:
        return {}
    poster_path  = details.get("poster_path") or details.get("backdrop_path")
    poster       = f"{TMDB_IMG}{poster_path}" if poster_path else None
    release_date = details.get("release_date", "")
    vote_avg     = details.get("vote_average", 0)
    genres       = [g["name"] for g in details.get("genres", [])]
    cast_list    = details.get("credits", {}).get("cast", [])
    crew_list    = details.get("credits", {}).get("crew", [])
    kw_list      = details.get("keywords", {}).get("keywords", [])
    return {
        "id":          str(movie_id),
        "title":       details.get("title", "Unknown"),
        "overview":    details.get("overview", ""),
        "year":        release_date[:4] if release_date else "N/A",
        "runtime":     f"{details.get('runtime')} min" if details.get("runtime") else "N/A",
        "rating":      f"{vote_avg:.1f}/10" if vote_avg else "N/A",
        "popularity":  details.get("popularity", 0),
        "genres":      ", ".join(genres) if genres else "N/A",
        "genres_list": genres,
        "cast":        ", ".join(c["name"] for c in cast_list[:8]),
        "director":    next((c["name"] for c in crew_list if c.get("job") == "Director"), "N/A"),
        "keywords":    " ".join(k["name"] for k in kw_list[:20]),
        "poster":      poster,
    }


def _build_document(movie: dict) -> str:
    genres_boost   = (movie.get("genres",   "") + " ") * 3
    keywords_boost = (movie.get("keywords", "") + " ") * 2
    parts = [genres_boost, keywords_boost,
             f"director {movie.get('director','')}",
             movie.get("cast", ""), movie.get("overview", ""), movie.get("title", "")]
    return " ".join(p for p in parts if p.strip())


def _add_movie_to_store(movie: dict) -> bool:
    mid = movie["id"]
    if mid in _movie_store:
        return False
    _movie_store[mid] = {"movie": movie, "document": _build_document(movie)}
    return True


def _fetch_movie_parallel(movie_id: int) -> dict:
    """Wrapper for parallel fetching — skips already cached."""
    if str(movie_id) in _movie_store:
        return _movie_store[str(movie_id)]["movie"]
    return fetch_full_movie(movie_id)


def _bootstrap_collection(n: int = 60) -> None:
    """Fetch bootstrap movies in parallel for speed."""
    ids_seen = set()
    all_ids  = []

    for endpoint in ["movie/popular", "movie/top_rated", "movie/now_playing"]:
        for m in _tmdb_get(endpoint, page=1).get("results", []):
            if len(ids_seen) >= n: break
            mid = m.get("id")
            if mid and mid not in ids_seen:
                ids_seen.add(mid)
                all_ids.append(mid)
        if len(ids_seen) >= n: break

    # Fetch all in parallel — up to 8 threads
    added = False
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_full_movie, mid): mid for mid in all_ids}
        for future in as_completed(futures):
            movie = future.result()
            if movie and _add_movie_to_store(movie):
                added = True

    if added:
        _rebuild_matrix()
        _save_cache()


def get_recommendations(movie_title: str, n: int = 10) -> list:
    global _vectorizer, _matrix, _matrix_ids

    results = search_movie_tmdb(movie_title)
    if not results: return []

    seed = fetch_full_movie(results[0]["id"])
    if not seed: return []

    seed_id = seed["id"]
    _add_movie_to_store(seed)

    if len(_movie_store) < n + 5:
        _bootstrap_collection(n + 40)
    else:
        _rebuild_matrix()

    if _matrix is None or len(_matrix_ids) < 2: return []
    if seed_id not in _matrix_ids: _rebuild_matrix()

    try:
        seed_idx = _matrix_ids.index(seed_id)
    except ValueError:
        return []

    sim_scores     = cosine_similarity(_matrix[seed_idx], _matrix).flatten()
    ranked_indices = np.argsort(sim_scores)[::-1]

    # Collect top candidate IDs first (exclude seed)
    candidate_ids = []
    for idx in ranked_indices:
        mid = _matrix_ids[idx]
        if mid == seed_id: continue
        candidate_ids.append(mid)
        if len(candidate_ids) >= n + 5: break

    # Fetch all candidates in parallel
    recommendations = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_movie_parallel, int(mid)): mid for mid in candidate_ids}
        results_map = {}
        for future in as_completed(futures):
            mid = futures[future]
            movie = future.result()
            if movie:
                results_map[mid] = movie

    # Preserve similarity order
    for mid in candidate_ids:
        if mid in results_map:
            recommendations.append(results_map[mid])
        elif _movie_store.get(mid, {}).get("movie"):
            recommendations.append(_movie_store[mid]["movie"])
        if len(recommendations) >= n: break

    return recommendations


def fetch_trending(n: int = 16) -> list:
    data = _tmdb_get("trending/movie/week")
    movies = []
    for m in data.get("results", [])[:n]:
        poster_path = m.get("poster_path")
        movies.append({
            "id":     str(m.get("id", "")),
            "title":  m.get("title", "Unknown"),
            "year":   (m.get("release_date", "") or "")[:4],
            "rating": f"{m.get('vote_average', 0):.1f}/10",
            "poster": f"{TMDB_IMG}{poster_path}" if poster_path else None,
            "genres": "N/A",
        })
    return movies


def search_movies_for_display(query: str, n: int = 12) -> list:
    results = search_movie_tmdb(query)
    movies  = []
    for m in results[:n]:
        poster_path = m.get("poster_path")
        movies.append({
            "id":     str(m.get("id", "")),
            "title":  m.get("title", "Unknown"),
            "year":   (m.get("release_date", "") or "")[:4],
            "rating": f"{m.get('vote_average', 0):.1f}/10",
            "poster": f"{TMDB_IMG}{poster_path}" if poster_path else None,
            "genres": "N/A",
        })
    return movies


# ── NEW: Browse by Language / Country ─────────────────────────────────────────

# Supported language codes mapped to display names
LANGUAGE_OPTIONS = {
    "Any":        "",
    "English":    "en",
    "Hindi":      "hi",
    "French":     "fr",
    "Spanish":    "es",
    "Korean":     "ko",
    "Japanese":   "ja",
    "Italian":    "it",
    "German":     "de",
    "Tamil":      "ta",
    "Telugu":     "te",
    "Portuguese": "pt",
    "Chinese":    "zh",
    "Arabic":     "ar",
    "Turkish":    "tr",
    "Russian":    "ru",
}

# TMDb region codes for country filtering
COUNTRY_OPTIONS = {
    "Any":            "",
    "🇺🇸 USA":         "US",
    "🇮🇳 India":       "IN",
    "🇬🇧 UK":          "GB",
    "🇫🇷 France":      "FR",
    "🇩🇪 Germany":     "DE",
    "🇯🇵 Japan":       "JP",
    "🇰🇷 South Korea": "KR",
    "🇮🇹 Italy":       "IT",
    "🇪🇸 Spain":       "ES",
    "🇧🇷 Brazil":      "BR",
    "🇨🇳 China":       "CN",
    "🇲🇽 Mexico":      "MX",
    "🇷🇺 Russia":      "RU",
    "🇦🇺 Australia":   "AU",
    "🇹🇷 Turkey":      "TR",
}

GENRE_ID_MAP = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35,
    "Crime": 80, "Documentary": 99, "Drama": 18, "Family": 10751,
    "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402,
    "Mystery": 9648, "Romance": 10749, "Science Fiction": 878,
    "Thriller": 53, "War": 10752, "Western": 37,
}

SORT_OPTIONS = {
    "Popularity ↓":   "popularity.desc",
    "Rating ↓":       "vote_average.desc",
    "Newest First":   "primary_release_date.desc",
    "Oldest First":   "primary_release_date.asc",
}


def fetch_by_language_country(
    language: str = "",
    region: str = "",
    genre: str = "",
    sort: str = "popularity.desc",
    page: int = 1,
    n: int = 16,
) -> list:
    """
    Discover movies filtered by original language, region, and/or genre.
    Returns a list of lightweight movie dicts (poster, title, year, rating).
    """
    params = {
        "sort_by":               sort,
        "vote_count.gte":        50,    # skip obscure unrated titles
        "page":                  page,
    }
    if language:
        params["with_original_language"] = language
    if region:
        params["region"] = region
    if genre and genre in GENRE_ID_MAP:
        params["with_genres"] = GENRE_ID_MAP[genre]

    data = _tmdb_get("discover/movie", **params)
    movies = []
    for m in data.get("results", [])[:n]:
        poster_path = m.get("poster_path")
        movies.append({
            "id":     str(m.get("id", "")),
            "title":  m.get("title", "Unknown"),
            "year":   (m.get("release_date", "") or "")[:4],
            "rating": f"{m.get('vote_average', 0):.1f}/10",
            "poster": f"{TMDB_IMG}{poster_path}" if poster_path else None,
            "genres": "N/A",
            "overview": m.get("overview", ""),
        })
    return movies


# ── NEW: Release Calendar (Upcoming Movies) ───────────────────────────────────

def fetch_upcoming_movies(region: str = "US", pages: int = 3) -> list:
    """
    Fetch upcoming theatrical releases from TMDb, sorted by release date.
    Returns enriched dicts including release_date for calendar grouping.
    """
    seen = set()
    movies = []

    for page in range(1, pages + 1):
        data = _tmdb_get("movie/upcoming", region=region, page=page)
        for m in data.get("results", []):
            mid = m.get("id")
            release_date = m.get("release_date", "")
            if not release_date or not mid or mid in seen:
                continue
            seen.add(mid)
            poster_path = m.get("poster_path")
            movies.append({
                "id":           str(mid),
                "title":        m.get("title", "Unknown"),
                "release_date": release_date,          # full YYYY-MM-DD
                "year":         release_date[:4],
                "rating":       f"{m.get('vote_average', 0):.1f}/10",
                "poster":       f"{TMDB_IMG}{poster_path}" if poster_path else None,
                "genres":       "N/A",
                "overview":     m.get("overview", ""),
                "popularity":   m.get("popularity", 0),
            })

    # Sort by release date ascending (soonest first)
    movies.sort(key=lambda x: x["release_date"])
    return movies