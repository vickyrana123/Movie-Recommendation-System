import random
import streamlit as st
import requests
from datetime import datetime, date

from recommender import (
    fetch_full_movie,
    fetch_trending,
    get_recommendations,
    search_movie_tmdb,
    search_movies_for_display,
    fetch_by_language_country,
    fetch_upcoming_movies,
    LANGUAGE_OPTIONS,
    COUNTRY_OPTIONS,
    GENRE_ID_MAP,
    SORT_OPTIONS,
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
    section[data-testid="stSidebar"] .stButton > button { background: transparent !important; border: 1px solid #e50914 !important; color: #e50914 !important; width: 100% !important; padding: 0.6rem 1rem !important; height: auto !important; }
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
    /* Watchlist row buttons — identical size */
    [data-testid="stHorizontalBlock"] .stButton > button {
        min-width: 0 !important;
        width: 100% !important;
        height: 40px !important;
        line-height: 1 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        padding: 0.5rem 1rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.06em !important;
    }
    /* ── Calendar styles ── */
    .cal-month-header {
        font-family: 'Bebas Neue', cursive; font-size: 1.6rem; color: #e50914;
        letter-spacing: 0.12em; border-bottom: 1px solid #2a2a2a;
        padding-bottom: 6px; margin: 2rem 0 1rem;
    }
    .cal-card {
        display: flex; gap: 14px; align-items: flex-start;
        background: #161616; border: 1px solid #1f1f1f; border-radius: 10px;
        padding: 50px; margin-bottom: 10px;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .cal-card:hover { border-color: #e50914; box-shadow: 0 6px 24px rgba(229,9,20,0.15); }
    .cal-date-box {
        min-width: 52px; background: #e50914; border-radius: 8px;
        text-align: center; padding: 6px 4px; flex-shrink: 0;
    }
    .cal-date-day { font-family: 'Bebas Neue', cursive; font-size: 1.6rem; color: #fff; line-height: 1; }
    .cal-date-mon { font-size: 0.62rem; font-weight: 700; color: rgba(255,255,255,0.75); letter-spacing: 0.1em; text-transform: uppercase; }
    .cal-info { flex: 1; min-width: 0; }
    .cal-title { font-weight: 700; font-size: 0.92rem; color: #eee; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .cal-meta { font-size: 0.72rem; color: #555; margin-top: 3px; }
    .cal-overview { font-size: 0.75rem; color: #666; margin-top: 5px; line-height: 1.5; }
    /* ── Language browse filter pills ── */
    .filter-pill {
        display: inline-block; background: #1a1a1a; border: 1px solid #333;
        border-radius: 20px; padding: 4px 14px; font-size: 0.75rem; color: #aaa;
        margin: 3px; cursor: pointer;
    }
    .filter-pill.active { background: #e50914; border-color: #e50914; color: #fff; }
</style>
""", unsafe_allow_html=True)


# ===================== SESSION STATE =====================
for _k, _v in [
    ("current_movie_title", None), ("current_movie_id", None),
    ("watchlist", []), ("active_tab", 0), ("scroll_top", False),
    ("recently_viewed", []), ("ui_lang", "English"),
    ("lb_language", "Any"), ("lb_country", "Any"),
    ("lb_genre", "Any"), ("lb_sort", "Popularity ↓"), ("lb_page", 1),
    ("cal_region", "🇺🇸 USA"),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ===================== TRANSLATIONS =====================
LANG = {
    "English": {
        "controls": "🎛️ Controls", "search_ph": "Type any movie title…",
        "select_movie": "Select a movie", "get_recos": "🎯 Get Recommendations",
        "no_results": "No results found.", "recos_slider": "Recommendations",
        "sort_filter": "⚙️ Sort & Filter", "sort_by": "Sort by",
        "sort_opts": ["Similarity", "Rating ↓", "Year (Newest)"],
        "genre_filter": "Genre filter", "min_rating": "Minimum Rating ⭐",
        "decade": "📅 Decade", "decade_opts": ["Any","2020s","2010s","2000s","1990s","1980s","1970s & older"],
        "surprise": "🎲 Surprise Me!", "watchlist_count": "Watchlist",
        "now_exploring": "Now Exploring", "because_liked": "Because you liked",
        "no_match": "No movies matched your filters.",
        "trending": "🔥 Trending This Week", "discover": "🔍 Search Any Movie",
        "search_ph2": "Search TMDb — any movie, any language, any year…",
        "watchlist_empty": "Your watchlist is empty.<br>Browse and save movies from any tab.",
        "clear_wl": "🗑️ Clear Watchlist", "recently_viewed": "🕐 Recently Viewed",
        "no_history": "No movies viewed yet.<br>Start exploring to build your history.",
        "clear_hist": "🗑️ Clear History", "similar": "Similar", "save": "+ Save",
        "saved": "✓ Saved", "trailer": "▶ Trailer", "close": "Close",
        "remove": "Remove", "sub": "One search. Endless movies. • Discover what to watch next.",
        "ui_language": "🌐 Website Language",
    },
    "Hindi": {
        "controls": "🎛️ नियंत्रण", "search_ph": "कोई भी फिल्म का नाम लिखें…",
        "select_movie": "फिल्म चुनें", "get_recos": "🎯 सुझाव पाएं",
        "no_results": "कोई परिणाम नहीं मिला।", "recos_slider": "सुझाव",
        "sort_filter": "⚙️ क्रम और फ़िल्टर", "sort_by": "क्रम",
        "sort_opts": ["समानता", "रेटिंग ↓", "वर्ष (नवीनतम)"],
        "genre_filter": "शैली फ़िल्टर", "min_rating": "न्यूनतम रेटिंग ⭐",
        "decade": "📅 दशक", "decade_opts": ["कोई भी","2020s","2010s","2000s","1990s","1980s","1970s व पुराने"],
        "surprise": "🎲 मुझे चौंकाओ!", "watchlist_count": "वॉचलिस्ट",
        "now_exploring": "अभी देख रहे हैं", "because_liked": "क्योंकि आपको पसंद आई",
        "no_match": "कोई फिल्म फ़िल्टर से मेल नहीं खाती।",
        "trending": "🔥 इस हफ्ते ट्रेंडिंग", "discover": "🔍 कोई भी फिल्म खोजें",
        "search_ph2": "TMDb पर खोजें — कोई भी फिल्म, कोई भी भाषा, कोई भी साल…",
        "watchlist_empty": "आपकी वॉचलिस्ट खाली है।<br>किसी भी टैब से फिल्में सहेजें।",
        "clear_wl": "🗑️ वॉचलिस्ट साफ करें", "recently_viewed": "🕐 हाल ही में देखा",
        "no_history": "अभी तक कोई फिल्म नहीं देखी।<br>इतिहास बनाने के लिए एक्सप्लोर करें।",
        "clear_hist": "🗑️ इतिहास साफ करें", "similar": "समान", "save": "+ सहेजें",
        "saved": "✓ सहेजा", "trailer": "▶ ट्रेलर", "close": "बंद करें",
        "remove": "हटाएं", "sub": "एक खोज। अनंत फिल्में। • अगली फिल्म खोजें।",
        "ui_language": "🌐 वेबसाइट भाषा",
    }
}

def T(key):
    lang = st.session_state.get("ui_lang", "English")
    return LANG.get(lang, LANG["English"]).get(key, LANG["English"].get(key, key))

def set_current_movie(title, tmdb_id=None):
    st.session_state.current_movie_title = title
    st.session_state.current_movie_id = tmdb_id
    rv = st.session_state.recently_viewed
    entry = {"title": title, "id": str(tmdb_id) if tmdb_id else ""}
    rv = [r for r in rv if r["id"] != entry["id"]]
    rv.insert(0, entry)
    st.session_state.recently_viewed = rv[:10]


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
                    if st.button(T("similar"), key=f"{key_prefix}_sim_{i+j}", use_container_width=True):
                        set_current_movie(movie["title"], int(movie.get("id", 0)) or None)
                        st.session_state.active_tab = 0
                        st.session_state.scroll_top = True
                        st.rerun()
                with b2:
                    in_wl = movie.get("id") in [w["id"] for w in st.session_state.watchlist]
                    if st.button(T("saved") if in_wl else T("save"), key=f"{key_prefix}_wl_{i+j}", disabled=in_wl, use_container_width=True):
                        add_to_watchlist(movie)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)


# ===================== TAB SWITCHER =====================
if st.session_state.get("active_tab", 0) == 0 and st.session_state.get("current_movie_title"):
    st.markdown("""
    <script>
    setTimeout(function() {
        const tabs = window.parent.document.querySelectorAll('[data-testid="stTab"]');
        if (tabs.length > 0) tabs[0].click();
    }, 100);
    </script>
    """, unsafe_allow_html=True)

# ===================== HEADER =====================
st.markdown('<div class="cinematic-title">CineMatch</div>', unsafe_allow_html=True)
st.markdown(f'<div class="cinematic-sub">{T("sub")}</div>', unsafe_allow_html=True)

# ===================== SIDEBAR =====================
with st.sidebar:
    ui_lang = st.selectbox(T("ui_language"), list(LANG.keys()),
                           index=list(LANG.keys()).index(st.session_state.get("ui_lang","English")),
                           key="lang_select")
    if ui_lang != st.session_state.get("ui_lang","English"):
        st.session_state.ui_lang = ui_lang
        st.rerun()

    st.markdown(f"### {T('controls')}")
    search_term = st.text_input(T("controls"), placeholder=T("search_ph"),
                                key="sidebar_search", label_visibility="collapsed")

    sidebar_results = []
    movie_options = []
    movie_ids = []
    if search_term and len(search_term.strip()) > 1:
        sidebar_results = search_movie_tmdb(search_term)
        movie_options = [f"{m['title']} ({(m.get('release_date','') or '')[:4]})" for m in sidebar_results[:20]]
        movie_ids = [m["id"] for m in sidebar_results[:20]]

    if movie_options:
        chosen_label = st.selectbox(T("select_movie"), options=movie_options, key="movie_selector")
        chosen_idx = movie_options.index(chosen_label)
        chosen_movie = sidebar_results[chosen_idx]
        if st.session_state.get("current_movie_id") != chosen_movie["id"]:
            set_current_movie(chosen_movie["title"], chosen_movie["id"])
            st.session_state.active_tab = 0
            st.rerun()
    elif search_term:
        st.caption(T("no_results"))

    no_of_reco = st.slider(T("recos_slider"), 5, 20, 10)
    st.markdown("---")
    st.markdown(f"#### {T('sort_filter')}")
    sort_by = st.selectbox(T("sort_by"), T("sort_opts"))
    genre_filter = st.multiselect(T("genre_filter"), [
        "Action", "Adventure", "Animation", "Comedy", "Crime",
        "Drama", "Fantasy", "Horror", "Mystery", "Romance",
        "Science Fiction", "Thriller", "War", "Western"
    ])
    min_rating = st.slider(T("min_rating"), 0.0, 10.0, 0.0, step=0.5)
    decade_filter = st.selectbox(T("decade"), T("decade_opts"))
    st.markdown("---")
    st.markdown("<div style='width:100%'>", unsafe_allow_html=True)
    if st.button(T("surprise"), use_container_width=True):
        import random as _r
        try:
            pop = requests.get("https://api.themoviedb.org/3/movie/popular",
                               params={"api_key": TMDB_API_KEY, "page": _r.randint(1, 5)},
                               timeout=10).json().get("results", [])
            if pop:
                pick = _r.choice(pop)
                set_current_movie(pick["title"], pick["id"])
                st.rerun()
        except Exception:
            st.toast("⚠️ Connection timeout. Please try again!", icon="🌐")
    st.markdown("</div>", unsafe_allow_html=True)
    if st.session_state.watchlist:
        st.markdown(f"📋 **{T('watchlist_count')}:** {len(st.session_state.watchlist)}")


# ===================== TABS =====================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🎯 " + T("get_recos")[2:],
    "🔥 " + T("trending")[2:],
    "🔍 " + T("discover")[2:],
    "🌍 Browse by Language",
    "📅 Release Calendar",
     "📋 " + T("watchlist_count"),
         T("recently_viewed"),

])

# ── TAB 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    if st.session_state.get("scroll_top", False):
        st.markdown("""
        <script>
            window.parent.document.querySelector('[data-testid="stAppViewContainer"]').scrollTo({top: 0, behavior: 'smooth'});
        </script>
        """, unsafe_allow_html=True)
        st.session_state.scroll_top = False

    if st.session_state.get("_force_reload"):
        st.session_state["_force_reload"] = None

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
                <div class="featured-badge">{T("now_exploring")}</div>
                <div class="featured-title">{feat_title}</div>
                <div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:12px;">
                    <span style="background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 14px;font-size:0.78rem;color:#f0c040;font-weight:700;">⭐ {feat_rating}</span>
                    <span style="background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 14px;font-size:0.78rem;color:#aaa;">📅 {feat_year}</span>
                    <span style="background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 14px;font-size:0.78rem;color:#aaa;">⏱ {feat_runtime}</span>
                    <span style="background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 14px;font-size:0.78rem;color:#aaa;">🎬 {feat_dir}</span>
                </div>
                <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;">
                    {"".join(f'<span style="background:#e50914;color:#fff;border-radius:12px;padding:2px 10px;font-size:0.7rem;font-weight:600;">{g}</span>' for g in feat_genres.split(", ") if g and g != "N/A")}
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
        if decade_filter not in ("Any", T("decade_opts")[0]):
            decade_map = {
                "2020s": (2020, 2029), "2010s": (2010, 2019), "2000s": (2000, 2009),
                "1990s": (1990, 1999), "1980s": (1980, 1989), "1970s & older": (0, 1979)
            }
            d_from, d_to = decade_map.get(decade_filter, (0, 9999))
            recos = [r for r in recos if r.get("year","0").isdigit() and d_from <= int(r["year"]) <= d_to]
        sort_opts = T("sort_opts")
        if sort_by == sort_opts[1]:
            recos.sort(key=lambda x: float(x["rating"].split("/")[0]) if x.get("rating","N/A") != "N/A" else 0, reverse=True)
        elif sort_by == sort_opts[2]:
            recos.sort(key=lambda x: int(x["year"]) if x.get("year","N/A") not in ("N/A","") else 0, reverse=True)

        recos = recos[:no_of_reco]
        st.markdown(f'<div class="section-header">{T("because_liked")} {feat_title}</div>', unsafe_allow_html=True)
        st.caption(f"{len(recos)} recommendations • {sort_by}")

        if recos:
            render_card_grid(recos, key_prefix="reco", cols_per_row=5)
        else:
            st.warning(T("no_match"))
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
    st.markdown(f'<div class="section-header">{T("trending")}</div>', unsafe_allow_html=True)
    with st.spinner("Loading trending movies…"):
        trending = fetch_trending(16)
    if trending:
        render_card_grid(trending, key_prefix="trend", cols_per_row=4)
    else:
        st.error("Could not load trending movies. Check your internet connection.")

# ── TAB 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown(f'<div class="section-header">{T("discover")}</div>', unsafe_allow_html=True)
    query = st.text_input("Search", placeholder=T("search_ph2"), key="discover_search", label_visibility="collapsed")
    if query and len(query.strip()) > 1:
        with st.spinner("Searching…"):
            disc_results = search_movies_for_display(query, n=12)
        if disc_results:
            st.caption(f"{len(disc_results)} results for **{query}**")
            render_card_grid(disc_results, key_prefix="disc", cols_per_row=4)
        else:
            st.warning(f'No results found for "{query}".')

# ── TAB 4 — 🌍 BROWSE BY LANGUAGE / COUNTRY ───────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">🌍 Browse by Language & Country</div>', unsafe_allow_html=True)
    st.caption("Discover top movies from any language or region — powered by TMDb Discover API.")

    # ── Filters row ──
    f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
    with f1:
        lb_lang = st.selectbox(
            "🗣️ Language",
            options=list(LANGUAGE_OPTIONS.keys()),
            index=list(LANGUAGE_OPTIONS.keys()).index(st.session_state.lb_language),
            key="lb_lang_select",
        )
        st.session_state.lb_language = lb_lang

    with f2:
        lb_country = st.selectbox(
            "🌍 Country / Region",
            options=list(COUNTRY_OPTIONS.keys()),
            index=list(COUNTRY_OPTIONS.keys()).index(st.session_state.lb_country),
            key="lb_country_select",
        )
        st.session_state.lb_country = lb_country

    with f3:
        genre_choices = ["Any"] + list(GENRE_ID_MAP.keys())
        lb_genre = st.selectbox(
            "🎭 Genre",
            options=genre_choices,
            index=genre_choices.index(st.session_state.lb_genre) if st.session_state.lb_genre in genre_choices else 0,
            key="lb_genre_select",
        )
        st.session_state.lb_genre = lb_genre

    with f4:
        lb_sort = st.selectbox(
            "↕️ Sort By",
            options=list(SORT_OPTIONS.keys()),
            index=list(SORT_OPTIONS.keys()).index(st.session_state.lb_sort) if st.session_state.lb_sort in SORT_OPTIONS else 0,
            key="lb_sort_select",
        )
        st.session_state.lb_sort = lb_sort

    # Reset page when filters change
    filter_sig = (lb_lang, lb_country, lb_genre, lb_sort)
    if st.session_state.get("_lb_last_filter") != filter_sig:
        st.session_state.lb_page = 1
        st.session_state["_lb_last_filter"] = filter_sig

    # Active filter summary
    active_filters = []
    if lb_lang != "Any":     active_filters.append(f"🗣️ {lb_lang}")
    if lb_country != "Any":  active_filters.append(f"🌍 {lb_country}")
    if lb_genre != "Any":    active_filters.append(f"🎭 {lb_genre}")
    active_filters.append(f"↕️ {lb_sort}")
    st.markdown(
        " &nbsp;".join(
            f'<span style="background:#1a1a1a;border:1px solid #333;border-radius:20px;'
            f'padding:3px 12px;font-size:0.72rem;color:#aaa;">{f}</span>'
            for f in active_filters
        ),
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    with st.spinner("Fetching movies…"):
        lb_movies = fetch_by_language_country(
            language=LANGUAGE_OPTIONS.get(lb_lang, ""),
            region=COUNTRY_OPTIONS.get(lb_country, ""),
            genre=lb_genre if lb_genre != "Any" else "",
            sort=SORT_OPTIONS.get(lb_sort, "popularity.desc"),
            page=st.session_state.lb_page,
            n=16,
        )

    if lb_movies:
        st.caption(f"Showing page {st.session_state.lb_page} — {len(lb_movies)} movies")
        render_card_grid(lb_movies, key_prefix="lb", cols_per_row=4)

        # Pagination
        st.markdown("<br>", unsafe_allow_html=True)
        pg1, pg2, pg3 = st.columns([1, 2, 1])
        with pg1:
            if st.session_state.lb_page > 1:
                if st.button("← Previous Page", use_container_width=True, key="lb_prev"):
                    st.session_state.lb_page -= 1
                    st.rerun()
        with pg2:
            st.markdown(
                f"<div style='text-align:center;color:#444;font-size:0.78rem;padding-top:10px;'>Page {st.session_state.lb_page}</div>",
                unsafe_allow_html=True,
            )
        with pg3:
            if st.button("Next Page →", use_container_width=True, key="lb_next"):
                st.session_state.lb_page += 1
                st.rerun()
    else:
        st.warning("No movies found for this combination. Try adjusting the filters.")

# ── TAB 5 — 📅 RELEASE CALENDAR ───────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-header">📅 Upcoming Release Calendar</div>', unsafe_allow_html=True)
    st.caption("Theatrical releases coming soon — grouped by month.")

    # Region picker
    cal_col1, cal_col2 = st.columns([2, 6])
    with cal_col1:
        cal_region_label = st.selectbox(
            "🌍 Region",
            options=list(COUNTRY_OPTIONS.keys())[1:],   # skip "Any"
            index=list(COUNTRY_OPTIONS.keys())[1:].index(st.session_state.cal_region)
                  if st.session_state.cal_region in list(COUNTRY_OPTIONS.keys())[1:] else 0,
            key="cal_region_select",
        )
        st.session_state.cal_region = cal_region_label

    cal_region_code = COUNTRY_OPTIONS.get(cal_region_label, "US")

    with st.spinner("Loading upcoming releases…"):
        upcoming = fetch_upcoming_movies(region=cal_region_code, pages=3)

    if not upcoming:
        st.warning("No upcoming movies found. Try a different region.")
    else:
        today_str = date.today().isoformat()

        # Separate: coming soon vs already released (in case TMDb returns some)
        future_movies  = [m for m in upcoming if m["release_date"] >= today_str]
        recent_movies  = [m for m in upcoming if m["release_date"] < today_str]

        def _render_calendar(movies_list, key_prefix):
            """Render movies grouped by Month Year with card layout."""
            from itertools import groupby

            def month_key(m):
                try:
                    return datetime.strptime(m["release_date"], "%Y-%m-%d").strftime("%B %Y")
                except Exception:
                    return "Unknown"

            groups = {}
            for m in movies_list:
                mk = month_key(m)
                groups.setdefault(mk, []).append(m)

            for month_label, group in groups.items():
                st.markdown(f'<div class="cal-month-header">📆 {month_label}</div>', unsafe_allow_html=True)
                cols_per_row = 2
                for i in range(0, len(group), cols_per_row):
                    row_movies = group[i:i + cols_per_row]
                    row_cols   = st.columns(len(row_movies))
                    for j, m in enumerate(row_movies):
                        with row_cols[j]:
                            try:
                                dt = datetime.strptime(m["release_date"], "%Y-%m-%d")
                                day_str = dt.strftime("%d")
                                mon_str = dt.strftime("%b")
                            except Exception:
                                day_str, mon_str = "?", "?"

                            overview_snippet = m.get("overview", "")
                            overview_snippet = overview_snippet[:120] + "…" if len(overview_snippet) > 120 else overview_snippet

                            # Card HTML
                            poster_html = (
                                f'<img src="{m["poster"]}" style="width:54px;height:80px;object-fit:cover;border-radius:6px;flex-shrink:0;" loading="lazy"/>'
                                if m.get("poster")
                                else '<div style="width:54px;height:80px;background:#1a1a2e;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0;">🎬</div>'
                            )
                            st.markdown(f"""
                            <div class="cal-card">
                                <div class="cal-date-box">
                                    <div class="cal-date-day">{day_str}</div>
                                    <div class="cal-date-mon">{mon_str}</div>
                                </div>
                                {poster_html}
                                <div class="cal-info">
                                    <div class="cal-title">{m['title']}</div>
                                    <div class="cal-meta">⭐ {m.get('rating','N/A')} &nbsp;•&nbsp; {m.get('release_date','')}</div>
                                    <div class="cal-overview">{overview_snippet}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Action buttons
                            b1, b2 = st.columns([1, 1])
                            with b1:
                                if st.button(T("similar"), key=f"{key_prefix}_sim_{m['id']}", use_container_width=True):
                                    set_current_movie(m["title"], int(m["id"]) if m["id"].isdigit() else None)
                                    st.session_state.active_tab = 0
                                    st.session_state.scroll_top = True
                                    st.rerun()
                            with b2:
                                in_wl = m.get("id") in [w["id"] for w in st.session_state.watchlist]
                                if st.button(T("saved") if in_wl else T("save"), key=f"{key_prefix}_wl_{m['id']}", disabled=in_wl, use_container_width=True):
                                    add_to_watchlist(m)
                                    st.rerun()

        if future_movies:
            st.markdown(f"<span style='color:#555;font-size:0.8rem;'>Showing {len(future_movies)} upcoming releases for <b style='color:#aaa'>{cal_region_label}</b></span>", unsafe_allow_html=True)
            _render_calendar(future_movies, key_prefix="cal_fut")

        if recent_movies:
            with st.expander(f"🎬 Recently Released ({len(recent_movies)} movies)", expanded=False):
                _render_calendar(recent_movies, key_prefix="cal_rec")
    

with tab6:
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
            c1, c2, c3, c4 = st.columns([3, 1, 1.5, 1.5])
            with c1:
                st.markdown(f"🎬 **{w['title']}** &nbsp; <span style='color:#555;font-size:0.8rem'>{w.get('year','')}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='color:#e50914;font-size:0.8rem;font-weight:700;'>⭐ {w.get('rating','N/A')}</span>", unsafe_allow_html=True)
            with c3:
                if st.button(T("trailer"), key=f"wl_trailer_{idx}"):
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
                    for _w in st.session_state.watchlist:
                        if _w["id"] != w["id"]:
                            st.session_state[f"show_trailer_{_w['id']}"] = False
                    st.session_state[f"show_trailer_{w['id']}"] = not current
                    st.rerun()
            with c4:
                if st.button(T("close"), key=f"wl_rm_{idx}"):
                    st.session_state.watchlist.remove(w)
                    st.rerun()

            trailer_key = st.session_state.get(f"trailer_{w['id']}")
            show_trailer = st.session_state.get(f"show_trailer_{w['id']}", False)
            if show_trailer and trailer_key and trailer_key != "none":
                st.markdown(
                    f'<iframe width="100%" height="515" src="https://www.youtube.com/embed/{trailer_key}?autoplay=1" '
                    f'frameborder="0" allow="autoplay; encrypted-media" allowfullscreen style="border-radius:10px;margin:8px 0;"></iframe>',
                    unsafe_allow_html=True
                )
            elif show_trailer and (not trailer_key or trailer_key == "none"):
                st.caption("⚠️ No trailer available for this movie.")
            st.markdown("<hr style='margin:4px 0;border-color:#1a1a1a;'>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_clear1, col_clear2, col_clear3 = st.columns([1, 2, 1])
        with col_clear2:
            if st.button(T("clear_wl"), use_container_width=True):
                st.session_state.watchlist = []
                st.rerun()
    
with tab7:
    st.markdown(f'<div class="section-header">{T("recently_viewed")}</div>', unsafe_allow_html=True)
    rv = st.session_state.recently_viewed
    if not rv:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#444;">
            <div style="font-size:2.5rem;">🕐</div>
            <div style="margin-top:0.8rem;font-size:0.9rem;">No movies viewed yet.<br>Start exploring to build your history.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.caption(f"{len(rv)} recently viewed")
        for ridx, r in enumerate(rv):
            rc1, rc2, rc3 = st.columns([5, 1.5, 1.5])
            with rc1:
                st.markdown(f"🎬 **{r['title']}**", unsafe_allow_html=True)
            with rc2:
                if st.button(T("similar"), key=f"rv_sim_{ridx}"):
                    _mid = int(r["id"]) if r.get("id") and str(r["id"]).isdigit() else None
                    set_current_movie(r["title"], _mid)
                    st.session_state.active_tab = 0
                    st.session_state.scroll_top = True
                    st.session_state["_force_reload"] = r["id"]
                    st.rerun()
            with rc3:
                if st.button(T("remove"), key=f"rv_rm_{ridx}"):
                    st.session_state.recently_viewed.pop(ridx)
                    st.rerun()
            st.markdown("<hr style='margin:4px 0;border-color:#1a1a1a;'>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button(T("clear_hist"), use_container_width=True):
                st.session_state.recently_viewed = []
                st.rerun()


# ===================== FOOTER =====================
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#2a2a2a;font-size:1.12rem;letter-spacing:0.12em;text-transform:uppercase;'>"
    "MADE BY ❤ VICKY RANA"
    "</p>",
    unsafe_allow_html=True
)