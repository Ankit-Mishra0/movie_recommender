import os
import sys
import requests
import pandas as pd
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "a69ec4a9d6e61d5b1d1b6a9ad88cd8ab")
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
MOVIES_CSV = 'datasets/tmdb_movies.csv'


def get_tmdb_movies(num_movies=1000, max_retries=3):
    movies = []
    pages = (num_movies // 20) + 1

    for page in range(1, pages + 1):
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f'{TMDB_BASE_URL}/movie/popular',
                    params={'api_key': TMDB_API_KEY, 'page': page},
                    timeout=10
                )
                response.raise_for_status()
                page_movies = response.json()['results']
                movies.extend(page_movies)

                if len(movies) >= num_movies:
                    break
                break

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
            except requests.exceptions.RequestException:
                break

        if len(movies) >= num_movies:
            break

    return movies[:num_movies]


def save_movies_to_csv(movies, filename):
    movies_data = []
    for movie in movies:
        movies_data.append({
            'movieId': movie['id'],
            'title': movie['title'],
            'genres': get_movie_genres(movie),
            'overview': movie.get('overview', ''),
            'release_date': movie.get('release_date', ''),
            'vote_average': movie.get('vote_average', 0),
            'popularity': movie.get('popularity', 0)
        })

    df = pd.DataFrame(movies_data)
    df.to_csv(filename, index=False)
    return df


def load_movies_from_csv(filename):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return None


def get_movie_genres(movie):
    genre_map = {
        28: 'Action', 12: 'Adventure', 16: 'Animation', 35: 'Comedy',
        80: 'Crime', 99: 'Documentary', 18: 'Drama', 10751: 'Family',
        14: 'Fantasy', 36: 'History', 27: 'Horror', 10402: 'Music',
        9648: 'Mystery', 10749: 'Romance', 878: 'Science Fiction',
        10770: 'TV Movie', 53: 'Thriller', 10752: 'War', 37: 'Western'
    }

    genres = [genre_map.get(genre_id, 'Unknown') for genre_id in movie.get('genre_ids', [])]
    return '|'.join(genres) if genres else 'Unknown'


if __name__ == '__main__':
    force_refresh = '--refresh' in sys.argv

    if not force_refresh and os.path.exists(MOVIES_CSV):
        movies_df = load_movies_from_csv(MOVIES_CSV)
        if movies_df is None or len(movies_df) == 0:
            force_refresh = True
    else:
        force_refresh = True

    if force_refresh:
        tmdb_movies = get_tmdb_movies(1000)

        if not tmdb_movies:
            tmdb_movies = [
                {'id': 1, 'title': 'The Shawshank Redemption', 'genre_ids': [18, 80], 'overview': 'Two imprisoned men bond over a number of years.', 'release_date': '1994-09-23', 'vote_average': 9.3, 'popularity': 100},
                {'id': 2, 'title': 'The Godfather', 'genre_ids': [18, 80], 'overview': 'The aging patriarch of an organized crime dynasty transfers control to his reluctant son.', 'release_date': '1972-03-24', 'vote_average': 9.2, 'popularity': 95},
                {'id': 3, 'title': 'The Dark Knight', 'genre_ids': [28, 80, 18], 'overview': 'When the menace known as the Joker wreaks havoc on the people of Gotham.', 'release_date': '2008-07-18', 'vote_average': 9.0, 'popularity': 90},
                {'id': 4, 'title': 'Pulp Fiction', 'genre_ids': [53, 80], 'overview': 'The lives of two mob hitmen, a boxer, and others intertwine.', 'release_date': '1994-10-14', 'vote_average': 8.9, 'popularity': 85},
                {'id': 5, 'title': 'Forrest Gump', 'genre_ids': [35, 18, 10749], 'overview': 'The presidencies of Kennedy and Johnson, Vietnam, etc.', 'release_date': '1994-07-06', 'vote_average': 8.8, 'popularity': 80},
            ]

        movies_df = save_movies_to_csv(tmdb_movies, MOVIES_CSV)

    if len(movies_df) == 0:
        exit(1)

    user_ratings = []

    for i in range(3):
        movie_input = input(f"Movie {i+1}: ").lower().strip()
        matches = movies_df[movies_df["title"].str.lower().str.contains(movie_input, na=False)]

        if matches.empty:
            continue

        if len(matches) > 1:
            for idx, row in enumerate(matches.head(5).iterrows()):
                actual_idx, movie = row
                print(f"  {idx+1}. {movie['title']}")
            while True:
                try:
                    choice = int(input("Select number (1-5): ")) - 1
                    if 0 <= choice < len(matches.head(5)):
                        selected_movie = matches.iloc[choice]
                        break
                except ValueError:
                    pass
        else:
            selected_movie = matches.iloc[0]

        while True:
            try:
                rating = float(input("Rating (1-5): "))
                if 1 <= rating <= 5:
                    break
            except ValueError:
                pass

        user_ratings.append({
            'movieId': selected_movie['movieId'],
            'title': selected_movie['title'],
            'rating': rating,
            'genres': selected_movie['genres'],
            'overview': selected_movie['overview']
        })

    def get_content_based_recommendations(user_ratings, movies_df, n_recommendations=5):
        movies_df['content'] = movies_df['genres'].fillna('') + ' ' + movies_df['overview'].fillna('')
        rated_movie_ids = [rating['movieId'] for rating in user_ratings]
        candidate_movies = movies_df[~movies_df['movieId'].isin(rated_movie_ids)].copy()

        tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        tfidf_matrix = tfidf.fit_transform(candidate_movies['content'])

        candidate_movies['similarity_score'] = 0.0

        for user_rating in user_ratings:
            if user_rating['rating'] >= 4:
                user_movie_content = user_rating['genres'] + ' ' + user_rating['overview']
                user_vector = tfidf.transform([user_movie_content])
                similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
                weighted_similarities = similarities * user_rating['rating']
                candidate_movies['similarity_score'] += weighted_similarities

        candidate_movies['final_score'] = (
            candidate_movies['similarity_score'] * 0.7 +
            candidate_movies['popularity'] * 0.2 +
            candidate_movies['vote_average'] * 0.1
        )

        recommendations = candidate_movies.nlargest(n_recommendations, 'final_score')
        return recommendations[['title', 'genres', 'release_date', 'vote_average', 'final_score']]

    recommendations = get_content_based_recommendations(user_ratings, movies_df, 5)

    for idx, movie in recommendations.iterrows():
        print(f"📽️  {movie['title']}")
        print(f"   Genres: {movie['genres']}")
