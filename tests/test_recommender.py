import pandas as pd

from recommender_core import build_recommendation_scores


def test_build_recommendation_scores_prioritizes_similar_content():
    movies_df = pd.DataFrame(
        [
            {
                "movieId": 1,
                "title": "Inception",
                "genres": "Action|Sci-Fi",
                "overview": "A thief enters dreams to steal secrets.",
                "release_date": "2010-07-16",
                "vote_average": 8.8,
                "popularity": 85,
            },
            {
                "movieId": 2,
                "title": "The Dark Knight",
                "genres": "Action|Crime",
                "overview": "Batman faces the Joker in Gotham.",
                "release_date": "2008-07-18",
                "vote_average": 8.9,
                "popularity": 90,
            },
            {
                "movieId": 3,
                "title": "The Notebook",
                "genres": "Romance|Drama",
                "overview": "A young couple falls in love in the 1940s.",
                "release_date": "2004-06-25",
                "vote_average": 7.8,
                "popularity": 70,
            },
        ]
    )

    user_ratings = [
        {
            "movieId": 1,
            "title": "Inception",
            "rating": 5,
            "genres": "Action|Sci-Fi",
            "overview": "A thief enters dreams to steal secrets.",
        }
    ]

    recommendations = build_recommendation_scores(user_ratings, movies_df, n_recommendations=2)

    assert not recommendations.empty
    assert recommendations.iloc[0]["title"] == "The Dark Knight"
    assert recommendations.iloc[0]["final_score"] >= recommendations.iloc[1]["final_score"]
    assert "reason" in recommendations.columns
    assert "Action" in recommendations.iloc[0]["reason"] or "Sci-Fi" in recommendations.iloc[0]["reason"]
