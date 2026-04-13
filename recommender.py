"""
recommender.py
==============
Lightweight movie recommendation engine — zero PyTorch, zero ChromaDB.

Stack:
  - TMDb API          → live movie metadata
  - scikit-learn      → TF-IDF vectorizer + cosine similarity
  - Pure Python cache → no SQLite, no DLL issues
"""

import os
import pickle
import requests
import numpy as np
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w500"
CACHE_FILE   = "./movie_cache.pkl"

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
    _vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=15000, sublinear_tf=True)
    _matrix = _vectorizer.fit_transform(docs)

_load_cache()
_rebuild_matrix()


def _tmdb_get(path: str, **params) -> dict:
    try:
        r = requests.get(f"{TMDB_BASE}/{path}", params={"api_key": TMDB_API_KEY, **params}, timeout=8)
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

def _bootstrap_collection(n: int = 60) -> None:
    ids_seen = set(); added = False
    for endpoint in ["movie/popular", "movie/top_rated", "movie/now_playing"]:
        for m in _tmdb_get(endpoint, page=1).get("results", []):
            if len(ids_seen) >= n: break
            mid = m.get("id")
            if mid and mid not in ids_seen:
                ids_seen.add(mid)
                movie = fetch_full_movie(mid)
                if movie and _add_movie_to_store(movie):
                    added = True
        if len(ids_seen) >= n: break
    if added:
        _rebuild_matrix(); _save_cache()

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
    sim_scores    = cosine_similarity(_matrix[seed_idx], _matrix).flatten()
    ranked_indices = np.argsort(sim_scores)[::-1]
    recommendations = []
    for idx in ranked_indices:
        mid = _matrix_ids[idx]
        if mid == seed_id: continue
        full = fetch_full_movie(int(mid))
        if full: recommendations.append(full)
        elif _movie_store.get(mid, {}).get("movie"): recommendations.append(_movie_store[mid]["movie"])
        if len(recommendations) >= n: break
    return recommendations

def fetch_trending(n: int = 16) -> list:
    data = _tmdb_get("trending/movie/week")
    movies = []
    for m in data.get("results", [])[:n]:
        poster_path = m.get("poster_path")
        movies.append({"id": str(m.get("id","")), "title": m.get("title","Unknown"),
            "year": (m.get("release_date","") or "")[:4],
            "rating": f"{m.get('vote_average',0):.1f}/10",
            "poster": f"{TMDB_IMG}{poster_path}" if poster_path else None, "genres": "N/A"})
    return movies

def search_movies_for_display(query: str, n: int = 12) -> list:
    results = search_movie_tmdb(query)
    movies  = []
    for m in results[:n]:
        poster_path = m.get("poster_path")
        movies.append({"id": str(m.get("id","")), "title": m.get("title","Unknown"),
            "year": (m.get("release_date","") or "")[:4],
            "rating": f"{m.get('vote_average',0):.1f}/10",
            "poster": f"{TMDB_IMG}{poster_path}" if poster_path else None, "genres": "N/A"})
    return movies