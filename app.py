from flask import Flask, render_template, request, jsonify
import pickle
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

# Load the movie data and similarity matrix
try:
    movies = pickle.load(open('movie_list.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    print(f"Loaded {len(movies)} movies and similarity matrix")
    
except Exception as e:
    print(f"Error loading data: {e}")
    raise

# Cache for storing poster URLs
poster_cache = {}

def fetch_poster(movie_id):
    # Check cache first
    if movie_id in poster_cache:
        return poster_cache[movie_id]
    
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=68f01f4a95f5a98b77eaec878c214fbe&language=en-US"
    
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = session.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if 'poster_path' in data and data['poster_path']:
            poster_path = data['poster_path']
            full_path = f"https://image.tmdb.org/t/p/w500{poster_path}"
            poster_cache[movie_id] = full_path
            return full_path
        else:
            placeholder = "https://via.placeholder.com/300x450?text=No+Poster+Available"
            poster_cache[movie_id] = placeholder
            return placeholder
            
    except Exception as e:
        print(f"Error fetching poster for movie ID {movie_id}: {str(e)}")
        placeholder = "https://via.placeholder.com/300x450?text=Poster+Unavailable"
        poster_cache[movie_id] = placeholder
        return placeholder

def get_recommendations(movie):
    try:
        index = movies[movies['title'] == movie].index[0]
        distances = sorted(
            list(enumerate(similarity[index])), 
            reverse=True, 
            key=lambda x: x[1]
        )
        
        recommended_movies = []
        for i in distances[1:6]:
            movie_data = {
                'title': str(movies.iloc[i[0]].title),
                'movie_id': int(movies.iloc[i[0]].movie_id),  # Convert to native Python int
                'similarity': float(round(i[1], 3))  # Convert to native Python float
            }
            recommended_movies.append(movie_data)
        
        return recommended_movies
    except IndexError:
        return []
    except Exception as e:
        print(f"Error in get_recommendations: {str(e)}")
        return []

@app.route('/')
def index():
    movie_list = sorted(movies['title'].values)
    return render_template('index.html', movies=movie_list)

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        movie_name = request.form['movie']
        enable_posters = request.form.get('enable_posters') == 'on'
        
        recommendations = get_recommendations(movie_name)
        
        if not recommendations:
            return jsonify({
                'error': 'No recommendations found for this movie',
                'recommendations': [],
                'selected_movie': movie_name,
                'enable_posters': enable_posters
            })
        
        if enable_posters:
            for movie in recommendations:
                movie['poster'] = fetch_poster(movie['movie_id'])
                time.sleep(0.1)  # Small delay to avoid overwhelming the API
        
        return jsonify({
            'recommendations': recommendations,
            'selected_movie': movie_name,
            'enable_posters': enable_posters
        })
    
    except Exception as e:
        print(f"Error in recommend route: {str(e)}")
        return jsonify({
            'error': f'An error occurred: {str(e)}',
            'recommendations': [],
            'selected_movie': request.form.get('movie', ''),
            'enable_posters': False
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
