import os
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "a69ec4a9d6e61d5b1d1b6a9ad88cd8ab")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_BACKDROP_BASE = "https://image.tmdb.org/t/p/w1280"
MOVIES_CSV = "datasets/tmdb_movies.csv"
FALLBACK_MOVIES_CSV = "datasets/movies.csv"

GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}

POSTER_FALLBACKS = {
    "Inception": "https://image.tmdb.org/t/p/w500/oYuLEW9WAFK1PFi23fcrRf2eAQ9.jpg",
    "Interstellar": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
    "The Dark Knight": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
    "The Matrix": "https://image.tmdb.org/t/p/w500/f89U3w9nYiBXwA92zWBYVwvbyh5.jpg",
    "The Shawshank Redemption": "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOZ3quhKhI.jpg",
    "The Godfather": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
    "Fight Club": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
    "Pulp Fiction": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
    "Forrest Gump": "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9LiyvuPhv.jpg",
    "The Lord of the Rings: The Fellowship of the Ring": "https://image.tmdb.org/t/p/w500/6oom5WUlCTTM101ZRIkM1neTxNy.jpg",
    "Dune: Part Two": "https://image.tmdb.org/t/p/w500/1pdfLPoWuVzhAcStTWySizKGTTz.jpg",
    "Everything Everywhere All at Once": "https://image.tmdb.org/t/p/w500/7WsyChLLEzcqIFv2dF2vmy4crJF.jpg",
    "Toy Story": "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
    "Avengers: Endgame": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9v1chvyBsL.jpg",
    "Spider-Man: Into the Spider-Verse": "https://image.tmdb.org/t/p/w500/iiZZdoQHee21W5WccxWjXmCccKV.jpg",
    "Oppenheimer": "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGvC2G1WScW.jpg",
    "Parasite": "https://image.tmdb.org/t/p/w500/7IiTqvZteU0D28aEXwHqP19jKzH.jpg"
}

BACKDROP_FALLBACKS = {
    "Inception": "https://image.tmdb.org/t/p/w1280/8ZTVqvKDQ8emSGUEMjsS4yHAiW5.jpg",
    "Interstellar": "https://image.tmdb.org/t/p/w1280/xJHokMbljvjADYdit5fKSuVftv.jpg",
    "The Dark Knight": "https://image.tmdb.org/t/p/w1280/hkBaD2BoFJistfsH2eWjJRjEVカ.jpg",
    "Dune: Part Two": "https://image.tmdb.org/t/p/w1280/xOM08Go8fG7W2vF4uQI0x2LIs0c.jpg",
    "Oppenheimer": "https://image.tmdb.org/t/p/w1280/fm6K8Oi23Nm9vpyT6uRSd25yIkT.jpg"
}

DETAILS_CACHE: Dict[int, Dict[str, Any]] = {}


def get_poster_url(title: str, path: Optional[str]) -> str:
    if path and isinstance(path, str) and path.startswith("/"):
        return f"{TMDB_IMAGE_BASE}{path}"
    if path and isinstance(path, str) and path.startswith("http"):
        return path
    if title in POSTER_FALLBACKS:
        return POSTER_FALLBACKS[title]
    return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80"


def get_backdrop_url(title: str, path: Optional[str]) -> str:
    if path and isinstance(path, str) and path.startswith("/"):
        return f"{TMDB_BACKDROP_BASE}{path}"
    if path and isinstance(path, str) and path.startswith("http"):
        return path
    if title in BACKDROP_FALLBACKS:
        return BACKDROP_FALLBACKS[title]
    return "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?w=1280&q=80"


def format_genres(genre_ids_or_list: Any) -> str:
    if isinstance(genre_ids_or_list, list):
        if len(genre_ids_or_list) > 0 and isinstance(genre_ids_or_list[0], dict):
            return "|".join([g.get("name", "") for g in genre_ids_or_list if g.get("name")])
        genres = [GENRE_MAP.get(gid, "Unknown") for gid in genre_ids_or_list if isinstance(gid, int)]
        return "|".join([g for g in genres if g != "Unknown"]) if genres else "General"
    elif isinstance(genre_ids_or_list, str):
        return genre_ids_or_list
    return "General"


