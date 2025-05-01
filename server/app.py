import os
import time
import base64
import requests
import urllib.parse
import json
import psutil
import tracemalloc
from dotenv import load_dotenv
from flask import Flask, request, redirect, jsonify, session, make_response, Response, stream_with_context, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from flask_session import Session
from llm_model import SpotifyManagement
from llm_model import SpotifyAPI

# Load environment variables
load_dotenv()
REACT_APP = os.getenv('REACT_APP')

# MongoDB configuration
MONGO_URI = os.getenv('MONGO_URI')
MONGO_CLIENT = os.getenv('MONGO_CLIENT')
MONGO_SESSIONS = os.getenv('MONGO_SESSIONS')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
print (SPOTIFY_REDIRECT_URI)

# Spotify API configuration
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# App configuration
app = Flask(__name__, static_folder='../client/build', static_url_path='/')
app.secret_key = os.getenv('SESSION_SECRET', 'RANDOM STRING')
app.config['SESSION_TYPE'] = 'mongodb'
app.config['SESSION_MONGODB'] = MongoClient(MONGO_URI, tls=True,
    tlsAllowInvalidCertificates=True)
app.config['SESSION_MONGODB_DB'] = MONGO_CLIENT
app.config['SESSION_MONGODB_COLLECT'] = MONGO_SESSIONS
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour in seconds
app.config['SESSION_USE_SIGNER'] = True
# Set to True in production with HTTPS
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['PREFERRED_URL_SCHEME'] = 'https'  # Force HTTPS for all URL generation
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit request size to 16MB


# Initialize session
Session(app)

# Configure CORS
CORS(app, resources={
     r"/*": {
         "origins": REACT_APP,
         "supports_credentials": True,
         "allow_headers": ["Content-Type", "Authorization"],
         "expose_headers": ["Content-Type", "X-CSRFToken"],
         "max_age": 600  # Cache preflight requests for 10 minutes
     }
})

requests.adapters.DEFAULT_TIMEOUT = 15

print("Initializing Spotify manager...")
spotify_manager = SpotifyManagement()
print("Login to generate personalized recommendations...\n")

user_recommendation_cache = {}
user_chunking_cache = {}

# Middleware equivalent to refresh token if expired


