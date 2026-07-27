<div align="center">

# CinematicAI — Next-Gen Movie Recommender & Media Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25%2B-FF4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![TMDB API](https://img.shields.io/badge/TMDB-Live%20Data-01b4e4.svg?style=for-the-badge&logo=themoviedb&logoColor=white)](https://themoviedb.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

_An intelligent, multi-page movie recommendation platform built with TF-IDF content-based vector embeddings, live TMDB API integration for **ANY movie in existence**, explainable AI reasoning, high-res posters, official trailers, and a modern Dark Glassmorphism design system._

</div>

---

## Key Features

- **Universal Search (ANY Movie)**: Live search querying TMDB's full database of 800,000+ movies dynamically.
- **Multi-Factor Explainable AI Engine**: Combines TF-IDF vector similarity across weighted features (Genres, Keywords, Cast & Director, Overview) with user star ratings (1–5★) and TMDB similarity graph boosting.
- **Explainable Reasons**: Every recommendation generates a clear, natural-language rationale (_e.g., "Matched 96% based on your 5★ rating for Inception — shares Mind-Bending Sci-Fi themes, director Christopher Nolan, and action pacing"_).
- **Modern Dark Glassmorphism UI**: 5 SPA pages built with HSL dark mode, CSS backdrop filters, smooth hover animations, and responsive layouts.
- **Authentic TMDB Poster & Backdrop Art**: High-resolution posters (`w500`) and wallpaper backdrops (`w1280`) with native image fallback protection.
- **Interactive Movie Detail Lightbox**: Click any movie to view full overview, release metrics, **embedded YouTube trailers**, and **Director & Lead Cast avatar cards**.
- **My Watchlist & Favorites**: Saved collection with real-time badge updates and `localStorage` persistence.
- **Taste Insights & Metrics**: Visual analytics progress charts showing top genre preferences and rating distribution.

---

## Multi-Page Platform Architecture

The web application features 5 dedicated Single Page Application (SPA) views:

| View Tab                | Description                                                                                                                     |
| :---------------------- | :------------------------------------------------------------------------------------------------------------------------------ |
| **Discover & Trending** | Hero wallpaper banner, popular trending carousel, and top-rated masterpieces spotlight.                                         |
| **AI Recommender**      | Interactive taste builder with universal TMDB search, 5-star ratings, mood chips, filter controls, and explainable match cards. |
| **Catalog Explorer**    | Full database browser with title filter, min rating slider, era selector, and sorting options.                                  |
| **Watchlist**           | Bookmarked favorites drawer synced with persistent browser storage.                                                             |
| **Taste Insights**      | Interactive preference metrics breakdown showing genre distribution and rating statistics.                                      |

---

## Repository Structure

```
movie-recommender/
├── server.py               # FastAPI web server & REST API routes
├── app.py                  # Streamlit application entry point
├── recommender_core.py     # TF-IDF vectorizer engine, TMDB API & scoring logic
├── templates/
│   └── index.html          # Multi-page HTML5 Single Page Application
├── static/
│   ├── css/style.css       # Dark Glassmorphism CSS design system
│   └── js/app.js           # Client-side SPA router, search autocomplete & modal manager
├── datasets/
│   ├── tmdb_movies.csv     # Local offline movie metadata cache
│   └── movies.csv          # Fallback dataset
├── Dockerfile              # Container build definition
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── .gitignore              # Git ignore rules (secrets & temp files protected)
```

---

## Quickstart Guide

### 1. Prerequisites & Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/YOUR_USERNAME/movie-recommender.git
cd movie-recommender

python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

_(Optional)_ Add your free TMDB API key to `.env`:

```env
TMDB_API_KEY=your_tmdb_api_key_here
```

### 3. Run the Application

#### Option A: FastAPI Web App (Recommended)

```bash
python3 server.py
```

Open **`http://localhost:8000`** in your browser.

#### Option B: Streamlit Platform

```bash
streamlit run app.py
```

Open **`http://localhost:8501`** in your browser.

---

## REST API Endpoints

FastAPI exposes clean REST endpoints for integration:

| Method | Endpoint                | Description                                                     |
| :----- | :---------------------- | :-------------------------------------------------------------- |
| `GET`  | `/api/search?q={query}` | Search ANY movie title live via TMDB API                        |
| `GET`  | `/api/trending`         | Fetch popular trending movies with high-res posters             |
| `GET`  | `/api/top-rated`        | Fetch top-rated all-time movies                                 |
| `GET`  | `/api/movie/{id}`       | Fetch deep movie details (director, cast, trailer key)          |
| `POST` | `/api/recommend`        | Post user taste profile & filters to receive AI recommendations |

### Sample Recommendation Payload (`POST /api/recommend`):

```json
{
  "user_ratings": [
    {
      "movieId": 27205,
      "title": "Inception",
      "rating": 5.0,
      "genres": "Action|Science Fiction"
    }
  ],
  "filters": {
    "genre": "Science Fiction",
    "min_rating": 8.0,
    "era": "all",
    "sort_by": "best_match"
  },
  "n_recommendations": 6
}
```

---

## Docker Deployment

Build and run using Docker:

```bash
# Build Docker image
docker build -t cinematic-ai .

# Run container on port 8000
docker run -p 8000:8000 cinematic-ai
```

---

## Cloud Deployment Options

- **Render.com**: Connect GitHub repo, set Build Command to `pip install -r requirements.txt`, and Start Command to `uvicorn server:app --host 0.0.0.0 --port $PORT`.
- **Streamlit Community Cloud**: Connect GitHub repo and set Main file path to `app.py`.

---

## License

Distributed under the MIT License. See `LICENSE` for more details.
