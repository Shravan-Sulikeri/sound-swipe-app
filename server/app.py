from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from llm_model import SpotifyManagement

load_dotenv()

app = Flask(__name__)
CORS(app) 

spotify_manager = SpotifyManagement()

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """
    Endpoint to get music recommendations based on user's Spotify playlists
    """
    try:
        recommendations = spotify_manager.fetch_user_songs()
        
        if not recommendations:
            return jsonify({
                'status': 'error',
                'message': 'Could not generate recommendations',
                'data': []
            }), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Recommendations generated successfully',
            'data': recommendations
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error generating recommendations: {str(e)}',
            'data': []
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)