import os
import time
import base64
import requests
import urllib.parse
from dotenv import load_dotenv
from flask import Flask, request, redirect, jsonify, session, make_response
from flask_cors import CORS
from pymongo import MongoClient
from flask_session import Session
from llm_model import SpotifyManagement

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv('MONGO_URI')
MONGO_CLIENT = os.getenv('MONGO_CLIENT')
MONGO_SESSIONS = os.getenv('MONGO_SESSIONS')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# Spotify API configuration
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# App configuration
app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET', 'RANDOM STRING')
app.config['SESSION_TYPE'] = 'mongodb'
app.config['SESSION_MONGODB'] = MongoClient(MONGO_URI)
app.config['SESSION_MONGODB_DB'] = MONGO_CLIENT
app.config['SESSION_MONGODB_COLLECT'] = MONGO_SESSIONS
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour in seconds
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Initialize session
Session(app)

# Configure CORS
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://localhost:5000"]}}, supports_credentials=True)

# Initialize the Spotify manager
print("Initializing Spotify manager...")
spotify_manager = SpotifyManagement()
print("Generating initial song recommendations, please be patient...\n")
try:
    preloaded_songs = spotify_manager.fetch_user_songs()
    print(f"Generated {len(preloaded_songs)} songs successfully!")
except Exception as e:
    print(f"Error loading songs: {e}")
    preloaded_songs = []

# Middleware equivalent to refresh token if expired
def refresh_token_if_expired():
    if 'token' not in session:
        return None, {"error": "Not authenticated"}, 401
    
    token_data = session['token']
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    expires_in = token_data.get('expires_in', 3600)
    timestamp = token_data.get('timestamp', 0)
    
    # Check if token is expired
    is_expired = time.time() - timestamp > expires_in
    
    if not is_expired:
        # Token is still valid
        return access_token, None, 200
    
    # Token is expired, refresh it
    try:
        auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_header}"
            }
        )
        
        if response.status_code != 200:
            return None, {"error": "Failed to refresh token"}, 400
        
        response_data = response.json()
        
        # Update the session with the new token
        session['token'] = {
            'access_token': response_data['access_token'],
            'refresh_token': refresh_token,  # Spotify may not return a new refresh token
            'expires_in': response_data['expires_in'],
            'timestamp': time.time()
        }
        
        return response_data['access_token'], None, 200
    
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None, {"error": "Failed to refresh token"}, 400

@app.route('/api/check-auth')
def check_auth():
    access_token, error_response, status_code = refresh_token_if_expired()
    if error_response:
        return jsonify(error_response), status_code
    
    return jsonify({
        "authenticated": True,
        "access_token": access_token
    })

@app.route('/api/token')
def get_token():
    access_token, error_response, status_code = refresh_token_if_expired()
    if error_response:
        return jsonify(error_response), status_code
    
    return jsonify({
        "access_token": access_token
    })

@app.route('/login')
def login():
    scope = "user-read-private user-read-email playlist-modify-public playlist-modify-private playlist-read-private"
    
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "scope": scope,
        "redirect_uri": SPOTIFY_REDIRECT_URI
    })
    
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    
    if not code:
        return jsonify({"error": "Authorization code missing"}), 400
    
    try:
        auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "grant_type": "authorization_code"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_header}"
            }
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Authentication failed"}), 400
        
        response_data = response.json()
        
        # Store token information in session
        session['token'] = {
            'access_token': response_data['access_token'],
            'refresh_token': response_data['refresh_token'],
            'expires_in': response_data['expires_in'],
            'timestamp': time.time()
        }
        
        print(f"Access Token: {response_data['access_token'][:10]}...")
        
        # Redirect back to the React app
        return redirect("http://localhost:3000/")
    
    except Exception as e:
        print(f"Error exchanging code for access token: {e}")
        return jsonify({"error": "Authentication failed"}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect("http://localhost:3000/")

@app.route('/api/me')
def get_me():
    access_token, error_response, status_code = refresh_token_if_expired()
    if error_response:
        return jsonify(error_response), status_code
    
    try:
        response = requests.get(
            "https://api.spotify.com/v1/me",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch user data"}), response.status_code
        
        return jsonify(response.json())
    
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return jsonify({"error": "Failed to fetch user data"}), 500

@app.route('/api/playlists')
def get_playlists():
    access_token, error_response, status_code = refresh_token_if_expired()
    if error_response:
        return jsonify(error_response), status_code
    
    try:
        response = requests.get(
            "https://api.spotify.com/v1/me/playlists",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch playlists"}), response.status_code
        
        return jsonify(response.json())
    
    except Exception as e:
        print(f"Error fetching playlists: {e}")
        return jsonify({"error": "Failed to fetch playlists"}), 500

@app.route('/api/recommendations')
def get_recommendations():
    """
    Endpoint to get music recommendations based on user's Spotify playlists
    """
    try:
        return jsonify({
            'status': 'success',
            'data': preloaded_songs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/session-check', methods=['POST'])
def check_session():
    """
    Check if the session is valid and return the token
    """
    if 'token' not in session:
        return jsonify({"error": "No session found"}), 401
    
    token_data = session.get('token', {})
    access_token = token_data.get('access_token')
    
    if not access_token:
        return jsonify({"error": "No token in session"}), 403
    
    return jsonify({
        "message": "Session valid!",
        "access_token": access_token
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT'))
    print(f"Server starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)