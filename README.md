# 🎬 CineMatch — Movie Recommender App

> **One search. Endless movies. — Discover what to watch next.**

CineMatch is a Netflix-style movie recommendation web app built with Streamlit. Search any movie, get smart recommendations, explore trending films, and manage your personal watchlist — all powered by live TMDb data.

---

## 🚀 Features

- 🎯 **Smart Recommendations** — Search any movie and get similar ones based on genres, keywords, cast, and director
- 🔥 **Trending Now** — See what's trending this week, live from TMDb
- 🔍 **Discover** — Search across TMDb's library of 900,000+ titles
- 📋 **Watchlist** — Save movies and watch their trailers directly inside the app
- ⭐ **Rating Filter** — Filter recommendations by minimum IMDb rating
- 🎲 **Surprise Me!** — Get a random movie recommendation instantly
- 🔃 **Sort Options** — Sort by similarity, rating, or release year
- 🎭 **Genre Filter** — Narrow recommendations to specific genres

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Recommendations | Scikit-learn (TF-IDF + Cosine Similarity) |
| Movie Data | TMDb API (live) |
| Caching | Python pickle (local `movie_cache.pkl`) |
| Styling | Custom CSS (Netflix dark theme) |

---

## 📦 Installation

### 1. Clone or download the project

```
Movie_Recommender_App/
├── App.py
├── recommender.py
├── requirements.txt
└── README.md
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run App.py
```

The app will open at `http://localhost:8501` in your browser.

---

## 📋 Requirements

```
streamlit>=1.32.0
requests>=2.31.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

> **Note:** No PyTorch, no ChromaDB, no heavy ML libraries required. Works on any standard Python 3.10+ installation.

---

## 🔑 TMDb API Key

The app uses a TMDb API key stored in `recommender.py`. To use your own key:

1. Sign up at [https://www.themoviedb.org](https://www.themoviedb.org)
2. Go to Settings → API → Request an API Key
3. Replace the key in `recommender.py`:

```python
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "your_api_key_here")
```

Or set it as an environment variable:

```bash
set TMDB_API_KEY=your_api_key_here    # Windows
export TMDB_API_KEY=your_api_key_here # Mac/Linux
```

---

## 🎮 How to Use

1. **Search** a movie title in the sidebar search box
2. **Select** the correct movie from the dropdown
3. Click **🎯 Get Recommendations**
4. Browse your personalized recommendations
5. Use **Sort** and **Filter** options to refine results
6. Click **+ Save** to add movies to your Watchlist
7. In the Watchlist tab, click **▶ Trailer** to watch the trailer inside the app

---

## 📁 File Structure

| File | Description |
|---|---|
| `App.py` | Main Streamlit UI — all pages, tabs, sidebar |
| `recommender.py` | Recommendation engine — TMDb API, TF-IDF, caching |
| `requirements.txt` | Python dependencies |
| `movie_cache.pkl` | Auto-generated local cache (created on first run) |

---

## ⚠️ Troubleshooting

| Error | Fix |
|---|---|
| `ImportError: cannot import fetch_full_movie` | Make sure you're using the latest `recommender.py` |
| `c10.dll failed` | Uninstall torch: `pip uninstall torch torchvision torchaudio -y` |
| `ButtonMixin got unexpected keyword argument` | Upgrade Streamlit: `pip install --upgrade streamlit` |
| App loads but no results | Check your internet connection — app fetches live data |
| Slow on first run | Normal — cache is being built for the first time |

---

## 🙌 Credits

- Movie data provided by [TMDb](https://www.themoviedb.org)
- Built with [Streamlit](https://streamlit.io)
- Recommendations powered by [scikit-learn](https://scikit-learn.org)

---

<p align="center">MADE BY ❤ VICKY RANA</p>
