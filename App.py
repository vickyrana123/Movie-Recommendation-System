"""
App.py  —  CineMatch Streamlit frontend
Optimizations: st.cache_data for API calls, _wl_ids set for O(1) lookups,
pre-computed genre HTML, no redundant markdown wrappers, deduped column logic.
"""

import streamlit as st
import requests
from datetime import datetime, date

from recommender import (
    fetch_full_movie, fetch_trending, get_recommendations,
    search_movie_tmdb, search_movies_for_display,
    fetch_by_language_country, fetch_upcoming_movies,
    LANGUAGE_OPTIONS, COUNTRY_OPTIONS, GENRE_ID_MAP, SORT_OPTIONS, TMDB_API_KEY,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CineMatch • Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (injected once, never re-rendered) ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[data-testid="stAppViewContainer"]{background:#0d0d0d!important;color:#e8e8e8!important;font-family:'Inter',sans-serif}
[data-testid="stHeader"]{background:transparent!important}
.block-container{padding-top:1rem!important;padding-bottom:2rem!important;max-width:100%!important}
section[data-testid="stSidebar"]{background:#111!important;border-right:1px solid #222!important}
section[data-testid="stSidebar"] *{color:#ccc!important}
section[data-testid="stSidebar"] label{color:#aaa!important;font-size:.78rem;letter-spacing:.06em;text-transform:uppercase}
section[data-testid="stSidebar"] [data-baseweb="select"]{background:#1a1a1a!important;border:1px solid #333!important;border-radius:6px!important}
section[data-testid="stSidebar"] input{background:#1a1a1a!important;border:1px solid #333!important;color:#eee!important;border-radius:6px!important}
.cinematic-title{font-family:'Bebas Neue',cursive;font-size:clamp(2.8rem,6vw,5rem);letter-spacing:.08em;background:linear-gradient(135deg,#e50914,#ff6b35 50%,#fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1;margin-bottom:0}
.cinematic-sub{font-size:.85rem;color:#555;letter-spacing:.15em;text-transform:uppercase;margin-top:.3rem;margin-bottom:2rem}
[data-testid="stTabs"] [role="tablist"]{background:transparent!important;border-bottom:1px solid #222!important}
[data-testid="stTabs"] [role="tab"]{color:#666!important;font-size:.78rem!important;letter-spacing:.1em!important;text-transform:uppercase!important;font-weight:700!important;padding:.6rem 1.4rem!important;border-radius:0!important;border-bottom:2px solid transparent!important;transition:all .2s}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#e50914!important;border-bottom:2px solid #e50914!important;background:transparent!important}
[data-testid="stTabs"] [role="tab"]:hover{color:#fff!important;background:transparent!important}
.movie-grid-card{background:#161616;border-radius:10px;overflow:hidden;position:relative;cursor:pointer;transition:transform .3s,box-shadow .3s;border:1px solid #1f1f1f;margin-bottom:4px}
.movie-grid-card:hover{transform:scale(1.04) translateY(-4px);box-shadow:0 20px 50px rgba(229,9,20,.2),0 8px 20px rgba(0,0,0,.6);border-color:#e50914;z-index:10}
.movie-card-poster{width:100%;aspect-ratio:2/3;object-fit:cover;display:block}
.movie-card-no-poster{width:100%;aspect-ratio:2/3;background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);display:flex;align-items:center;justify-content:center;font-size:3rem}
.movie-card-overlay{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(0,0,0,.95) 60%);padding:40px 12px 14px;transform:translateY(100%);transition:transform .35s}
.movie-grid-card:hover .movie-card-overlay{transform:translateY(0)}
.movie-card-rating{display:inline-block;background:rgba(229,9,20,.85);color:#fff;font-size:.65rem;font-weight:700;padding:2px 7px;border-radius:4px}
.movie-card-genres{font-size:.65rem;color:#aaa;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.movie-card-static{padding:10px 12px 12px;background:#161616}
.movie-card-static-title{font-size:.78rem;font-weight:600;color:#ddd;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.movie-card-static-year{font-size:.68rem;color:#555}
.section-header{font-family:'Inter',sans-serif;font-size:1.05rem;font-weight:700;color:#fff;letter-spacing:.04em;text-transform:uppercase;border-left:3px solid #e50914;padding-left:10px;margin:2rem 0 1rem}
.featured-banner{width:100%;border-radius:14px;overflow:hidden;position:relative;margin-bottom:2.5rem;background:linear-gradient(135deg,#0d0d0d,#1a0000);border:1px solid #2a1a1a;padding:2.5rem;min-height:180px}
.featured-badge{display:inline-block;background:#e50914;color:#fff;font-size:.65rem;font-weight:800;letter-spacing:.15em;text-transform:uppercase;padding:3px 10px;border-radius:4px;margin-bottom:10px}
.featured-title{font-family:'Bebas Neue',cursive;font-size:clamp(1.8rem,4vw,3rem);color:#fff;letter-spacing:.05em;line-height:1;margin:6px 0}
.stButton>button{background:#e50914!important;color:#fff!important;border:none!important;border-radius:6px!important;font-size:.72rem!important;font-weight:700!important;letter-spacing:.05em!important;text-transform:uppercase!important;padding:.4rem 0!important;transition:all .2s!important;width:100%!important;min-width:0!important;display:flex!important;align-items:center!important;justify-content:center!important}
.stButton>button:hover{background:#ff1a1a!important;transform:scale(1.03)!important;box-shadow:0 4px 18px rgba(229,9,20,.4)!important}
.stButton>button:disabled{background:#2a2a2a!important;color:#555!important;transform:none!important;box-shadow:none!important}
section[data-testid="stSidebar"] .stButton>button{background:transparent!important;border:1px solid #e50914!important;color:#e50914!important;width:100%!important;padding:.6rem 1rem!important;height:auto!important}
section[data-testid="stSidebar"] .stButton>button:hover{background:#e50914!important;color:#fff!important}
[data-testid="stExpander"]{background:#1a1a1a!important;border:1px solid #252525!important;border-radius:8px!important}
[data-testid="stExpander"] summary{color:#888!important;font-size:.78rem!important}
[data-testid="stTextInput"] input{background:#1a1a1a!important;border:1px solid #333!important;color:#eee!important;border-radius:6px!important}
[data-testid="stTextInput"] input:focus{border-color:#e50914!important;box-shadow:0 0 0 2px rgba(229,9,20,.2)!important}
[data-testid="stAlert"]{background:#1a1a1a!important;border:1px solid #2a2a2a!important;border-radius:8px!important;color:#ccc!important}
hr{border-color:#1e1e1e!important}
.stCaption,small{color:#555!important}
[data-testid="stToast"]{background:#1f1f1f!important;border:1px solid #333!important;border-radius:10px!important;color:#eee!important}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:#111}
::-webkit-scrollbar-thumb{background:#2a2a2a;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#e50914}
[data-testid="stHorizontalBlock"] .stButton>button{min-width:0!important;width:100%!important;height:40px!important;line-height:1!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;padding:.5rem 1rem!important;display:flex!important;align-items:center!important;justify-content:center!important;font-size:.75rem!important;letter-spacing:.06em!important}
.cal-month-header{font-family:'Bebas Neue',cursive;font-size:2rem;color:#e50914;letter-spacing:.14em;border-bottom:2px solid #2a2a2a;padding-bottom:8px;margin:2.5rem 0 1.2rem}
.cal-card{display:flex;gap:20px;align-items:flex-start;background:#161616;border:1px solid #1f1f1f;border-radius:14px;padding:20px;margin-bottom:16px;transition:border-color .25s,box-shadow .25s,transform .2s}
.cal-card:hover{border-color:#e50914;box-shadow:0 8px 32px rgba(229,9,20,.18),0 2px 8px rgba(0,0,0,.5);transform:translateY(-2px)}
.cal-date-box{min-width:68px;background:linear-gradient(135deg,#e50914,#c0000f);border-radius:12px;text-align:center;padding:10px 8px;flex-shrink:0;box-shadow:0 4px 14px rgba(229,9,20,.35)}
.cal-date-day{font-family:'Bebas Neue',cursive;font-size:2.4rem;color:#fff;line-height:1}
.cal-date-mon{font-size:.78rem;font-weight:800;color:rgba(255,255,255,.85);letter-spacing:.14em;text-transform:uppercase;margin-top:2px}
.cal-poster{width:100px;height:150px;object-fit:cover;border-radius:10px;flex-shrink:0;box-shadow:0 6px 20px rgba(0,0,0,.6)}
.cal-poster-placeholder{width:100px;height:150px;background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);border-radius:10px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:2.4rem}
.cal-info{flex:1;min-width:0;padding-top:2px}
.cal-title{font-family:'Inter',sans-serif;font-weight:700;font-size:1.15rem;color:#f0f0f0;line-height:1.3;margin-bottom:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cal-badges{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}
.cal-badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:.78rem;font-weight:600}
.cal-badge-rating{background:rgba(240,192,64,.15);color:#f0c040;border:1px solid rgba(240,192,64,.3)}
.cal-badge-date{background:rgba(255,255,255,.07);color:#bbb;border:1px solid #2a2a2a}
.cal-overview{font-size:.86rem;color:#888;line-height:1.65;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    "current_movie_title": None, "current_movie_id": None,
    "watchlist": [], "active_tab": 0, "scroll_top": False,
    "recently_viewed": [], "ui_lang": "English",
    "lb_language": "Any", "lb_country": "Any",
    "lb_genre": "Any", "lb_sort": "Popularity ↓", "lb_page": 1,
    "cal_region": "🇺🇸 USA",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Translations ──────────────────────────────────────────────────────────────
LANG = {
    "English": {
        "controls":"🎛️ Controls","search_ph":"Type any movie title…",
        "select_movie":"Select a movie","get_recos":"🎯 Get Recommendations",
        "no_results":"No results found.","recos_slider":"Recommendations",
        "sort_filter":"⚙️ Sort & Filter","sort_by":"Sort by",
        "sort_opts":["Similarity","Rating ↓","Year (Newest)"],
        "genre_filter":"Genre filter","min_rating":"Minimum Rating ⭐",
        "decade":"📅 Decade","decade_opts":["Any","2020s","2010s","2000s","1990s","1980s","1970s & older"],
        "surprise":"🎲 Surprise Me!","watchlist_count":"Watchlist",
        "now_exploring":"Now Exploring","because_liked":"Because you liked",
        "no_match":"No movies matched your filters.",
        "trending":"🔥 Trending This Week","discover":"🔍 Search Any Movie",
        "search_ph2":"Search TMDb — any movie, any language, any year…",
        "clear_wl":"🗑️ Clear Watchlist","recently_viewed":"🕐 Recently Viewed",
        "clear_hist":"🗑️ Clear History","similar":"Similar","save":"+ Save",
        "saved":"✓ Saved","trailer":"▶ Trailer","close":"Close",
        "remove":"Remove","sub":"One search. Endless movies. • Discover what to watch next.",
        "ui_language":"🌐 Website Language",
    },
    "Hindi": {
        "controls":"🎛️ नियंत्रण","search_ph":"कोई भी फिल्म का नाम लिखें…",
        "select_movie":"फिल्म चुनें","get_recos":"🎯 सुझाव पाएं",
        "no_results":"कोई परिणाम नहीं मिला।","recos_slider":"सुझाव",
        "sort_filter":"⚙️ क्रम और फ़िल्टर","sort_by":"क्रम",
        "sort_opts":["समानता","रेटिंग ↓","वर्ष (नवीनतम)"],
        "genre_filter":"शैली फ़िल्टर","min_rating":"न्यूनतम रेटिंग ⭐",
        "decade":"📅 दशक","decade_opts":["कोई भी","2020s","2010s","2000s","1990s","1980s","1970s व पुराने"],
        "surprise":"🎲 मुझे चौंकाओ!","watchlist_count":"वॉचलिस्ट",
        "now_exploring":"अभी देख रहे हैं","because_liked":"क्योंकि आपको पसंद आई",
        "no_match":"कोई फिल्म फ़िल्टर से मेल नहीं खाती।",
        "trending":"🔥 इस हफ्ते ट्रेंडिंग","discover":"🔍 कोई भी फिल्म खोजें",
        "search_ph2":"TMDb पर खोजें — कोई भी फिल्म, कोई भी भाषा, कोई भी साल…",
        "clear_wl":"🗑️ वॉचलिस्ट साफ करें","recently_viewed":"🕐 हाल ही में देखा",
        "clear_hist":"🗑️ इतिहास साफ करें","similar":"समान","save":"+ सहेजें",
        "saved":"✓ सहेजा","trailer":"▶ ट्रेलर","close":"बंद करें",
        "remove":"हटाएं","sub":"एक खोज। अनंत फिल्में। • अगली फिल्म खोजें।",
        "ui_language":"🌐 वेबसाइट भाषा",
    },
}

def T(key: str) -> str:
    lang = st.session_state.get("ui_lang", "English")
    return LANG.get(lang, LANG["English"]).get(key, LANG["English"].get(key, key))

# ── Cached API wrappers (TTL = 5 min) ─────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _cached_trending():
    return fetch_trending(16)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_upcoming(region: str):
    return fetch_upcoming_movies(region=region, pages=3)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_discover(query: str):
    return search_movies_for_display(query, n=12)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_browse(language, region, genre, sort, page):
    return fetch_by_language_country(language=language, region=region,
                                     genre=genre, sort=sort, page=page, n=16)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _wl_ids() -> set:
    """O(1) watchlist lookup set — rebuilt only when called."""
    return {w["id"] for w in st.session_state.watchlist}

def set_current_movie(title: str, tmdb_id=None) -> None:
    st.session_state.current_movie_title = title
    st.session_state.current_movie_id    = tmdb_id
    year = poster = None
    if tmdb_id:
        try:
            d = fetch_full_movie(int(tmdb_id))
            year   = d.get("year")
            poster = d.get("poster")
        except Exception:
            pass
    rv    = st.session_state.recently_viewed
    entry = {"title": title, "id": str(tmdb_id) if tmdb_id else "", "year": year or "N/A", "poster": poster}
    rv    = [r for r in rv if r["id"] != entry["id"]]
    st.session_state.recently_viewed = [entry] + rv[:9]

def add_to_watchlist(movie: dict) -> None:
    if movie.get("id") not in _wl_ids():
        st.session_state.watchlist.append({
            "id":     movie.get("id", ""),
            "title":  movie.get("title", "Unknown"),
            "poster": movie.get("poster"),
            "year":   movie.get("year", "N/A"),
            "rating": movie.get("rating", "N/A"),
        })
        st.toast(f"📌 Added **{movie['title']}** to watchlist!", icon="✅")

def _rating_float(r: dict) -> float:
    try:
        return float(r.get("rating", "0/10").split("/")[0])
    except ValueError:
        return 0.0

def _year_int(r: dict) -> int:
    y = r.get("year", "0")
    return int(y) if str(y).isdigit() else 0

# ── Card grid renderer ────────────────────────────────────────────────────────
def render_card_grid(movies: list, key_prefix: str, cols_per_row: int = 5) -> None:
    wl = _wl_ids()
    for i in range(0, len(movies), cols_per_row):
        row  = movies[i:i + cols_per_row]
        cols = st.columns(len(row))
        for j, movie in enumerate(row):
            with cols[j]:
                poster_html = (
                    f'<img class="movie-card-poster" src="{movie["poster"]}" loading="lazy"/>'
                    if movie.get("poster")
                    else '<div class="movie-card-no-poster">🎬</div>'
                )
                director = movie.get("director", "")
                dir_txt  = f"• {director}" if director and director != "N/A" else ""
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
</div>""", unsafe_allow_html=True)

                in_wl = movie.get("id") in wl
                b1, b2 = st.columns(2)
                with b1:
                    if st.button(T("similar"), key=f"{key_prefix}_sim_{i+j}", use_container_width=True):
                        set_current_movie(movie["title"], int(movie.get("id") or 0) or None)
                        st.session_state.active_tab  = 0
                        st.session_state.scroll_top  = True
                        st.rerun()
                with b2:
                    if st.button(T("saved") if in_wl else T("save"),
                                 key=f"{key_prefix}_wl_{i+j}",
                                 disabled=in_wl, use_container_width=True):
                        add_to_watchlist(movie)
                        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="cinematic-title">CineMatch</div>', unsafe_allow_html=True)
st.markdown(f'<div class="cinematic-sub">{T("sub")}</div>', unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    ui_lang = st.selectbox(T("ui_language"), list(LANG.keys()),
                           index=list(LANG.keys()).index(st.session_state.get("ui_lang","English")),
                           key="lang_select")
    if ui_lang != st.session_state.get("ui_lang", "English"):
        st.session_state.ui_lang = ui_lang
        st.rerun()

    st.markdown(f"### {T('controls')}")
    search_term = st.text_input(T("controls"), placeholder=T("search_ph"),
                                key="sidebar_search", label_visibility="collapsed")

    sidebar_results, movie_options, movie_ids = [], [], []
    if search_term and len(search_term.strip()) > 1:
        sidebar_results = list(search_movie_tmdb(search_term))
        movie_options   = [f"{m['title']} ({(m.get('release_date','') or '')[:4]})" for m in sidebar_results[:20]]
        movie_ids       = [m["id"] for m in sidebar_results[:20]]

    if movie_options:
        chosen_label = st.selectbox(T("select_movie"), options=movie_options, key="movie_selector")
        chosen_movie = sidebar_results[movie_options.index(chosen_label)]
        if st.session_state.get("current_movie_id") != chosen_movie["id"]:
            set_current_movie(chosen_movie["title"], chosen_movie["id"])
            st.session_state.active_tab = 0
            st.rerun()
    elif search_term:
        st.caption(T("no_results"))

    no_of_reco   = st.slider(T("recos_slider"), 5, 20, 10)
    st.markdown("---")
    st.markdown(f"#### {T('sort_filter')}")
    sort_by      = st.selectbox(T("sort_by"), T("sort_opts"))
    genre_filter = st.multiselect(T("genre_filter"), list(GENRE_ID_MAP.keys()))
    min_rating   = st.slider(T("min_rating"), 0.0, 10.0, 0.0, step=0.5)
    decade_filter = st.selectbox(T("decade"), T("decade_opts"))
    st.markdown("---")

    if st.button(T("surprise"), use_container_width=True):
        import random as _r
        try:
            pop = requests.get(
                "https://api.themoviedb.org/3/movie/popular",
                params={"api_key": TMDB_API_KEY, "page": _r.randint(1, 5)},
                timeout=8,
            ).json().get("results", [])
            if pop:
                pick = _r.choice(pop)
                set_current_movie(pick["title"], pick["id"])
                st.rerun()
        except Exception:
            st.toast("⚠️ Connection timeout. Try again!", icon="🌐")

    if st.session_state.watchlist:
        st.markdown(f"📋 **{T('watchlist_count')}:** {len(st.session_state.watchlist)}")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🎯 Recommendations",
    "🔥 Trending",
    "🔍 Discover",
    "🌍 Browse by Language",
    "📅 Release Calendar",
    f"📋 {T('watchlist_count')}",
    T("recently_viewed"),
])

# ── TAB 1 — Recommendations ───────────────────────────────────────────────────
with tab1:
    if st.session_state.get("scroll_top"):
        st.session_state.scroll_top = False

    title = st.session_state.current_movie_title
    mid   = st.session_state.current_movie_id

    if title:
        seed = fetch_full_movie(mid) if mid else {}
        feat_genres_html = "".join(
            f'<span style="background:#e50914;color:#fff;border-radius:12px;padding:2px 10px;font-size:.7rem;font-weight:600;">{g}</span>'
            for g in (seed.get("genres") or "").split(", ") if g and g != "N/A"
        )
        story = seed.get("overview", "")

        b_col, p_col = st.columns([3, 1])
        with b_col:
            st.markdown(f"""
<div class="featured-banner">
  <div class="featured-badge">{T("now_exploring")}</div>
  <div class="featured-title">{seed.get("title", title)}</div>
  <div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:12px;">
    <span style="background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 14px;font-size:.78rem;color:#f0c040;font-weight:700;">⭐ {seed.get("rating","N/A")}</span>
    <span style="background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 14px;font-size:.78rem;color:#aaa;">📅 {seed.get("year","N/A")}</span>
    <span style="background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 14px;font-size:.78rem;color:#aaa;">⏱ {seed.get("runtime","N/A")}</span>
    <span style="background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 14px;font-size:.78rem;color:#aaa;">🎬 {seed.get("director","N/A")}</span>
  </div>
  <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;">{feat_genres_html}</div>
  <div style="margin-top:10px;font-size:.82rem;color:#777;max-width:640px;line-height:1.6;">{story[:240] + "…" if len(story) > 240 else story}</div>
</div>""", unsafe_allow_html=True)
        with p_col:
            if seed.get("poster"):
                st.image(seed["poster"], width=300)

        with st.spinner(f"Finding movies similar to **{seed.get('title', title)}**…"):
            recos = get_recommendations(title, n=no_of_reco + 5)

        # Apply filters
        if genre_filter:
            recos = [r for r in recos if any(g in r.get("genres","") for g in genre_filter)]
        if min_rating > 0:
            recos = [r for r in recos if _rating_float(r) >= min_rating]
        decade_map = {
            "2020s": (2020, 2029), "2010s": (2010, 2019), "2000s": (2000, 2009),
            "1990s": (1990, 1999), "1980s": (1980, 1989), "1970s & older": (0, 1979),
        }
        if decade_filter in decade_map:
            lo, hi = decade_map[decade_filter]
            recos = [r for r in recos if lo <= _year_int(r) <= hi]

        sort_opts = T("sort_opts")
        if sort_by == sort_opts[1]:
            recos.sort(key=_rating_float, reverse=True)
        elif sort_by == sort_opts[2]:
            recos.sort(key=_year_int, reverse=True)
        recos = recos[:no_of_reco]

        st.markdown(f'<div class="section-header">{T("because_liked")} {seed.get("title", title)}</div>', unsafe_allow_html=True)
        st.caption(f"{len(recos)} recommendations • {sort_by}")
        if recos:
            render_card_grid(recos, key_prefix="reco", cols_per_row=5)
        else:
            st.warning(T("no_match"))
    else:
        st.markdown("""
<div style="text-align:center;padding:5rem 2rem;">
  <div style="font-size:4rem;margin-bottom:1.2rem;">🎬</div>
  <div style="font-family:'Bebas Neue',cursive;font-size:2.5rem;color:#fff;letter-spacing:.1em;">Welcome to CineMatch</div>
  <div style="color:#555;margin-top:.8rem;font-size:.9rem;line-height:1.8;">
    Search any movie in the sidebar and click <strong style="color:#e50914;">Get Recommendations</strong>.<br>
    Or hit <strong style="color:#e50914;">Surprise Me!</strong> to discover something new.<br><br>
    <span style="font-size:.75rem;color:#3a3a3a;">Powered by TMDb's library of 900,000+ titles.</span>
  </div>
</div>""", unsafe_allow_html=True)

# ── TAB 2 — Trending ──────────────────────────────────────────────────────────
with tab2:
    st.markdown(f'<div class="section-header">{T("trending")}</div>', unsafe_allow_html=True)
    with st.spinner("Loading trending movies…"):
        trending = _cached_trending()
    if trending:
        render_card_grid(trending, key_prefix="trend", cols_per_row=4)
    else:
        st.error("Could not load trending movies. Check your internet connection.")

# ── TAB 3 — Discover ──────────────────────────────────────────────────────────
with tab3:
    st.markdown(f'<div class="section-header">{T("discover")}</div>', unsafe_allow_html=True)
    query = st.text_input("Search", placeholder=T("search_ph2"),
                          key="discover_search", label_visibility="collapsed")
    if query and len(query.strip()) > 1:
        with st.spinner("Searching…"):
            disc_results = _cached_discover(query.strip())
        if disc_results:
            st.caption(f"{len(disc_results)} results for **{query}**")
            render_card_grid(disc_results, key_prefix="disc", cols_per_row=4)
        else:
            st.warning(f'No results found for "{query}".')

# ── TAB 4 — Browse by Language / Country ──────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">🌍 Browse by Language & Country</div>', unsafe_allow_html=True)
    st.caption("Discover top movies from any language or region — powered by TMDb Discover API.")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        lb_lang = st.selectbox("🗣️ Language", list(LANGUAGE_OPTIONS.keys()),
                               index=list(LANGUAGE_OPTIONS.keys()).index(st.session_state.lb_language),
                               key="lb_lang_select")
        st.session_state.lb_language = lb_lang
    with f2:
        lb_country = st.selectbox("🌍 Country / Region", list(COUNTRY_OPTIONS.keys()),
                                  index=list(COUNTRY_OPTIONS.keys()).index(st.session_state.lb_country),
                                  key="lb_country_select")
        st.session_state.lb_country = lb_country
    with f3:
        genre_choices = ["Any"] + list(GENRE_ID_MAP.keys())
        lb_genre = st.selectbox("🎭 Genre", genre_choices,
                                index=genre_choices.index(st.session_state.lb_genre)
                                      if st.session_state.lb_genre in genre_choices else 0,
                                key="lb_genre_select")
        st.session_state.lb_genre = lb_genre
    with f4:
        lb_sort = st.selectbox("↕️ Sort By", list(SORT_OPTIONS.keys()),
                               index=list(SORT_OPTIONS.keys()).index(st.session_state.lb_sort)
                                     if st.session_state.lb_sort in SORT_OPTIONS else 0,
                               key="lb_sort_select")
        st.session_state.lb_sort = lb_sort

    # Reset page on filter change
    filter_sig = (lb_lang, lb_country, lb_genre, lb_sort)
    if st.session_state.get("_lb_last_filter") != filter_sig:
        st.session_state.lb_page      = 1
        st.session_state["_lb_last_filter"] = filter_sig

    # Active filter pills
    pills = [f"🗣️ {lb_lang}"] * (lb_lang != "Any") + \
            [f"🌍 {lb_country}"] * (lb_country != "Any") + \
            [f"🎭 {lb_genre}"] * (lb_genre != "Any") + [f"↕️ {lb_sort}"]
    st.markdown(" &nbsp;".join(
        f'<span style="background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:3px 12px;font-size:.72rem;color:#aaa;">{p}</span>'
        for p in pills), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    with st.spinner("Fetching movies…"):
        lb_movies = _cached_browse(
            LANGUAGE_OPTIONS.get(lb_lang, ""),
            COUNTRY_OPTIONS.get(lb_country, ""),
            lb_genre if lb_genre != "Any" else "",
            SORT_OPTIONS.get(lb_sort, "popularity.desc"),
            st.session_state.lb_page,
        )

    if lb_movies:
        st.caption(f"Page {st.session_state.lb_page} — {len(lb_movies)} movies")
        render_card_grid(lb_movies, key_prefix="lb", cols_per_row=4)
        st.markdown("<br>", unsafe_allow_html=True)
        pg1, pg2, pg3 = st.columns([1, 2, 1])
        with pg1:
            if st.session_state.lb_page > 1:
                if st.button("← Previous Page", use_container_width=True, key="lb_prev"):
                    st.session_state.lb_page -= 1
                    st.rerun()
        with pg2:
            st.markdown(f"<div style='text-align:center;color:#444;font-size:.78rem;padding-top:10px;'>Page {st.session_state.lb_page}</div>",
                        unsafe_allow_html=True)
        with pg3:
            if st.button("Next Page →", use_container_width=True, key="lb_next"):
                st.session_state.lb_page += 1
                st.rerun()
    else:
        st.warning("No movies found for this combination. Try adjusting the filters.")

# ── TAB 5 — Release Calendar ──────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-header">📅 Upcoming Release Calendar</div>', unsafe_allow_html=True)
    st.caption("Theatrical releases coming soon — grouped by month.")

    cal_col1, _ = st.columns([2, 6])
    with cal_col1:
        cal_region_label = st.selectbox(
            "🌍 Region",
            options=list(COUNTRY_OPTIONS.keys())[1:],
            index=list(COUNTRY_OPTIONS.keys())[1:].index(st.session_state.cal_region)
                  if st.session_state.cal_region in list(COUNTRY_OPTIONS.keys())[1:] else 0,
            key="cal_region_select",
        )
        st.session_state.cal_region = cal_region_label

    cal_region_code = COUNTRY_OPTIONS.get(cal_region_label, "US")

    with st.spinner("Loading upcoming releases…"):
        upcoming = _cached_upcoming(cal_region_code)

    if not upcoming:
        st.warning("No upcoming movies found. Try a different region.")
    else:
        today_str    = date.today().isoformat()
        current_year = date.today().year
        future_movies = [m for m in upcoming
                         if m["release_date"] >= today_str and int(m.get("year") or 0) >= current_year]
        recent_movies = [m for m in upcoming
                         if m["release_date"] < today_str and int(m.get("year") or 0) >= current_year]

        def _render_calendar(movies_list: list, key_prefix: str) -> None:
            groups: dict = {}
            for m in movies_list:
                try:
                    mk = datetime.strptime(m["release_date"], "%Y-%m-%d").strftime("%B %Y")
                except Exception:
                    mk = "Unknown"
                groups.setdefault(mk, []).append(m)

            wl = _wl_ids()
            for month_label, group in groups.items():
                st.markdown(f'<div class="cal-month-header">📆 {month_label}</div>', unsafe_allow_html=True)
                for i in range(0, len(group), 2):
                    row_movies = group[i:i + 2]
                    row_cols   = st.columns(len(row_movies))
                    for j, m in enumerate(row_movies):
                        with row_cols[j]:
                            try:
                                dt        = datetime.strptime(m["release_date"], "%Y-%m-%d")
                                day_str   = dt.strftime("%d")
                                mon_str   = dt.strftime("%b")
                                full_date = dt.strftime("%d %B %Y")
                            except Exception:
                                day_str = mon_str = "?"
                                full_date = m.get("release_date", "N/A")

                            ov   = m.get("overview", "No overview available.")
                            ov   = ov[:280] + "…" if len(ov) > 280 else ov
                            img  = (f'<img class="cal-poster" src="{m["poster"]}" loading="lazy"/>'
                                    if m.get("poster") else '<div class="cal-poster-placeholder">🎬</div>')

                            st.markdown(f"""
<div class="cal-card">
  <div class="cal-date-box"><div class="cal-date-day">{day_str}</div><div class="cal-date-mon">{mon_str}</div></div>
  {img}
  <div class="cal-info">
    <div class="cal-title" title="{m['title']}">{m['title']}</div>
    <div class="cal-badges">
      <span class="cal-badge cal-badge-rating">⭐ {m.get("rating","N/A")}</span>
      <span class="cal-badge cal-badge-date">📅 {full_date}</span>
    </div>
    <div class="cal-overview">{ov}</div>
  </div>
</div>""", unsafe_allow_html=True)

                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button(T("similar"), key=f"{key_prefix}_sim_{m['id']}", use_container_width=True):
                                    set_current_movie(m["title"], int(m["id"]) if m["id"].isdigit() else None)
                                    st.session_state.active_tab = 0
                                    st.session_state.scroll_top = True
                                    st.rerun()
                            with b2:
                                in_wl = m.get("id") in wl
                                if st.button(T("saved") if in_wl else T("save"),
                                             key=f"{key_prefix}_wl_{m['id']}",
                                             disabled=in_wl, use_container_width=True):
                                    add_to_watchlist(m)
                                    st.rerun()
                            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if future_movies:
            st.caption(f"Showing {len(future_movies)} upcoming releases for **{cal_region_label}**")
            _render_calendar(future_movies, "cal_fut")
        if recent_movies:
            with st.expander(f"🎬 Recently Released ({len(recent_movies)} movies)", expanded=False):
                _render_calendar(recent_movies, "cal_rec")

# ── TAB 6 — Watchlist ─────────────────────────────────────────────────────────
with tab6:
    wl    = st.session_state.watchlist
    count = len(wl)
    st.markdown(f'<div class="section-header">📋 My Watchlist — {count} movie{"s" if count != 1 else ""}</div>', unsafe_allow_html=True)

    if not wl:
        st.markdown('<div style="text-align:center;padding:3rem;color:#444;"><div style="font-size:2.5rem;">📭</div><div style="margin-top:.8rem;font-size:.9rem;">Your watchlist is empty.<br>Browse and save movies from any tab.</div></div>', unsafe_allow_html=True)
    else:
        poster_cols = st.columns(min(count, 8))
        for i, w in enumerate(wl[:8]):
            with poster_cols[i]:
                if w.get("poster"):
                    st.image(w["poster"], width=120)
                st.caption(w["title"][:18] + ("…" if len(w["title"]) > 18 else ""))

        st.markdown("<br>", unsafe_allow_html=True)
        for idx, w in enumerate(wl.copy()):
            c1, c2, c3, c4 = st.columns([3, 1, 1.5, 1.5])
            with c1:
                st.markdown(f"🎬 **{w['title']}** &nbsp;<span style='color:#555;font-size:.8rem'>{w.get('year','')}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='color:#e50914;font-size:.8rem;font-weight:700;'>⭐ {w.get('rating','N/A')}</span>", unsafe_allow_html=True)
            with c3:
                if st.button(T("trailer"), key=f"wl_trailer_{idx}"):
                    tk = st.session_state.get(f"trailer_{w['id']}")
                    if not tk:
                        try:
                            vd = requests.get(
                                f"https://api.themoviedb.org/3/movie/{w['id']}/videos",
                                params={"api_key": TMDB_API_KEY}, timeout=6,
                            ).json()
                            trailers = [v for v in vd.get("results", [])
                                        if v.get("type") == "Trailer" and v.get("site") == "YouTube"]
                            tk = trailers[0]["key"] if trailers else "none"
                        except Exception:
                            tk = "none"
                        st.session_state[f"trailer_{w['id']}"] = tk
                    # Close other trailers
                    for _w in st.session_state.watchlist:
                        if _w["id"] != w["id"]:
                            st.session_state[f"show_trailer_{_w['id']}"] = False
                    st.session_state[f"show_trailer_{w['id']}"] = not st.session_state.get(f"show_trailer_{w['id']}", False)
                    st.rerun()
            with c4:
                if st.button(T("close"), key=f"wl_rm_{idx}"):
                    st.session_state.watchlist.remove(w)
                    st.rerun()

            tk = st.session_state.get(f"trailer_{w['id']}")
            if st.session_state.get(f"show_trailer_{w['id']}"):
                if tk and tk != "none":
                    st.markdown(
                        f'<iframe width="100%" height="315" src="https://www.youtube.com/embed/{tk}?autoplay=1" '
                        f'frameborder="0" allow="autoplay;encrypted-media" allowfullscreen style="border-radius:10px;margin:8px 0;"></iframe>',
                        unsafe_allow_html=True)
                else:
                    st.caption("⚠️ No trailer available.")
            st.markdown("<hr style='margin:4px 0;border-color:#1a1a1a;'>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_c, _ = st.columns([1, 2, 1])
        with col_c:
            if st.button(T("clear_wl"), use_container_width=True):
                st.session_state.watchlist = []
                st.rerun()

# ── TAB 7 — Recently Viewed ───────────────────────────────────────────────────
with tab7:
    st.markdown(f'<div class="section-header">{T("recently_viewed")}</div>', unsafe_allow_html=True)
    rv = st.session_state.recently_viewed

    if not rv:
        st.markdown('<div style="text-align:center;padding:3rem;color:#444;"><div style="font-size:2.5rem;">🕐</div><div style="margin-top:.8rem;font-size:.9rem;">No movies viewed yet.<br>Start exploring to build your history.</div></div>', unsafe_allow_html=True)
    else:
        RECENT_CUTOFF = 2020
        rv_f1, rv_f2 = st.columns([3, 1])
        with rv_f1:
            show_all = st.toggle("Show all years (including older movies)", value=False, key="rv_show_all")
        with rv_f2:
            st.markdown(f"<div style='text-align:right;color:#555;font-size:.8rem;padding-top:8px;'>{len(rv)} total</div>", unsafe_allow_html=True)

        if show_all:
            display_rv = rv
        else:
            display_rv = [r for r in rv if str(r.get("year","0")).isdigit() and int(r.get("year", 0)) >= RECENT_CUTOFF]
            skipped = len(rv) - len(display_rv)
            if skipped:
                st.caption(f"ℹ️ Hiding {skipped} older movie(s) (pre-{RECENT_CUTOFF}). Toggle above to show all.")

        if not display_rv:
            st.info("No recent movies (2020+) in your history. Toggle 'Show all years' to see everything.")
        else:
            for ridx, r in enumerate(display_rv):
                yr    = r.get("year", "N/A")
                yint  = int(yr) if str(yr).isdigit() else 0
                yc    = "#e50914" if yint >= 2024 else "#f0c040" if yint >= 2020 else "#555"
                rc_poster, rc_info, rc_btn1, rc_btn2 = st.columns([1, 5, 1.5, 1.5])
                with rc_poster:
                    if r.get("poster"):
                        st.image(r["poster"], width=55)
                    else:
                        st.markdown("<div style='width:55px;height:80px;background:#1a1a2e;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;'>🎬</div>", unsafe_allow_html=True)
                with rc_info:
                    st.markdown(
                        f"<div style='padding-top:8px;'><span style='font-weight:700;font-size:.95rem;color:#eee;'>{r['title']}</span>"
                        f"&nbsp;&nbsp;<span style='background:{yc}22;color:{yc};border:1px solid {yc}44;border-radius:10px;padding:2px 10px;font-size:.72rem;font-weight:700;'>{yr}</span></div>",
                        unsafe_allow_html=True)
                with rc_btn1:
                    if st.button(T("similar"), key=f"rv_sim_{ridx}", use_container_width=True):
                        _mid = int(r["id"]) if r.get("id") and str(r["id"]).isdigit() else None
                        set_current_movie(r["title"], _mid)
                        st.session_state.active_tab = 0
                        st.session_state.scroll_top = True
                        st.rerun()
                with rc_btn2:
                    if st.button(T("remove"), key=f"rv_rm_{ridx}", use_container_width=True):
                        actual = next((i for i, x in enumerate(rv) if x["id"] == r["id"]), None)
                        if actual is not None:
                            st.session_state.recently_viewed.pop(actual)
                        st.rerun()
                st.markdown("<hr style='margin:6px 0;border-color:#1a1a1a;'>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_ch, _ = st.columns([1, 2, 1])
        with col_ch:
            if st.button(T("clear_hist"), use_container_width=True):
                st.session_state.recently_viewed = []
                st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#2a2a2a;font-size:1.12rem;letter-spacing:.12em;text-transform:uppercase;'>MADE BY ❤ VICKY RANA</p>",
    unsafe_allow_html=True,
)