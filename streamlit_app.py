import pickle
import streamlit as st
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def fetch_poster(movie_id):
    # Check cache first
    if movie_id in st.session_state.poster_cache:
        return st.session_state.poster_cache[movie_id]
    
    url = "https://api.themoviedb.org/3/movie/{}?api_key=68f01f4a95f5a98b77eaec878c214fbe&language=en-US".format(
        movie_id)
    
    # Create a session with retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        # Add timeout and headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        data = session.get(url, timeout=10, headers=headers)
        data.raise_for_status()  # Raises an HTTPError for bad responses
        data_json = data.json()
        
        if 'poster_path' in data_json and data_json['poster_path']:
            poster_path = data_json['poster_path']
            full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
            # Cache the result
            st.session_state.poster_cache[movie_id] = full_path
            return full_path
        else:
            # Return a placeholder image if poster not found
            placeholder = "https://via.placeholder.com/500x750?text=No+Poster+Available"
            st.session_state.poster_cache[movie_id] = placeholder
            return placeholder
            
    except requests.exceptions.RequestException as e:
        st.warning(f"Failed to fetch poster for movie ID {movie_id}: {str(e)}")
        # Return a placeholder image on error
        placeholder = "https://via.placeholder.com/500x750?text=Poster+Unavailable"
        st.session_state.poster_cache[movie_id] = placeholder
        return placeholder
    except Exception as e:
        st.warning(f"Unexpected error fetching poster: {str(e)}")
        placeholder = "https://via.placeholder.com/500x750?text=Error+Loading+Poster"
        st.session_state.poster_cache[movie_id] = placeholder
        return placeholder


def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(
        list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    
    # Add progress bar for better UX
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, i in enumerate(distances[1:6]):
        # Update progress
        progress = (idx + 1) / 5
        progress_bar.progress(progress)
        status_text.text(f'Fetching poster {idx + 1}/5...')
        
        # fetch the movie poster
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)
        
        # Add small delay between requests to avoid overwhelming the API
        if idx < 4:  # Don't delay after the last request
            time.sleep(0.5)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    return recommended_movie_names, recommended_movie_posters


st.header('Movie Recommender System')

# Initialize session state for caching
if 'poster_cache' not in st.session_state:
    st.session_state.poster_cache = {}

movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

# Add option to disable poster fetching
enable_posters = st.checkbox("Enable poster images (may be slow)", value=True)

if st.button('Show Recommendation'):
    if enable_posters:
        recommended_movie_names, recommended_movie_posters = recommend(selected_movie)
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.text(recommended_movie_names[0])
            st.image(recommended_movie_posters[0])
        with col2:
            st.text(recommended_movie_names[1])
            st.image(recommended_movie_posters[1])
        with col3:
            st.text(recommended_movie_names[2])
            st.image(recommended_movie_posters[2])
        with col4:
            st.text(recommended_movie_names[3])
            st.image(recommended_movie_posters[3])
        with col5:
            st.text(recommended_movie_names[4])
            st.image(recommended_movie_posters[4])
    else:
        # Fast mode without posters
        index = movies[movies['title'] == selected_movie].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        st.subheader("Recommended Movies:")
        for i, distance in enumerate(distances[1:6]):
            movie_name = movies.iloc[distance[0]].title
            similarity_score = distance[1]
            st.write(f"{i+1}. **{movie_name}** (Similarity: {similarity_score:.3f})")
