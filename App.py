import random
import streamlit as st
import requests

from recommender import (
    fetch_full_movie,
    fetch_trending,
    get_recommendations,
    search_movie_tmdb,
    search_movies_for_display,
    TMDB_API_KEY,
)

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="CineMatch • Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== NETFLIX-STYLE CSS =====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0d0d0d !important;
        color: #e8e8e8 !important;
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    section[data-testid="stSidebar"] {
        background: #111111 !important;
        border-right: 1px solid #222 !important;
    }
    section[data-testid="stSidebar"] * { color: #ccc !important; }
    section[data-testid="stSidebar"] label {
        color: #aaa !important; font-size: 0.78rem;
        letter-spacing: 0.06em; text-transform: uppercase;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] {
        background: #1a1a1a !important; border: 1px solid #333 !important; border-radius: 6px !important;
    }
    section[data-testid="stSidebar"] input {
        background: #1a1a1a !important; border: 1px solid #333 !important;
        color: #eee !important; border-radius: 6px !important;
    }
    .cinematic-title {
        font-family: 'Bebas Neue', cursive;
        font-size: clamp(2.8rem, 6vw, 5rem);
        letter-spacing: 0.08em;
        background: linear-gradient(135deg, #e50914 0%, #ff6b35 50%, #ffffff 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
        line-height: 1; margin-bottom: 0;
    }
    .cinematic-sub {
        font-size: 0.85rem; color: #555; letter-spacing: 0.15em;
        text-transform: uppercase; margin-top: 0.3rem; margin-bottom: 2rem;
    }
    [data-testid="stTabs"] [role="tablist"] { background: transparent !important; border-bottom: 1px solid #222 !important; }
    [data-testid="stTabs"] [role="tab"] {
        color: #666 !important; font-size: 0.78rem !important; letter-spacing: 0.1em !important;
        text-transform: uppercase !important; font-weight: 700 !important;
        padding: 0.6rem 1.4rem !important; border-radius: 0 !important;
        border-bottom: 2px solid transparent !important; transition: all 0.2s;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #e50914 !important; border-bottom: 2px solid #e50914 !important; background: transparent !important;
    }
    [data-testid="stTabs"] [role="tab"]:hover { color: #fff !important; background: transparent !important; }
    .movie-grid-card {
        background: #161616; border-radius: 10px; overflow: hidden; position: relative;
        cursor: pointer; transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid #1f1f1f; margin-bottom: 4px;
    }
    .movie-grid-card:hover {
        transform: scale(1.04) translateY(-4px);
        box-shadow: 0 20px 50px rgba(229,9,20,0.2), 0 8px 20px rgba(0,0,0,0.6);
        border-color: #e50914; z-index: 10;
    }
    .movie-card-poster { width: 100%; aspect-ratio: 2/3; object-fit: cover; display: block; }
    .movie-card-no-poster {
        width: 100%; aspect-ratio: 2/3;
        background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
        display: flex; align-items: center; justify-content: center; font-size: 3rem;
    }
    .movie-card-overlay {
        position: absolute; bottom: 0; left: 0; right: 0;
        background: linear-gradient(transparent 0%, rgba(0,0,0,0.95) 60%);
        padding: 40px 12px 14px; transform: translateY(100%); transition: transform 0.35s ease;
    }
    .movie-grid-card:hover .movie-card-overlay { transform: translateY(0); }
    .movie-card-rating {
        display: inline-block; background: rgba(229,9,20,0.85); color: #fff;
        font-size: 0.65rem; font-weight: 700; padding: 2px 7px; border-radius: 4px;
    }
    .movie-card-genres { font-size: 0.65rem; color: #aaa; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .movie-card-static { padding: 10px 12px 12px; background: #161616; }
    .movie-card-static-title { font-size: 0.78rem; font-weight: 600; color: #ddd; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .movie-card-static-year { font-size: 0.68rem; color: #555; }
    .section-header {
        font-family: 'Inter', sans-serif; font-size: 1.05rem; font-weight: 700; color: #fff;
        letter-spacing: 0.04em; text-transform: uppercase; border-left: 3px solid #e50914;
        padding-left: 10px; margin: 2rem 0 1rem;
    }
    .featured-banner {
        width: 100%; border-radius: 14px; overflow: hidden; position: relative;
        margin-bottom: 2.5rem; background: linear-gradient(135deg, #0d0d0d 0%, #1a0000 100%);
        border: 1px solid #2a1a1a; padding: 2.5rem; min-height: 180px;
    }
    .featured-badge {
        display: inline-block; background: #e50914; color: #fff; font-size: 0.65rem;
        font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase;
        padding: 3px 10px; border-radius: 4px; margin-bottom: 10px;
    }
    .featured-title {
        font-family: 'Bebas Neue', cursive; font-size: clamp(1.8rem, 4vw, 3rem);
        color: #fff; letter-spacing: 0.05em; line-height: 1; margin: 6px 0;
    }
    .featured-meta { font-size: 0.8rem; color: #888; margin-top: 6px; }
    .stButton > button {
        background: #e50914 !important; color: #fff !important; border: none !important;
        border-radius: 6px !important; font-size: 0.72rem !important; font-weight: 700 !important;
        letter-spacing: 0.05em !important; text-transform: uppercase !important;
        padding: 0.4rem 0 !important; transition: all 0.2s !important;
        width: 100% !important; min-width: 0 !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }
    .stButton > button:hover {
        background: #ff1a1a !important; transform: scale(1.03) !important;
        box-shadow: 0 4px 18px rgba(229,9,20,0.4) !important;
    }
    .stButton > button:disabled { background: #2a2a2a !important; color: #555 !important; transform: none !important; box-shadow: none !important; }
    section[data-testid="stSidebar"] .stButton > button { background: transparent !important; border: 1px solid #e50914 !important; color: #e50914 !important; width: 100% !important; }
    section[data-testid="stSidebar"] .stButton > button:hover { background: #e50914 !important; color: #fff !important; }
    [data-testid="stExpander"] { background: #1a1a1a !important; border: 1px solid #252525 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] summary { color: #888 !important; font-size: 0.78rem !important; }
    [data-testid="stTextInput"] input { background: #1a1a1a !important; border: 1px solid #333 !important; color: #eee !important; border-radius: 6px !important; }
    [data-testid="stTextInput"] input:focus { border-color: #e50914 !important; box-shadow: 0 0 0 2px rgba(229,9,20,0.2) !important; }
    [data-testid="stAlert"] { background: #1a1a1a !important; border: 1px solid #2a2a2a !important; border-radius: 8px !important; color: #ccc !important; }
    hr { border-color: #1e1e1e !important; }
    .stCaption, small { color: #555 !important; }
    [data-testid="stToast"] { background: #1f1f1f !important; border: 1px solid #333 !important; border-radius: 10px !important; color: #eee !important; }
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #111; }
    ::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #e50914; }
</style>
""", unsafe_allow_html=True)


# ===================== SESSION STATE =====================
for _k, _v in [("current_movie_title", None), ("current_movie_id", None), ("watchlist", [])]:
    if _k not in st.session_state:
        st.session_state[_k] = _v


def set_current_movie(title, tmdb_id=None):
    st.session_state.current_movie_title = title
    st.session_state.current_movie_id = tmdb_id


def add_to_watchlist(movie):
    ids = [w["id"] for w in st.session_state.watchlist]
    if movie.get("id") not in ids:
        st.session_state.watchlist.append({
            "id": movie.get("id", ""), "title": movie.get("title", "Unknown"),
            "poster": movie.get("poster"), "year": movie.get("year", "N/A"),
            "rating": movie.get("rating", "N/A"),
        })
        st.toast(f"📌 Added **{movie['title']}** to watchlist!", icon="✅")


def render_card_grid(movies, key_prefix, cols_per_row=5):
    for i in range(0, len(movies), cols_per_row):
        row = movies[i:i + cols_per_row]
        cols = st.columns(len(row))
        for j, movie in enumerate(row):
            with cols[j]:
                poster_html = (
                    f'<img class="movie-card-poster" src="{movie["poster"]}" loading="lazy"/>'
                    if movie.get("poster") else '<div class="movie-card-no-poster">🎬</div>'
                )
                dir_txt = f'• {movie["director"]}' if movie.get("director") and movie["director"] != "N/A" else ""
                st.markdown(f"""
                <div class="movie-grid-card">
                    {poster_html}
                    <div class="movie-card-overlay">
                        <span class="movie-card-rating">⭐ {movie.get("rating","N/A")}</span>
                        <div class="movie-card-genres">{movie.get("genres","")}</div>
                    </div>
                    <div class="movie-card-static">
                        <div class="movie-card-static-title" title="{movie['title']}">{movie['title']}</div>
                        <div class="movie-card-static-year">{movie.get("year","")} {dir_txt}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown('<div style="display:flex;gap:4px;width:100%;">', unsafe_allow_html=True)
                b1, b2 = st.columns([1, 1])
                with b1:
                    if st.button("Similar", key=f"{key_prefix}_sim_{i+j}", use_container_width=True):
                        set_current_movie(movie["title"], int(movie.get("id", 0)) or None)
                        st.rerun()
                with b2:
                    in_wl = movie.get("id") in [w["id"] for w in st.session_state.watchlist]
                    if st.button("✓ Saved" if in_wl else "+ Save", key=f"{key_prefix}_wl_{i+j}", disabled=in_wl, use_container_width=True):
                        add_to_watchlist(movie)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)


# ===================== HEADER =====================
st.markdown('<div class="cinematic-title">CineMatch</div>', unsafe_allow_html=True)
st.markdown('<div class="cinematic-sub">One search. Endless movies. &nbsp;•&nbsp; Discover what to watch next.</div>', unsafe_allow_html=True)

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("### 🎛️ Controls")
    search_term = st.text_input("Search movies", placeholder="Type any movie title…", key="sidebar_search")

    sidebar_results = []
    movie_options = []
    movie_ids = []
    if search_term and len(search_term.strip()) > 1:
        sidebar_results = search_movie_tmdb(search_term)
        movie_options = [f"{m['title']} ({(m.get('release_date','') or '')[:4]})" for m in sidebar_results[:20]]
        movie_ids = [m["id"] for m in sidebar_results[:20]]

    if movie_options:
        chosen_label = st.selectbox("Select a movie", options=movie_options, key="movie_selector")
        chosen_idx = movie_options.index(chosen_label)
        if st.button("🎯 Get Recommendations"):
            set_current_movie(sidebar_results[chosen_idx]["title"], sidebar_results[chosen_idx]["id"])
            st.rerun()
    elif search_term:
        st.caption("No results found.")

    no_of_reco = st.slider("Recommendations", 5, 20, 10)
    st.markdown("---")
    st.markdown("#### ⚙️ Sort & Filter")
    sort_by = st.selectbox("Sort by", ["Similarity", "Rating ↓", "Year (Newest)"])
    genre_filter = st.multiselect("Genre filter", [
        "Action", "Adventure", "Animation", "Comedy", "Crime",
        "Drama", "Fantasy", "Horror", "Mystery", "Romance",
        "Science Fiction", "Thriller", "War", "Western"
    ])
    min_rating = st.slider("Minimum Rating ⭐", 0.0, 10.0, 0.0, step=0.5)
    st.markdown("---")
    st.markdown("<div style='width:100%'>", unsafe_allow_html=True)
    if st.button("🎲 Surprise Me!", use_container_width=True):
        import random as _r
        pop = requests.get("https://api.themoviedb.org/3/movie/popular",
                           params={"api_key": TMDB_API_KEY, "page": _r.randint(1, 10)},
                           timeout=6).json().get("results", [])
        if pop:
            pick = _r.choice(pop)
            set_current_movie(pick["title"], pick["id"])
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    if st.session_state.watchlist:
        st.markdown(f"📋 **Watchlist:** {len(st.session_state.watchlist)} movies")


# ===================== TABS =====================
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Recommendations", "🔥 Trending Now", "🔍 Discover", "📋 Watchlist"])

# ── TAB 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    if st.session_state.current_movie_title:
        title = st.session_state.current_movie_title
        mid   = st.session_state.current_movie_id
        seed  = fetch_full_movie(mid) if mid else {}

        feat_title   = seed.get("title", title)
        feat_rating  = seed.get("rating", "N/A")
        feat_year    = seed.get("year", "N/A")
        feat_runtime = seed.get("runtime", "N/A")
        feat_dir     = seed.get("director", "N/A")
        feat_genres  = seed.get("genres", "N/A")
        feat_story   = seed.get("overview", "")
        feat_poster  = seed.get("poster", "")

        b_col, p_col = st.columns([3, 1])
        with b_col:
            st.markdown(f"""
            <div class="featured-banner">
                <div class="featured-badge">Now Exploring</div>
                <div class="featured-title">{feat_title}</div>
                <div class="featured-meta">
                    ⭐ {feat_rating} &nbsp;•&nbsp; {feat_year} &nbsp;•&nbsp; {feat_runtime}<br>
                    🎬 {feat_dir} &nbsp;•&nbsp; {feat_genres}
                </div>
                <div style="margin-top:10px;font-size:0.82rem;color:#777;max-width:640px;line-height:1.6;">
                    {feat_story[:240] + "…" if len(feat_story) > 240 else feat_story}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with p_col:
            if feat_poster:
                st.image(feat_poster, width=300)

        with st.spinner(f"Finding movies similar to **{feat_title}**…"):
            recos = get_recommendations(title, n=no_of_reco + 5)

        if genre_filter:
            recos = [r for r in recos if any(g in r.get("genres", "") for g in genre_filter)]
        if min_rating > 0:
            recos = [r for r in recos if float(r.get("rating","0/10").split("/")[0]) >= min_rating]
        if sort_by == "Rating ↓":
            recos.sort(key=lambda x: float(x["rating"].split("/")[0]) if x.get("rating","N/A") != "N/A" else 0, reverse=True)
        elif sort_by == "Year (Newest)":
            recos.sort(key=lambda x: int(x["year"]) if x.get("year","N/A") not in ("N/A","") else 0, reverse=True)

        recos = recos[:no_of_reco]
        st.markdown(f'<div class="section-header">Because you liked {feat_title}</div>', unsafe_allow_html=True)
        st.caption(f"{len(recos)} recommendations • {sort_by}")

        if recos:
            render_card_grid(recos, key_prefix="reco", cols_per_row=5)
        else:
            st.warning("No movies matched your filters.")
    else:
        st.markdown("""
        <div style="text-align:center;padding:5rem 2rem;">
            <div style="font-size:4rem;margin-bottom:1.2rem;">🎬</div>
            <div style="font-family:'Bebas Neue',cursive;font-size:2.5rem;color:#fff;letter-spacing:0.1em;">Welcome to CineMatch</div>
            <div style="color:#555;margin-top:0.8rem;font-size:0.9rem;line-height:1.8;">
                Search any movie in the sidebar and click <strong style="color:#e50914;">Get Recommendations</strong>.<br>
                Or hit <strong style="color:#e50914;">Surprise Me!</strong> to discover something new.<br><br>
                <span style="font-size:0.75rem;color:#3a3a3a;">Search any movie from TMDb's library of 900,000+ titles.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 2 ─────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">🔥 Trending This Week</div>', unsafe_allow_html=True)
    with st.spinner("Loading trending movies…"):
        trending = fetch_trending(16)
    if trending:
        render_card_grid(trending, key_prefix="trend", cols_per_row=4)
    else:
        st.error("Could not load trending movies. Check your internet connection.")

# ── TAB 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">🔍 Search Any Movie</div>', unsafe_allow_html=True)
    query = st.text_input("", placeholder="Search TMDb — any movie, any language, any year…", key="discover_search")
    if query and len(query.strip()) > 1:
        with st.spinner("Searching…"):
            disc_results = search_movies_for_display(query, n=12)
        if disc_results:
            st.caption(f"{len(disc_results)} results for **{query}**")
            render_card_grid(disc_results, key_prefix="disc", cols_per_row=4)
        else:
            st.warning(f'No results found for "{query}".')

# ── TAB 4 ─────────────────────────────────────────────────────────────────────
with tab4:
    wl = st.session_state.watchlist
    count = len(wl)
    st.markdown(f'<div class="section-header">📋 My Watchlist — {count} movie{"s" if count != 1 else ""}</div>', unsafe_allow_html=True)

    if not wl:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#444;">
            <div style="font-size:2.5rem;">📭</div>
            <div style="margin-top:0.8rem;font-size:0.9rem;">Your watchlist is empty.<br>Browse and save movies from any tab.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        poster_cols = st.columns(min(count, 8))
        for i, w in enumerate(wl[:8]):
            with poster_cols[i]:
                if w.get("poster"):
                    st.image(w["poster"], width=120)
                st.caption(w["title"][:18] + ("…" if len(w["title"]) > 18 else ""))

        st.markdown("<br>", unsafe_allow_html=True)

        for idx, w in enumerate(wl.copy()):
            c1, c2, c3, c4 = st.columns([5, 1, 1, 1])
            with c1:
                st.markdown(f"🎬 **{w['title']}** &nbsp; <span style='color:#555;font-size:0.8rem'>{w.get('year','')}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='color:#e50914;font-size:0.8rem;font-weight:700;'>⭐ {w.get('rating','N/A')}</span>", unsafe_allow_html=True)
            with c3:
                if st.button("▶ Trailer", key=f"wl_trailer_{idx}"):
                    trailer_key = st.session_state.get(f"trailer_{w['id']}")
                    if not trailer_key:
                        try:
                            vid_data = requests.get(
                                f"https://api.themoviedb.org/3/movie/{w['id']}/videos",
                                params={"api_key": TMDB_API_KEY}, timeout=6
                            ).json()
                            trailers = [v for v in vid_data.get("results", [])
                                        if v.get("type") == "Trailer" and v.get("site") == "YouTube"]
                            trailer_key = trailers[0]["key"] if trailers else "none"
                        except Exception:
                            trailer_key = "none"
                        st.session_state[f"trailer_{w['id']}"] = trailer_key
                    current = st.session_state.get(f"show_trailer_{w['id']}", False)
                    st.session_state[f"show_trailer_{w['id']}"] = not current
                    st.rerun()
            with c4:
                if st.button("✕", key=f"wl_rm_{idx}"):
                    st.session_state.watchlist.remove(w)
                    st.rerun()

            trailer_key = st.session_state.get(f"trailer_{w['id']}")
            show_trailer = st.session_state.get(f"show_trailer_{w['id']}", False)
            if show_trailer and trailer_key and trailer_key != "none":
                st.markdown(
                    f'<iframe width="100%" height="315" src="https://www.youtube.com/embed/{trailer_key}?autoplay=1" '
                    f'frameborder="0" allow="autoplay; encrypted-media" allowfullscreen style="border-radius:10px;margin:8px 0;"></iframe>',
                    unsafe_allow_html=True
                )
            elif show_trailer and (not trailer_key or trailer_key == "none"):
                st.caption("⚠️ No trailer available for this movie.")
            st.markdown("<hr style='margin:4px 0;border-color:#1a1a1a;'>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Watchlist"):
            st.session_state.watchlist = []
            st.rerun()

# ===================== FOOTER =====================
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#2a2a2a;font-size:0.72rem;letter-spacing:0.12em;text-transform:uppercase;'>"
    "CineMatch &nbsp;•&nbsp; Your Movie Universe &nbsp;•&nbsp; Powered by TMDb"
    "</p>",
    unsafe_allow_html=True
)