def search_tmdb_movies(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    query = query.strip()
    if not query:
        return []

    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={"api_key": TMDB_API_KEY, "query": query, "include_adult": False, "language": "en-US"},
            timeout=5
        )
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                formatted = []
                for m in results[:limit]:
                    title = m.get("title", "")
                    poster = get_poster_url(title, m.get("poster_path"))
                    backdrop = get_backdrop_url(title, m.get("backdrop_path"))
                    formatted.append({
                        "movieId": int(m["id"]),
                        "id": int(m["id"]),
                        "title": title,
                        "release_date": m.get("release_date", ""),
                        "release_year": m.get("release_date", "")[:4] if m.get("release_date") else "N/A",
                        "vote_average": float(m.get("vote_average", 0.0)),
                        "popularity": float(m.get("popularity", 0.0)),
                        "overview": m.get("overview", ""),
                        "genres": format_genres(m.get("genre_ids", [])),
                        "poster_path": poster,
                        "backdrop_path": backdrop,
                        "source": "tmdb"
                    })
                return formatted
    except Exception:
        pass

    local_results = []
    if os.path.exists(MOVIES_CSV):
        try:
            df = pd.read_csv(MOVIES_CSV)
            matches = df[df["title"].str.contains(query, case=False, na=False)].head(limit)
            for _, row in matches.iterrows():
                t = str(row["title"])
                local_results.append({
                    "movieId": int(row["movieId"]),
                    "id": int(row["movieId"]),
                    "title": t,
                    "release_date": str(row.get("release_date", "")),
                    "release_year": str(row.get("release_date", ""))[:4] if row.get("release_date") else "N/A",
                    "vote_average": float(row.get("vote_average", 7.5)),
                    "popularity": float(row.get("popularity", 50.0)),
                    "overview": str(row.get("overview", "")),
                    "genres": str(row.get("genres", "Drama")),
                    "poster_path": get_poster_url(t, row.get("poster_path")),
                    "backdrop_path": get_backdrop_url(t, row.get("backdrop_path")),
                    "source": "local"
                })
        except Exception:
            pass

    if not local_results and os.path.exists(FALLBACK_MOVIES_CSV):
        try:
            df_fall = pd.read_csv(FALLBACK_MOVIES_CSV)
            matches = df_fall[df_fall["title"].str.contains(query, case=False, na=False)].head(limit)
            for _, row in matches.iterrows():
                t = str(row["title"])
                year_match = re.search(r'\((\d{4})\)', t)
                year = year_match.group(1) if year_match else "N/A"
                clean_t = re.sub(r'\s*\(\d{4}\)', '', t).strip()
                local_results.append({
                    "movieId": int(row["movieId"]),
                    "id": int(row["movieId"]),
                    "title": clean_t,
                    "release_date": year,
                    "release_year": year,
                    "vote_average": 7.5,
                    "popularity": 40.0,
                    "overview": f"A classic movie in {str(row.get('genres', '')).replace('|', ', ')}.",
                    "genres": str(row.get("genres", "")).replace("|", " | "),
                    "poster_path": get_poster_url(clean_t, None),
                    "backdrop_path": get_backdrop_url(clean_t, None),
                    "source": "local_fallback"
                })
        except Exception:
            pass

    return local_results[:limit]


