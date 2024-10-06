import pickle
import streamlit as st
from imdb import Cinemagoer
import concurrent.futures
import pandas as pd

# Initialize the Cinemagoer object
ia = Cinemagoer()

# Create a cache for poster URLs
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_poster_url(movie_title):
    try:
        movies = ia.search_movie(movie_title)
        if movies:
            movie = ia.get_movie(movies[0].movieID)
            if movie.get('full-size cover url'):
                return movie['full-size cover url']
            elif movie.get('cover url'):
                return movie['cover url']
    except Exception as e:
        st.error(f"Error fetching poster for {movie_title}: {e}")
    return f"https://via.placeholder.com/500x750/cccccc/000000?text={movie_title}"

def fetch_posters(movie_titles):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        return list(executor.map(get_poster_url, movie_titles))

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    # Get 20 recommended movies
    recommended_movies = [
        (movies.iloc[i[0]].title, get_credits(movies.iloc[i[0]]))
        for i in distances[1:21]
    ]
    recommended_movie_posters = fetch_posters([movie[0] for movie in recommended_movies])
    return recommended_movies, recommended_movie_posters

def get_credits(movie_row):
    """
    Display credits from the credit_cast list.
    This assumes the data is for the selected movie and iterates over cast members.
    """
    credits = []
    for cast_member in credit_cast:
        name = cast_member.get('name', 'Unknown')
        character = cast_member.get('character', 'Unknown')
        credits.append(f"{name} as {character}")
    
    return " | ".join(credits[:5])  # Limit to top 5 credits for brevity

# Load data
@st.cache_resource
def load_data():
    movies = pickle.load(open('movie_list.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    return movies, similarity

# Load the credit_cast data
@st.cache_resource
def load_credits():
    with open('credit_cast.pkl', 'rb') as f:
        return pickle.load(f)

# Custom CSS to increase font size and style
st.markdown("""
<style>
    .big-font {
        font-size:22px !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    .title-font {
        font-size:34px !important;
        font-weight: bold;
        text-align: center;
    }
    .credit-font {
        font-size:16px !important;
        color: #666;
        margin-top: 5px;
        text-align: center;
    }
    .stImage {
        border-radius: 8px;
    }
    .recommendation-section {
        margin-top: 50px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="title-font">Movie Recommender System</p>', unsafe_allow_html=True)

# Load movie data and similarity matrix
movies, similarity = load_data()

# Load credit_cast data
credit_cast = load_credits()

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list,
    help="Choose a movie you like to get similar recommendations."
)

if st.button('Show Recommendation'):
    with st.spinner('Fetching recommendations...'):
        recommended_movies, recommended_movie_posters = recommend(selected_movie)
    
    st.markdown('<div class="recommendation-section">', unsafe_allow_html=True)

    # Display posters in rows of 5 (total of 20 posters)
    for row_start in range(0, 20, 5):
        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                st.markdown(f'<p class="big-font">{recommended_movies[row_start + i][0]}</p>', unsafe_allow_html=True)
                st.image(recommended_movie_posters[row_start + i], use_column_width=True)
                st.markdown(f'<p class="credit-font">Top Cast:<br>{recommended_movies[row_start + i][1]}</p>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.info('This app uses IMDb data to fetch movie posters. Credits for each movie are displayed below the poster.')

# Preload posters for popular movies
@st.cache_data(ttl=86400)  # Cache for 24 hours
def preload_popular_posters():
    popular_movies = movies.sort_values(by='popularity', ascending=False).head(100)['title'].tolist()
    return fetch_posters(popular_movies)

# Run preloading in the background
import threading
threading.Thread(target=preload_popular_posters, daemon=True).start()