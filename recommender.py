"""
recommender.py
==============
Lightweight movie recommendation engine.
Optimized: deduped imports, connection pooling, sparse dot-product similarity,
parallel fetching, shared _parse_movie_row helper, strict upcoming filters.
"""

import os
import pickle
import logging
from datetime import date, datetime
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer

# ── Config ────────────────────────────────────────────────────────────────────

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w500"
CACHE_FILE   = "./movie_cache.pkl"
MAX_WORKERS  = 8

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

# ── Persistent HTTP session with connection pool ──────────────────────────────
_session = requests.Session()
_session.headers.update({"Accept": "application/json"})
_adapter = requests.adapters.HTTPAdapter(
    pool_connections=MAX_WORKERS,
    pool_maxsize=MAX_WORKERS,
    max_retries=1,
)
_session.mount("https://", _adapter)

# ── In-memory store ───────────────────────────────────────────────────────────
_movie_store: dict = {}
_vectorizer        = None
_matrix            = None   # sparse CSR — never densified until scoring
_matrix_ids: list  = []

# ── Constants ─────────────────────────────────────────────────────────────────
LANGUAGE_OPTIONS = {
    "Any": "", "English": "en", "Hindi": "hi", "French": "fr",
    "Spanish": "es", "Korean": "ko", "Japanese": "ja", "Italian": "it",
    "German": "de", "Tamil": "ta", "Telugu": "te", "Portuguese": "pt",
    "Chinese": "zh", "Arabic": "ar", "Turkish": "tr", "Russian": "ru",
}
COUNTRY_OPTIONS = {
    "Any": "",
    "🇺🇸 USA": "US", "🇮🇳 India": "IN", "🇬🇧 UK": "GB",
    "🇫🇷 France": "FR", "🇩🇪 Germany": "DE", "🇯🇵 Japan": "JP",
    "🇰🇷 South Korea": "KR", "🇮🇹 Italy": "IT", "🇪🇸 Spain": "ES",
    "🇧🇷 Brazil": "BR", "🇨🇳 China": "CN", "🇲🇽 Mexico": "MX",
    "🇷🇺 Russia": "RU", "🇦🇺 Australia": "AU", "🇹🇷 Turkey": "TR",
}
GENRE_ID_MAP = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35,
    "Crime": 80, "Documentary": 99, "Drama": 18, "Family": 10751,
    "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402,
    "Mystery": 9648, "Romance": 10749, "Science Fiction": 878,
    "Thriller": 53, "War": 10752, "Western": 37,
}
SORT_OPTIONS = {
    "Popularity ↓":  "popularity.desc",
    "Rating ↓":      "vote_average.desc",
    "Newest First":  "primary_release_date.desc",
    "Oldest First":  "primary_release_date.asc",
}


# ── Cache I/O ─────────────────────────────────────────────────────────────────
def _load_cache() -> None:
    global _movie_store
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "rb") as f:
                _movie_store = pickle.load(f)
        except Exception:
            _movie_store = {}


def _save_cache() -> None:
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(_movie_store, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        log.warning("Cache save failed: %s", e)


# ── TF-IDF matrix ─────────────────────────────────────────────────────────────
def _rebuild_matrix() -> None:
    global _vectorizer, _matrix, _matrix_ids
    if not _movie_store:
        _vectorizer = _matrix = None
        _matrix_ids = []
        return
    _matrix_ids = list(_movie_store.keys())
    docs = [_movie_store[mid]["document"] for mid in _matrix_ids]
    _vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10_000, sublinear_tf=True)
    _matrix = _vectorizer.fit_transform(docs)   # CSR sparse matrix


_load_cache()
_rebuild_matrix()


# ── TMDb GET ──────────────────────────────────────────────────────────────────
def _tmdb_get(path: str, **params) -> dict:
    try:
        r = _session.get(
            f"{TMDB_BASE}/{path}",
            params={"api_key": TMDB_API_KEY, **params},
            timeout=8,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("TMDb [%s] failed: %s", path, e)
        return {}


# ── Shared lightweight parser (avoids repeated code in list fetchers) ─────────
def _parse_movie_row(m: dict) -> dict:
    poster_path = m.get("poster_path")
    return {
        "id":           str(m.get("id", "")),
        "title":        m.get("title", "Unknown"),
        "year":         (m.get("release_date", "") or "")[:4],
        "rating":       f"{m.get('vote_average', 0):.1f}/10",
        "poster":       f"{TMDB_IMG}{poster_path}" if poster_path else None,
        "genres":       "N/A",
        "overview":     m.get("overview", ""),
    }


# ── Search (tuple return keeps lru_cache happy) ───────────────────────────────
@lru_cache(maxsize=512)
def search_movie_tmdb(query: str) -> tuple:
    return tuple(_tmdb_get("search/movie", query=query).get("results", []))


# ── Full movie detail ─────────────────────────────────────────────────────────
@lru_cache(maxsize=2048)
def fetch_full_movie(movie_id: int) -> dict:
    details = _tmdb_get(f"movie/{movie_id}", append_to_response="credits,keywords")
    if not details:
        return {}
    poster_path  = details.get("poster_path") or details.get("backdrop_path")
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
        "runtime":     f"{details['runtime']} min" if details.get("runtime") else "N/A",
        "rating":      f"{vote_avg:.1f}/10" if vote_avg else "N/A",
        "popularity":  details.get("popularity", 0),
        "genres":      ", ".join(genres) or "N/A",
        "genres_list": genres,
        "cast":        ", ".join(c["name"] for c in cast_list[:8]),
        "director":    next((c["name"] for c in crew_list if c.get("job") == "Director"), "N/A"),
        "keywords":    " ".join(k["name"] for k in kw_list[:20]),
        "poster":      f"{TMDB_IMG}{poster_path}" if poster_path else None,
    }