def fetch_movie_details(movie_id: int) -> Dict[str, Any]:
    if movie_id in DETAILS_CACHE:
        return DETAILS_CACHE[movie_id]

    default_details = {
        "id": movie_id,
        "movieId": movie_id,
        "title": "Movie Details",
        "overview": "",
        "tagline": "",
        "genres": "Drama",
        "director": "Unknown Director",
        "cast": [],
        "keywords": [],
        "trailer_key": None,
        "poster_path": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80",
        "backdrop_path": "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?w=1280&q=80",
        "vote_average": 7.5,
        "release_date": "",
        "runtime": 120,
        "similar_ids": []
    }

    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{movie_id}",
            params={
                "api_key": TMDB_API_KEY,
                "append_to_response": "keywords,credits,videos,similar,recommendations"
            },
            timeout=6
        )
        if response.status_code == 200:
            data = response.json()
            title = data.get("title", "")
            
            crew = data.get("credits", {}).get("crew", [])
            directors = [c.get("name") for c in crew if c.get("job") == "Director"]
            director_name = ", ".join(directors) if directors else "Unknown"

            raw_cast = data.get("credits", {}).get("cast", [])[:6]
            cast_list = [
                {
                    "name": c.get("name"),
                    "character": c.get("character"),
                    "profile_path": f"{TMDB_IMAGE_BASE}{c.get('profile_path')}" if c.get("profile_path") else "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&q=80"
                }
                for c in raw_cast
            ]

            raw_kw = data.get("keywords", {}).get("keywords", []) or data.get("keywords", {}).get("results", [])
            keywords = [k.get("name") for k in raw_kw[:8]]

            videos = data.get("videos", {}).get("results", [])
            trailers = [v.get("key") for v in videos if v.get("type") == "Trailer" and v.get("site") == "YouTube"]
            trailer_key = trailers[0] if trailers else (videos[0].get("key") if videos else None)

            rec_movies = data.get("recommendations", {}).get("results", []) or data.get("similar", {}).get("results", [])
            similar_ids = [m.get("id") for m in rec_movies if m.get("id")]

            details = {
                "id": movie_id,
                "movieId": movie_id,
                "title": title,
                "overview": data.get("overview", ""),
                "tagline": data.get("tagline", ""),
                "genres": format_genres(data.get("genres", [])),
                "director": director_name,
                "cast": cast_list,
                "keywords": keywords,
                "trailer_key": trailer_key,
                "poster_path": get_poster_url(title, data.get("poster_path")),
                "backdrop_path": get_backdrop_url(title, data.get("backdrop_path")),
                "vote_average": float(data.get("vote_average", 0.0)),
                "release_date": data.get("release_date", ""),
                "release_year": data.get("release_date", "")[:4] if data.get("release_date") else "N/A",
                "runtime": data.get("runtime", 0),
                "popularity": float(data.get("popularity", 0.0)),
                "similar_ids": similar_ids
            }
            DETAILS_CACHE[movie_id] = details
            return details
    except Exception:
        pass

    return default_details


def load_or_fetch_movies(force_refresh: bool = False) -> pd.DataFrame:
    os.makedirs("datasets", exist_ok=True)
    if not force_refresh and os.path.exists(MOVIES_CSV):
        try:
            df = pd.read_csv(MOVIES_CSV)
            if not df.empty and len(df) >= 5:
                return df
        except Exception:
            pass

    fallback = [
        {"movieId": 27205, "id": 27205, "title": "Inception", "genres": "Action|Science Fiction|Thriller", "overview": "Cobb, a skilled thief who commits corporate espionage by infiltrating subconscious dreams.", "release_date": "2010-07-16", "vote_average": 8.8, "popularity": 120.0, "poster_path": POSTER_FALLBACKS["Inception"], "backdrop_path": BACKDROP_FALLBACKS["Inception"]},
        {"movieId": 157336, "id": 157336, "title": "Interstellar", "genres": "Adventure|Drama|Science Fiction", "overview": "A team of explorers travel through a wormhole in space to ensure humanity's survival.", "release_date": "2014-11-05", "vote_average": 8.4, "popularity": 110.0, "poster_path": POSTER_FALLBACKS["Interstellar"], "backdrop_path": BACKDROP_FALLBACKS["Interstellar"]},
        {"movieId": 155, "id": 155, "title": "The Dark Knight", "genres": "Action|Crime|Drama", "overview": "Batman accepts one of the greatest psychological and physical tests of his ability to fight injustice.", "release_date": "2008-07-16", "vote_average": 8.5, "popularity": 105.0, "poster_path": POSTER_FALLBACKS["The Dark Knight"], "backdrop_path": BACKDROP_FALLBACKS["The Dark Knight"]},
        {"movieId": 693134, "id": 693134, "title": "Dune: Part Two", "genres": "Science Fiction|Adventure", "overview": "Paul Atreides unites with Chani and the Fremen while seeking revenge against conspirators.", "release_date": "2024-02-27", "vote_average": 8.2, "popularity": 130.0, "poster_path": POSTER_FALLBACKS["Dune: Part Two"], "backdrop_path": BACKDROP_FALLBACKS["Dune: Part Two"]},
        {"movieId": 872585, "id": 872585, "title": "Oppenheimer", "genres": "Drama|History", "overview": "The story of American scientist J. Robert Oppenheimer and his role in the Manhattan Project.", "release_date": "2023-07-19", "vote_average": 8.1, "popularity": 115.0, "poster_path": POSTER_FALLBACKS["Oppenheimer"], "backdrop_path": BACKDROP_FALLBACKS["Oppenheimer"]},
        {"movieId": 603, "id": 603, "title": "The Matrix", "genres": "Action|Science Fiction", "overview": "A computer hacker learns from mysterious rebels about the true nature of his reality.", "release_date": "1999-03-31", "vote_average": 8.2, "popularity": 95.0, "poster_path": POSTER_FALLBACKS["The Matrix"]},
        {"movieId": 278, "id": 278, "title": "The Shawshank Redemption", "genres": "Drama|Crime", "overview": "Two imprisoned men bond over a number of years, finding solace and eventual redemption.", "release_date": "1994-09-23", "vote_average": 8.7, "popularity": 100.0, "poster_path": POSTER_FALLBACKS["The Shawshank Redemption"]},
        {"movieId": 238, "id": 238, "title": "The Godfather", "genres": "Drama|Crime", "overview": "The aging patriarch of an organized crime dynasty transfers control of his empire.", "release_date": "1972-03-14", "vote_average": 8.7, "popularity": 98.0, "poster_path": POSTER_FALLBACKS["The Godfather"]},
        {"movieId": 550, "id": 550, "title": "Fight Club", "genres": "Drama", "overview": "An office worker forms an underground fight club that evolves into something much more.", "release_date": "1999-10-15", "vote_average": 8.4, "popularity": 90.0, "poster_path": POSTER_FALLBACKS["Fight Club"]},
        {"movieId": 680, "id": 680, "title": "Pulp Fiction", "genres": "Thriller|Crime", "overview": "The lives of mob hitmen, a boxer, and a gangster's wife intertwine.", "release_date": "1994-09-10", "vote_average": 8.5, "popularity": 88.0, "poster_path": POSTER_FALLBACKS["Pulp Fiction"]},
        {"movieId": 13, "id": 13, "title": "Forrest Gump", "genres": "Comedy|Drama|Romance", "overview": "The presidencies of Kennedy and Johnson, the Vietnam War, and other historical events unfold.", "release_date": "1994-06-23", "vote_average": 8.5, "popularity": 85.0, "poster_path": POSTER_FALLBACKS["Forrest Gump"]},
        {"movieId": 545611, "id": 545611, "title": "Everything Everywhere All at Once", "genres": "Action|Adventure|Science Fiction", "overview": "A middle-aged Chinese immigrant is swept up into an insane adventure in the multiverse.", "release_date": "2022-03-11", "vote_average": 7.8, "popularity": 80.0, "poster_path": POSTER_FALLBACKS["Everything Everywhere All at Once"]}
    ]
    df = pd.DataFrame(fallback)
    df.to_csv(MOVIES_CSV, index=False)
    return df


