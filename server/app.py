import pandas as pd
import pickle
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

print("Loading recommender model...")
recommender = pickle.load(open('spotify_recommender.pkl', 'rb'))
spotify_df = pd.read_csv('./datasets/tracks_features.csv')
spotify_df.fillna(0, inplace=True)
numeric_features = ['duration_ms', 'explicit', 'danceability', 'energy', 'key','loudness', 'mode', 'speechiness', 'acousticness','instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature', 'year', 'track_number', 'disc_number']
categorical_features = ['artists', 'artist_ids', 'album']
features = numeric_features + categorical_features

if 'release_date' in spotify_df.columns and 'year' not in spotify_df.columns:
    spotify_df['year'] = pd.to_datetime(spotify_df['release_date'], errors='coerce').dt.year
    spotify_df['year'] = spotify_df['year'].fillna(0).astype(int)
    
@app.route("/recommend", methods=['POST'])
def recommend():
    """Endpoint for getting song recommendations based on a playlist"""
    try:
        data = request.json
        if 'playlist_ids' in data:
            playlist_ids = data['playlist_ids']
            count = data.get('count', 20)
            id_column = data.get('id_column', 'id') # <--- Updated to use configurable ID column
            
            if 'preprocessor' in recommender and 'nn_model' in recommender:
                playlist_indices = []
                for track_id in playlist_ids:
                    matches = spotify_df.index[spotify_df[id_column] == track_id].tolist()
                    if matches:
                        playlist_indices.append(matches[0])
                        
                if not playlist_indices:
                    return jsonify({"error": "No matching tracks found in dataset"}), 404
                    
                input_features = spotify_df[features].copy()
                
                for feature in numeric_features:
                    if feature == 'explicit':
                        input_features[feature] = input_features[feature].astype(int).astype(float)
                    else:
                        input_features[feature] = input_features[feature].astype(float)
                        
                for feature in categorical_features:
                    input_features[feature] = input_features[feature].astype(str)
                    
                all_features_transformed = recommender['preprocessor'].transform(input_features)
                
                playlist_features = all_features_transformed[playlist_indices]
                
                distances_all = []
                indices_all = []
                for i in range(len(playlist_indices)):
                    song_features = playlist_features[i].reshape(1, -1)
                    distances, indices = recommender['nn_model'].kneighbors(
                        song_features, n_neighbors=count+1
                    )
                    distances_all.extend(distances[0][1:])
                    indices_all.extend(indices[0][1:])
                
                seen = set()
                unique_indices = [x for x in indices_all if not (x in seen or seen.add(x))]
                
                recommendation_indices = [idx for idx in unique_indices if idx not in playlist_indices]
                
                recommendation_indices = recommendation_indices[:count]
                
                recommended_songs = spotify_df.iloc[recommendation_indices]
                
                response_columns = [id_column, 'name', 'artists', 'album']
                
                recommendations = recommended_songs[response_columns].to_dict('records')
                
                return jsonify({
                    "recommendations": recommendations,
                    "count": len(recommendations)
                })
            else:
                return jsonify({"error": "Recommendation model not properly loaded"}), 500
        else:
            return jsonify({"error": "Missing playlist_ids in request"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/tracks", methods=['GET'])
def get_tracks():
    """Endpoint to get a list of tracks (for testing)"""
    try:
        sample_size = int(request.args.get('count', 20))
        sample = spotify_df.sample(sample_size)
        response_columns = ['id', 'name', 'artists', 'album']
        tracks = sample[response_columns].to_dict('records')
        return jsonify({
            "tracks": tracks,
            "count": len(tracks)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)