def refresh_token_if_expired():
    if 'token' not in session:
        return None, {"error": "Not authenticated"}, 401

    token_data = session['token']
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    expires_in = token_data.get('expires_in', 3600)
    timestamp = token_data.get('timestamp', 0)

    is_expired = time.time() - timestamp > expires_in

    if not is_expired:
        return access_token, None, 200

    try:
        auth_header = base64.b64encode(
            f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

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
        session['token'] = {
            'access_token': response_data['access_token'],
            'refresh_token': refresh_token,
            'expires_in': response_data['expires_in'],
            'timestamp': time.time()
        }

        return response_data['access_token'], None, 200

    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None, {"error": "Failed to refresh token"}, 400


def get_user_id(access_token):
    user_response = requests.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if user_response.status_code != 200:
        return jsonify({"error": "Failed to fetch user data"}), user_response.status_code

    user_id = user_response.json().get('id')
    return user_id

# Session handling

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/check-auth')
def check_auth():
    access_token, error_response, status_code = refresh_token_if_expired()
    if error_response:
        return jsonify(error_response), status_code

    return jsonify({
        "authenticated": True,
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

    print(f"Redirecting to Spotify for authentication: {auth_url}")
    return redirect(auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')

    if not code:
        return jsonify({"error": "Authorization code missing"}), 400

    try:
        auth_header = base64.b64encode(
            f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

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
        session['token'] = {
            'access_token': response_data['access_token'],
            'refresh_token': response_data['refresh_token'],
            'expires_in': response_data['expires_in'],
            'timestamp': time.time()
        }

        print(f"Access Token: {response_data['access_token'][:10]}...")
        return redirect(REACT_APP)

    except Exception as e:
        print(f"Error exchanging code for access token: {e}")
        return jsonify({"error": "Authentication failed"}), 400


@app.route('/logout')
def logout():
    session.clear()
    return redirect(REACT_APP)

# user info + setup


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


@app.route('/api/recommendations')
def get_recommendations():
    """
    Endpoint to get music recommendations based on user's Spotify playlists.
    Uses personalized recommendations if user is authenticated.
    """
    try:
        access_token, error_response, status_code = refresh_token_if_expired()

        if error_response:
            return jsonify({"error": "Authentication required for recommendations"}), status_code

        user_id = get_user_id(access_token=access_token)

        if user_id in user_recommendation_cache:
            print(f"Returning cached recommendations for user {user_id}")
            return jsonify({
                'status': 'success',
                'data': user_recommendation_cache[user_id],
                'personalized': True,
                'cached': True
            })

        print(f"Generating personalized recommendations for user {user_id}...")
        user_spotify_manager = SpotifyManagement(user_token=access_token)

        user_songs = user_spotify_manager.fetch_user_songs()

        if not user_songs or len(user_songs) == 0:
            return jsonify({
                'status': 'error',
                'message': 'No recommendations could be generated. Please try again or check your playlists.'
            }), 404

        user_recommendation_cache[user_id] = user_songs

        return jsonify({
            'status': 'success',
            'data': user_songs,
            'personalized': True,
            'cached': False
        })

    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Unable to generate recommendations at this time',
            'error_info': str(e)
        }), 500

@app.route('/api/recommendations-stream')
def get_recommendations_stream():
    try:
        print("New recommendations stream connection received")
        access_token, error_response, status_code = refresh_token_if_expired()

        if error_response:
            print(f"Authentication error in stream: {error_response}")
            return jsonify({"error": "Authentication required for recommendations"}), status_code

        user_id = get_user_id(access_token=access_token)
        
        # Use cached recommendations if available
        if user_id in user_recommendation_cache:
            print(f"Streaming cached recommendations for user {user_id}")
            def stream_cached():
                try:
                    batch = []
                    # Process in smaller batches to reduce memory usage
                    batch_size = 3  # Reduced from 5
                    for track in user_recommendation_cache[user_id]:
                        batch.append(track)
                        if len(batch) == batch_size:
                            yield f"data: {json.dumps(batch)}\n\n"
                            batch = []
                            # Add a small delay to prevent overwhelming the connection
                            time.sleep(0.1)
                    if batch:  # Send any remaining tracks
                        yield f"data: {json.dumps(batch)}\n\n"
                except Exception as e:
                    print(f"Error in cached stream: {str(e)}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return Response(stream_with_context(stream_cached()), mimetype='text/event-stream')

        print(f"Generating and streaming recommendations for user {user_id}")
        user_spotify_manager = SpotifyManagement(user_token=access_token)
        
        # Try-except block to handle potential memory issues
        try:
            tracks_generator = user_spotify_manager.fetch_user_songs_streamed()
            
            def generate():
                batch = []
                full_results = []  # <- For caching
                for track in tracks_generator:
                    batch.append(track)
                    full_results.append(track)
                    if len(batch) == 3:
                        yield f"data: {json.dumps(batch)}\n\n"
                        batch = []
                        time.sleep(0.1)
                if batch:
                    yield f"data: {json.dumps(batch)}\n\n"
                if full_results:
                    user_recommendation_cache[user_id] = full_results
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
            
        except Exception as e:
            print(f"Error preparing tracks generator: {str(e)}")
            return jsonify({"error": "Failed to prepare recommendations", "details": str(e)}), 500
            
    except Exception as e:
        print(f"Critical error in recommendations stream: {str(e)}")
        return Response(f"data: {json.dumps({'error': str(e)})}\n\n", mimetype='text/event-stream')

# playlists


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

        playlists = response.json()['items']
        filtered_playlists = list(filter(
            lambda pl: pl['description'] == 'SoundSwipe created playlist', playlists))

        return jsonify(filtered_playlists)

    except Exception as e:
        print(f"Error fetching playlists: {e}")
        return jsonify({"error": "Failed to fetch playlists"}), 500


@app.route('/api/create-playlist', methods=['POST'])
def create_playlist():
    '''
    Endpoint to create a playlist in spotify for the user
    '''
    try:
        # Get access token or handle expired token
        access_token, error_response, status_code = refresh_token_if_expired()
        if error_response:
            print(f"Authentication error: {error_response}")
            return jsonify({"error": "Authentication required for playlist creation", "details": error_response}), status_code

        print(f"Access token first 10 chars: {access_token[:10]}...")

        # Get user ID
        try:
            user_response = requests.get(
                "https://api.spotify.com/v1/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            print(f"User response status: {user_response.status_code}")

            if user_response.status_code != 200:
                print(f"Failed to get user data: {user_response.text}")
                return jsonify({"error": "Failed to fetch user data", "spotify_error": user_response.text}), user_response.status_code

            user_data = user_response.json()
            user_id = user_data.get('id')
            print(f"User ID: {user_id}")

            if not user_id:
                return jsonify({"error": "Could not determine user ID"}), 400
        except Exception as e:
            print(f"Error getting user ID: {e}")
            return jsonify({"error": "Error fetching user profile"}), 500

        # Get playlist name from request data
        request_data = request.get_json()
        playlist_name = request_data.get('name', 'SoundSwipe Playlist')

        # Now create the playlist
        playlist_url = f"https://api.spotify.com/v1/users/{user_id}/playlists"

        playlist_data = {
            "name": playlist_name,
            "description": "SoundSwipe created playlist",
            "public": False,
        }

        playlist_response = requests.post(
            playlist_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=playlist_data
        )

        if playlist_response.status_code not in [200, 201]:
            return jsonify({
                "error": "Failed to create playlist",
                "status": playlist_response.status_code,
                "spotify_error": playlist_response.text
            }), playlist_response.status_code

        playlist_data = playlist_response.json()
        playlist_id = playlist_data.get('id')
        playlist_url = playlist_data.get('spotify')

        return jsonify({
            'status': 'success',
            'id': playlist_id,
            'name': playlist_data.get('name'),
            'external_url': playlist_data.get('external_urls', {}).get('spotify')
        })

    except Exception as e:
        print(f"Error creating playlist: {e}")
        return jsonify({"error": f"Failed to create playlist: {str(e)}"}), 500


@app.route('/api/delete-playlist', methods=['DELETE'])
def delete_playlist():
    '''
    Endpoint to remove playlist from user profile
    '''
    try:
        # 1. Authentication check
        access_token, error_response, status_code = refresh_token_if_expired()
        if error_response:
            print(f"Authentication error: {error_response}")
            return jsonify({"error": "Authentication required to delete playlist", "details": error_response}), status_code

        # 2. Validate request data
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No data provided"}), 400

        playlist_id = request_data.get('playlist_id')
        if not playlist_id:
            return jsonify({"error": "Playlist ID is required"}), 400

        # 3. Make request to Spotify API
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Note: Spotify doesn't actually have a DELETE endpoint for playlists
        # Instead, we need to unfollow it (which removes it from user's library)
        response = requests.delete(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/followers",
            headers=headers
        )

        # 4. Handle response
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "message": f"Playlist {playlist_id} removed successfully"
            })
        else:
            error_message = response.json().get('error', {}).get('message', 'Unknown error')
            return jsonify({
                "error": "Failed to delete playlist",
                "details": error_message
            }), response.status_code

    except Exception as e:
        print(f"Error deleting playlist: {e}")
        return jsonify({
            "error": "Failed to delete playlist",
            "details": str(e)
        }), 500

# tracks


@app.route('/api/playlist/<playlistId>')
def get_songs(playlistId):
    '''
    Endpoint to get the songs for a given playlist
    '''
    try:
        access_token, error_response, status_code = refresh_token_if_expired()
        if error_response:
            print(f"Authentication error: {error_response}")
            return jsonify({"error": "Authentication required to add tracks", "details": error_response}), status_code

        url = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Make request to Spotify API
        response = requests.get(url, headers=headers)

        if not response.ok:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            return jsonify({'error': error_msg}), response.status_code

        tracks = []
        for item in response.json().get('items', []):
            track = item.get('track', {})
            if not track:
                continue

            try:
                tracks.append({
                    'id': track["id"],
                    'uri': track["uri"],
                    'name': track["name"],
                    'artist': track["artists"][0]["name"] if track.get('artists') else None,
                    'coverImage': track['album']['images'][0]['url'] if track.get('album', {}).get('images') else None,
                })
            except (KeyError, IndexError) as e:
                print(f"Skipping malformed track: {e}")
                continue

        return jsonify({'tracks': tracks}), 200

    except requests.exceptions.RequestException as e:
        print(f'Network error: {e}')
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        print(f'Unexpected error: {e}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/add-track', methods=['POST'])
def add_tracks():
    '''
    Endpoint to add tracks to a user's Spotify playlist
    '''
    try:
        # Get access token or handle expired token
        access_token, error_response, status_code = refresh_token_if_expired()
        if error_response:
            print(f"Authentication error: {error_response}")
            return jsonify({"error": "Authentication required to add tracks", "details": error_response}), status_code

        # Get request data
        request_data = request.get_json()
        playlist_id = request_data.get('playlist_id')
        track_uris = request_data.get('track_uris', [])

        # Validate required data
        if not playlist_id:
            return jsonify({"error": "Missing playlist_id parameter"}), 400
        if not track_uris:
            return jsonify({"error": "No tracks provided to add"}), 400

        # Add tracks to the playlist
        add_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        # Make the API request to add tracks
        add_tracks_response = requests.post(
            add_tracks_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={"uris": track_uris}
        )

        print(f"Add tracks response status: {add_tracks_response.status_code}")

        # Handle response
        if add_tracks_response.status_code not in [200, 201]:
            print(f"Failed to add tracks: {add_tracks_response.text}")
            return jsonify({
                "error": "Failed to add tracks to playlist",
                "status": add_tracks_response.status_code,
                "spotify_error": add_tracks_response.text
            }), add_tracks_response.status_code

        # Return success response
        response_data = add_tracks_response.json()
        return jsonify({
            'status': 'success',
            'playlist_id': playlist_id,
            'tracks_added': len(track_uris),
            'snapshot_id': response_data.get('snapshot_id')
        })

    except Exception as e:
        print(f"Error adding tracks to playlist: {e}")
        return jsonify({"error": f"Failed to add tracks to playlist: {str(e)}"}), 500


@app.route('/api/remove-track', methods=['DELETE'])
def remove_tracks():
    '''
    Endpoint to remove tracks from a user's Spotify playlist
    '''
    try:
        access_token, error_response, status_code = refresh_token_if_expired()
        if error_response:
            print(f"Authentication error: {error_response}")
            return jsonify({"error": "Authentication required to remove tracks", "details": error_response}), status_code

        request_data = request.get_json()
        playlist_id = request_data.get('playlist_id')
        track_uris = request_data.get('track_uris', [])

        if not playlist_id:
            return jsonify({"error": "Missing playlist_id parameter"}), 400
        if not track_uris:
            return jsonify({"error": "No tracks provided to remove"}), 400

        tracks_to_remove = [{"uri": uri} for uri in track_uris]

        remove_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        remove_tracks_response = requests.delete(
            remove_tracks_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={"tracks": tracks_to_remove}
        )

        print(
            f"Remove tracks response status: {remove_tracks_response.status_code}")

        if remove_tracks_response.status_code not in [200, 201]:
            print(f"Failed to remove tracks: {remove_tracks_response.text}")
            return jsonify({
                "error": "Failed to remove tracks from playlist",
                "status": remove_tracks_response.status_code,
                "spotify_error": remove_tracks_response.text
            }), remove_tracks_response.status_code

        response_data = remove_tracks_response.json()
        return jsonify({
            'status': 'success',
            'playlist_id': playlist_id,
            'tracks_removed': len(track_uris),
            'snapshot_id': response_data.get('snapshot_id')
        })

    except Exception as e:
        print(f"Error removing tracks from playlist: {e}")
        return jsonify({"error": f"Failed to remove tracks from playlist: {str(e)}"}), 500


@app.route('/api/search-track', methods=['POST'])
def search_track():
    try:
        # Get access token or handle expired token
        access_token, error_response, status_code = refresh_token_if_expired()
        if error_response:
            print(f"Authentication error: {error_response}")
            return jsonify({"error": "Authentication required for search", "details": error_response}), status_code

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract track and artist information
        track_name = data.get('track')
        artist_name = data.get('artist')

        if not track_name:
            return jsonify({"error": "Track name is required"}), 400

        # Create search query (artist is optional but improves accuracy)
        query = f"track:{track_name}"
        if artist_name:
            query += f" artist:{artist_name}"

        print(f"Searching Spotify for: {query}")

        # Make the search request to Spotify API
        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            params={
                "q": query,
                "type": "track",
                "limit": 1  # Get only the top result
            }
        )

        # Check for errors
        if response.status_code != 200:
            print(
                f"Spotify API error: {response.status_code} - {response.text}")
            return jsonify({
                "error": "Spotify API error",
                "details": response.text
            }), response.status_code

        # Parse the response
        result = response.json()

        # Check if any tracks were found
        if not result.get('tracks', {}).get('items'):
            print(f"No tracks found for query: {query}")
            return jsonify({"message": "No tracks found", "spotifyId": None}), 200

        # Get the first (best match) track
        track = result['tracks']['items'][0]
        spotify_id = track['id']
        track_uri = track['uri']

        print(
            f"Found track: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")

        # Return the Spotify track ID and URI
        return jsonify({
            "spotifyId": spotify_id,
            "uri": track_uri,  # Add the URI which is needed for adding to playlists
            "name": track['name'],
            "artist": track['artists'][0]['name'] if track['artists'] else None,
            "albumArt": track['album']['images'][0]['url'] if track['album']['images'] else None
        }), 200

    except Exception as e:
        print(f"Error in search-track endpoint: {str(e)}")
        return jsonify({"error": "Server error", "details": str(e)}), 500

@app.route('/api/display_name', methods=['GET'])
def get_display_name():
    """
    Endpoint to get the user's Spotify display name using the /me endpoint.
    """
    try:
        access_token, error_response, status_code = refresh_token_if_expired()
        if error_response:
            return jsonify(error_response), status_code
            
        # Make a direct request to Spotify's /me endpoint
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get("https://api.spotify.com/v1/me", headers=headers)
        
        if response.status_code != 200:
            print(f"Error from Spotify API: {response.status_code} - {response.text}")
            return jsonify({"error": "Failed to fetch user profile from Spotify"}), response.status_code
            
        # Extract display_name from the response
        user_data = response.json()
        display_name = user_data.get("display_name", "Spotify User")
        
        # Return the display name in a JSON response
        response = jsonify({"display_name": display_name})
        response.headers['Content-Type'] = 'application/json'
        return response
        
    except Exception as e:
        print(f"Error fetching display name: {e}")
        return jsonify({"error": "Failed to fetch display name", "details": str(e)}), 500

@app.route("/memory")
def memory():
    """
    Get detailed memory usage information for the application process
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    # Format sizes to be more human-readable
    def format_bytes(bytes):
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if bytes < 1024 or unit == 'GB':
                return f"{bytes:.2f} {unit}"
            bytes /= 1024
    
    # Create a dictionary with the memory stats
    memory_stats = {
        "rss": memory_info.rss,
        "rss_human": format_bytes(memory_info.rss),
        "vms": memory_info.vms,
        "vms_human": format_bytes(memory_info.vms),
        "uss": getattr(memory_info, 'uss', 0),  # Unique Set Size (Linux only)
        "uss_human": format_bytes(getattr(memory_info, 'uss', 0)),
        "percent": process.memory_percent(),
    }
    
    # Use jsonify to ensure proper JSON response
    return jsonify(memory_stats)

@app.route("/heap")
def heap():
    """
    Get heap memory tracking information from tracemalloc
    """
    if not tracemalloc.is_tracing():
        return {"error": "tracemalloc is not currently tracing memory allocations"}
    
    current, peak = tracemalloc.get_traced_memory()
    
    # Format sizes to be more human-readable
    def format_bytes(bytes):
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if bytes < 1024 or unit == 'GB':
                return f"{bytes:.2f} {unit}"
            bytes /= 1024
    
    # Get the top 10 memory allocations
    top_stats = tracemalloc.take_snapshot().statistics('lineno')
    top_allocations = []
    for stat in top_stats[:10]:  # Get top 10
        frame = stat.traceback[0]
        filename = os.path.basename(frame.filename)
        top_allocations.append({
            "filename": filename,
            "lineno": frame.lineno,
            "size": stat.size,
            "size_human": format_bytes(stat.size),
            "count": stat.count
        })
    
    return {
        "current_bytes": current,
        "current_human": format_bytes(current),
        "peak_bytes": peak,
        "peak_human": format_bytes(peak),
        "top_allocations": top_allocations
    }

@app.route("/memory/reset")
def reset_memory_tracking():
    """
    Reset the peak memory statistics in tracemalloc
    """
    tracemalloc.clear_traces()
    tracemalloc.reset_peak()
    return {"status": "success", "message": "Memory tracking has been reset"}

@app.route("/memory/recommendations-cache-size")
def cache_size():
    """
    Get information about the size of the recommendation cache
    """
    total_tracks = 0
    users_with_cache = len(user_recommendation_cache)
    
    for user_id, tracks in user_recommendation_cache.items():
        total_tracks += len(tracks)
    
    return {
        "users_with_cache": users_with_cache,
        "total_cached_tracks": total_tracks
    }

@app.route("/memory/clear-cache")
def clear_cache():
    """
    Clear all recommendation caches to free up memory
    """
    global user_recommendation_cache, user_chunking_cache
    
    cache_size_before = len(user_recommendation_cache)
    user_recommendation_cache = {}
    user_chunking_cache = {}
    
    return {
        "status": "success", 
        "message": f"Cleared caches for {cache_size_before} users"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT'))
    print(f"Server starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)