def get_top_rated_movies(limit: int = 12) -> List[Dict[str, Any]]:
    try:
        res = requests.get(
            f"{TMDB_BASE_URL}/movie/top_rated",
            params={"api_key": TMDB_API_KEY, "page": 1, "language": "en-US"},
            timeout=5
        )
        if res.status_code == 200:
            movies = res.json().get("results", [])[:limit]
            formatted = []
            for m in movies:
                t = m.get("title", "")
                formatted.append({
                    "movieId": int(m["id"]),
                    "id": int(m["id"]),
                    "title": t,
                    "release_year": m.get("release_date", "")[:4] if m.get("release_date") else "N/A",
                    "vote_average": round(float(m.get("vote_average", 0)), 1),
                    "genres": format_genres(m.get("genre_ids", [])),
                    "overview": m.get("overview", ""),
                    "poster_path": get_poster_url(t, m.get("poster_path")),
                    "backdrop_path": get_backdrop_url(t, m.get("backdrop_path"))
                })
            return formatted
    except Exception:
        pass

    df = load_or_fetch_movies()
    sorted_df = df.sort_values(by="vote_average", ascending=False).head(limit)
    res_list = []
    for _, row in sorted_df.iterrows():
        t = str(row["title"])
        res_list.append({
            "movieId": int(row["movieId"]),
            "id": int(row["movieId"]),
            "title": t,
            "release_year": str(row.get("release_date", ""))[:4] if row.get("release_date") else "N/A",
            "vote_average": float(row.get("vote_average", 8.5)),
            "genres": str(row.get("genres", "")).replace("|", " • "),
            "overview": str(row.get("overview", "")),
            "poster_path": get_poster_url(t, row.get("poster_path")),
            "backdrop_path": get_backdrop_url(t, row.get("backdrop_path"))
        })
    return res_list


