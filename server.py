import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from recommender_core import (
    search_tmdb_movies,
    fetch_movie_details,
    build_recommendation_scores,
    load_or_fetch_movies,
    get_top_rated_movies,
    get_poster_url,
    get_backdrop_url
)

app = FastAPI(title="CinematicAI - Multi-Page Movie Platform", version="2.5.0")

os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


class UserRating(BaseModel):
    movieId: int
    title: str
    rating: float
    genres: Optional[str] = ""
    overview: Optional[str] = ""


class FilterOptions(BaseModel):
    genre: Optional[str] = "all"
    min_rating: Optional[float] = 0.0
    era: Optional[str] = "all"
    sort_by: Optional[str] = "best_match"


class RecommendRequest(BaseModel):
    user_ratings: List[UserRating]
    filters: Optional[FilterOptions] = None
    n_recommendations: Optional[int] = 12


@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = "templates/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return "<h1>Movie Recommender API Running</h1>"


@app.get("/api/search")
def api_search(q: str = Query(..., min_length=1, description="Movie title search query")):
    results = search_tmdb_movies(q)
    return {"query": q, "results": results, "count": len(results)}


@app.get("/api/trending")
def api_trending(limit: int = 12):
    df = load_or_fetch_movies()
    movies = []
    for _, row in df.head(limit).iterrows():
        mid = int(row["movieId"])
        t = str(row["title"])
        movies.append({
            "movieId": mid,
            "id": mid,
            "title": t,
            "genres": str(row.get("genres", "")).replace("|", " • "),
            "release_year": str(row.get("release_date", ""))[:4] if row.get("release_date") else "N/A",
            "vote_average": round(float(row.get("vote_average", 8.0)), 1),
            "overview": str(row.get("overview", "")),
            "poster_path": get_poster_url(t, row.get("poster_path")),
            "backdrop_path": get_backdrop_url(t, row.get("backdrop_path"))
        })
    return {"trending": movies}


@app.get("/api/top-rated")
def api_top_rated(limit: int = 12):
    top_movies = get_top_rated_movies(limit=limit)
    return {"top_rated": top_movies}


@app.get("/api/movie/{movie_id}")
def api_movie_details(movie_id: int):
    details = fetch_movie_details(movie_id)
    if not details:
        raise HTTPException(status_code=404, detail="Movie details not found")
    return details


@app.post("/api/recommend")
def api_recommend(req: RecommendRequest):
    ratings_dict = [r.dict() for r in req.user_ratings]
    filters_dict = req.filters.dict() if req.filters else {}
    n = req.n_recommendations or 12

    recs = build_recommendation_scores(
        user_ratings=ratings_dict,
        filters=filters_dict,
        n_recommendations=n
    )

    return {
        "recommendations": recs,
        "total": len(recs),
        "user_profile_size": len(ratings_dict)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