# ── Store helpers ─────────────────────────────────────────────────────────────
def _build_document(movie: dict) -> str:
    parts = [
        (movie.get("genres",   "") + " ") * 3,
        (movie.get("keywords", "") + " ") * 2,
        f"director {movie.get('director', '')}",
        movie.get("cast", ""),
        movie.get("overview", ""),
        movie.get("title", ""),
    ]
    return " ".join(p for p in parts if p.strip())


def _add_movie_to_store(movie: dict) -> bool:
    mid = movie.get("id")
    if not mid or mid in _movie_store:
        return False
    _movie_store[mid] = {"movie": movie, "document": _build_document(movie)}
    return True


# ── Bootstrap ─────────────────────────────────────────────────────────────────
def _bootstrap_collection(n: int = 60) -> None:
    ids_seen: set  = set()
    all_ids: list  = []
    for endpoint in ("movie/popular", "movie/top_rated", "movie/now_playing"):
        if len(ids_seen) >= n:
            break
        for m in _tmdb_get(endpoint, page=1).get("results", []):
            mid = m.get("id")
            if mid and mid not in ids_seen:
                ids_seen.add(mid)
                all_ids.append(mid)
            if len(ids_seen) >= n:
                break

    added = False
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for movie in ex.map(fetch_full_movie, all_ids):
            if movie and _add_movie_to_store(movie):
                added = True
    if added:
        _rebuild_matrix()
        _save_cache()


# ── Recommendation engine ─────────────────────────────────────────────────────
def get_recommendations(movie_title: str, n: int = 10) -> list:
    global _matrix, _matrix_ids

    results = search_movie_tmdb(movie_title)
    if not results:
        return []

    seed = fetch_full_movie(results[0]["id"])
    if not seed:
        return []

    seed_id = seed["id"]
    _add_movie_to_store(seed)

    if len(_movie_store) < n + 5:
        _bootstrap_collection(n + 40)
    else:
        _rebuild_matrix()

    if _matrix is None or len(_matrix_ids) < 2:
        return []
    if seed_id not in _matrix_ids:
        _rebuild_matrix()

    try:
        seed_idx = _matrix_ids.index(seed_id)
    except ValueError:
        return []

    # Sparse dot-product → only densify the single scores vector
    seed_vec   = _matrix[seed_idx]
    dot_scores = (seed_vec @ _matrix.T).toarray().flatten()
    norms      = np.sqrt(np.asarray(_matrix.power(2).sum(axis=1)).flatten())
    seed_norm  = float(np.sqrt(seed_vec.power(2).sum()))
    denom      = norms * seed_norm
    with np.errstate(invalid="ignore", divide="ignore"):
        sim_scores = np.where(denom > 0, dot_scores / denom, 0.0)

    candidate_ids = [
        _matrix_ids[i]
        for i in np.argsort(sim_scores)[::-1]
        if _matrix_ids[i] != seed_id
    ][:n + 5]

    # Only fetch IDs not already in store
    to_fetch = [int(mid) for mid in candidate_ids if mid not in _movie_store]
    fetched: dict = {}
    if to_fetch:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            for mid, movie in zip(to_fetch, ex.map(fetch_full_movie, to_fetch)):
                if movie:
                    fetched[str(mid)] = movie

    recommendations = []
    for mid in candidate_ids:
        movie = fetched.get(mid) or _movie_store.get(mid, {}).get("movie")
        if movie:
            recommendations.append(movie)
        if len(recommendations) >= n:
            break

    return recommendations


# ── List fetchers ─────────────────────────────────────────────────────────────
def fetch_trending(n: int = 16) -> list:
    return [_parse_movie_row(m)
            for m in _tmdb_get("trending/movie/week").get("results", [])[:n]]


def search_movies_for_display(query: str, n: int = 12) -> list:
    return [_parse_movie_row(m) for m in search_movie_tmdb(query)[:n]]


def fetch_by_language_country(
    language: str = "",
    region: str = "",
    genre: str = "",
    sort: str = "popularity.desc",
    page: int = 1,
    n: int = 16,
) -> list:
    params: dict = {"sort_by": sort, "vote_count.gte": 50, "page": page}
    if language:
        params["with_original_language"] = language
    if region:
        params["region"] = region
    if genre and genre in GENRE_ID_MAP:
        params["with_genres"] = GENRE_ID_MAP[genre]
    return [_parse_movie_row(m)
            for m in _tmdb_get("discover/movie", **params).get("results", [])[:n]]


def fetch_upcoming_movies(region: str = "US", pages: int = 3) -> list:
    """Upcoming releases from today, current year only, max 18 months ahead."""
    today     = date.today()
    today_str = today.isoformat()
    cur_year  = today.year
    max_days  = 548  # ~18 months

    seen: set    = set()
    movies: list = []

    for page in range(1, pages + 1):
        for m in _tmdb_get("movie/upcoming", region=region, page=page).get("results", []):
            mid          = m.get("id")
            release_date = m.get("release_date", "")
            if not release_date or len(release_date) < 10 or not mid or mid in seen:
                continue
            try:
                rel_year = int(release_date[:4])
                rel_dt   = datetime.strptime(release_date, "%Y-%m-%d").date()
            except ValueError:
                continue
            if rel_year < cur_year or (rel_dt - today).days > max_days:
                continue
            seen.add(mid)
            row = _parse_movie_row(m)
            row["release_date"] = release_date
            row["popularity"]   = m.get("popularity", 0)
            movies.append(row)

    movies.sort(key=lambda x: x["release_date"])
    return movies