def build_recommendation_scores(
    user_ratings: List[Dict[str, Any]],
    movies_df: Optional[pd.DataFrame] = None,
    filters: Optional[Dict[str, Any]] = None,
    n_recommendations: int = 12
) -> List[Dict[str, Any]]:
    if not user_ratings:
        return []

    if movies_df is None or movies_df.empty:
        movies_df = load_or_fetch_movies()

    filters = filters or {}
    rated_ids = {int(r["movieId"]) for r in user_ratings}

    candidate_dict: Dict[int, Dict[str, Any]] = {}

    for _, row in movies_df.iterrows():
        mid = int(row["movieId"])
        t = str(row["title"])
        if mid not in rated_ids:
            candidate_dict[mid] = {
                "id": mid,
                "movieId": mid,
                "title": t,
                "genres": str(row.get("genres", "General")),
                "overview": str(row.get("overview", "")),
                "release_date": str(row.get("release_date", "")),
                "vote_average": float(row.get("vote_average", 7.0)),
                "popularity": float(row.get("popularity", 50.0)),
                "poster_path": get_poster_url(t, row.get("poster_path")),
                "backdrop_path": get_backdrop_url(t, row.get("backdrop_path")),
                "tmdb_graph_boost": 0.0
            }

    high_rated = [r for r in user_ratings if r.get("rating", 3) >= 4]
    if not high_rated:
        high_rated = user_ratings

    for user_item in high_rated:
        umid = int(user_item["movieId"])
        details = fetch_movie_details(umid)
        user_item["director"] = details.get("director", "Unknown")
        user_item["keywords"] = details.get("keywords", [])

        for sim_id in details.get("similar_ids", [])[:15]:
            if sim_id not in rated_ids:
                sim_details = fetch_movie_details(sim_id)
                if sim_details and sim_details.get("title"):
                    if sim_id not in candidate_dict:
                        candidate_dict[sim_id] = sim_details
                        candidate_dict[sim_id]["tmdb_graph_boost"] = 0.25
                    else:
                        candidate_dict[sim_id]["tmdb_graph_boost"] += 0.15

    candidates = list(candidate_dict.values())
    if not candidates:
        return []

    def build_feature_text(item: Dict[str, Any]) -> str:
        genres = str(item.get("genres", "")).replace("|", " ")
        overview = str(item.get("overview", ""))
        keywords = " ".join(item.get("keywords", [])) if isinstance(item.get("keywords"), list) else ""
        director = str(item.get("director", ""))
        cast_names = " ".join([c["name"] for c in item.get("cast", []) if isinstance(c, dict) and "name" in c])
        return f"{genres} {genres} {keywords} {keywords} {director} {director} {cast_names} {overview}"

    candidate_texts = [build_feature_text(c) for c in candidates]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=8000)
    try:
        candidate_tfidf = vectorizer.fit_transform(candidate_texts)
    except Exception:
        return []

    num_candidates = len(candidates)
    similarity_scores = [0.0] * num_candidates
    driver_matches: List[Dict[str, Any]] = [{} for _ in range(num_candidates)]

    for user_item in user_ratings:
        rating = float(user_item.get("rating", 3.0))
        if rating >= 5.0: weight = 1.0
        elif rating >= 4.0: weight = 0.7
        elif rating >= 3.0: weight = 0.3
        else: weight = -0.5

        u_text = f"{user_item.get('genres', '').replace('|', ' ')} {user_item.get('overview', '')} {user_item.get('director', '')} {' '.join(user_item.get('keywords', []))}"
        u_vec = vectorizer.transform([u_text])
        sims = cosine_similarity(u_vec, candidate_tfidf).flatten()

        for idx in range(num_candidates):
            added_sim = sims[idx] * weight
            similarity_scores[idx] += added_sim

            if weight > 0 and sims[idx] > driver_matches[idx].get("score", 0.0):
                driver_matches[idx] = {
                    "score": float(sims[idx]),
                    "user_movie": user_item.get("title", ""),
                    "user_rating": rating,
                    "user_genres": user_item.get("genres", ""),
                    "user_director": user_item.get("director", "Unknown"),
                    "user_keywords": user_item.get("keywords", [])
                }

    max_sim = max(max(similarity_scores), 0.001)
    results = []

    for idx, c in enumerate(candidates):
        raw_sim = max(similarity_scores[idx], 0.0)
        norm_sim = raw_sim / max_sim
        graph_boost = c.get("tmdb_graph_boost", 0.0)
        rating_score = float(c.get("vote_average", 7.0)) / 10.0
        pop_score = min(float(c.get("popularity", 50.0)) / 200.0, 1.0)

        final_score = (norm_sim * 0.60) + (graph_boost * 0.20) + (rating_score * 0.12) + (pop_score * 0.08)
        match_percentage = min(max(int(final_score * 100), 62), 99)

        genre_filter = filters.get("genre")
        if genre_filter and genre_filter.lower() != "all":
            if genre_filter.lower() not in str(c.get("genres", "")).lower():
                continue

        min_rating = float(filters.get("min_rating", 0.0))
        if float(c.get("vote_average", 0.0)) < min_rating:
            continue

        era_filter = filters.get("era")
        rel_year = c.get("release_year") or (c.get("release_date", "")[:4] if c.get("release_date") else "N/A")
        if era_filter and era_filter != "all" and rel_year != "N/A":
            try:
                y = int(rel_year)
                if era_filter == "2020s" and not (2020 <= y <= 2029): continue
                if era_filter == "2010s" and not (2010 <= y <= 2019): continue
                if era_filter == "2000s" and not (2000 <= y <= 2009): continue
                if era_filter == "1990s" and not (1990 <= y <= 1999): continue
                if era_filter == "classic" and y >= 1990: continue
            except ValueError:
                pass

        drv = driver_matches[idx]
        user_movie_title = drv.get("user_movie")
        reason_parts = []

        if user_movie_title:
            reason_parts.append(f"Recommended because you loved **{user_movie_title}** ({int(drv.get('user_rating', 5))}★).")
        
        c_director = c.get("director", "")
        if c_director and c_director != "Unknown" and c_director == drv.get("user_director"):
            reason_parts.append(f"Also directed by **{c_director}**.")
        
        c_genres = set(str(c.get("genres", "")).split("|"))
        u_genres = set(str(drv.get("user_genres", "")).split("|"))
        common_genres = [g for g in c_genres.intersection(u_genres) if g and g != "General"]
        
        if common_genres:
            reason_parts.append(f"Shares the **{', '.join(common_genres[:2])}** genre signature.")
        else:
            primary_g = str(c.get("genres", "")).split("|")[0]
            reason_parts.append(f"Top-tier entry in **{primary_g}**.")

        if float(c.get("vote_average", 0)) >= 8.0:
            reason_parts.append(f"Acclaimed by audiences with a **{c.get('vote_average'):.1f}/10** score.")

        explanation_text = " ".join(reason_parts)
        poster = get_poster_url(c["title"], c.get("poster_path"))
        backdrop = get_backdrop_url(c["title"], c.get("backdrop_path"))
        
        results.append({
            "movieId": int(c["id"]),
            "id": int(c["id"]),
            "title": str(c["title"]),
            "genres": str(c.get("genres", "General")).replace("|", " • "),
            "release_date": str(c.get("release_date", "")),
            "release_year": rel_year,
            "vote_average": round(float(c.get("vote_average", 0.0)), 1),
            "popularity": round(float(c.get("popularity", 0.0)), 1),
            "overview": str(c.get("overview", "")),
            "poster_path": poster,
            "backdrop_path": backdrop,
            "match_percentage": match_percentage,
            "final_score": round(float(final_score), 4),
            "reason": explanation_text,
            "driver_movie": user_movie_title or "Your taste profile",
            "director": c.get("director", "Unknown"),
            "cast": c.get("cast", []),
            "keywords": c.get("keywords", []),
            "trailer_key": c.get("trailer_key"),
            "sub_scores": {
                "content_similarity": min(int(norm_sim * 100), 99),
                "audience_rating": min(int((float(c.get("vote_average", 7.0)) / 10.0) * 100), 100),
                "graph_connection": 90 if graph_boost > 0 else 60
            }
        })

    sort_by = filters.get("sort_by", "best_match")
    if sort_by == "rating":
        results.sort(key=lambda x: x["vote_average"], reverse=True)
    elif sort_by == "latest":
        results.sort(key=lambda x: x["release_year"], reverse=True)
    elif sort_by == "popularity":
        results.sort(key=lambda x: x["popularity"], reverse=True)
    else:
        results.sort(key=lambda x: x["match_percentage"], reverse=True)

    return results[:n_recommendations]
