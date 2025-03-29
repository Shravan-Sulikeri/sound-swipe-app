from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from llm_model import SpotifyManagement

load_dotenv()

app = Flask(__name__)
CORS(app) 

# Initialize the Spotify manager and generate songs immediately
print("Initializing Spotify manager...")
spotify_manager = SpotifyManagement()
print("Generating initial song recommendations...")
preloaded_songs = spotify_manager.fetch_user_songs()
print(f"Generated {len(preloaded_songs)} songs successfully!")

@app.route('/api/recommendations', methods=['GET'])
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

@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    """
    Endpoint to get user's Spotify playlists
    """
    try:
        playlists = spotify_manager.recommendation_manager.combinator.spotify_api.fetch_current_user_playlists(
            spotify_manager.recommendation_manager.combinator.token
        )
        
        if not playlists:
            return jsonify({
                'status': 'error',
                'message': 'No playlists found',
                'data': []
            }), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Playlists retrieved successfully',
            'data': playlists
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving playlists: {str(e)}',
            'data': []
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Server starting on port {port}...")
    # Disable debug mode to prevent automatic restarts
    app.run(host='0.0.0.0', port=port, debug=False)