import pandas as pd
import numpy as np
import pickle
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.neighbors import NearestNeighbors
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import matplotlib.colors as mcolors

class SpotifyRecommender:
    def __init__(self):
        self.categorical_features = ['artists', 'artist_ids', 'album'] 
        self.numeric_features = ['duration_ms', 'explicit', 'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness', 'acousticness','instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature','year', 'track_number', 'disc_number'] 
        self.features = self.numeric_features + self.categorical_features
        self.nn_model = None
        self.df = None
        self.feature_matrix = None
        self.preprocessor = None

    def load_data(self, file_path):
        """Load and prepare the Spotify dataset with new structure"""
        print("Loading dataset...")
        self.df = pd.read_csv(file_path)
        self.df.fillna(0, inplace=True)
        
        if 'release_date' in self.df.columns and 'year' not in self.df.columns: # <--- Conversion of release date into datetime formatting
            self.df['year'] = pd.to_datetime(self.df['release_date'], errors='coerce').dt.year
            self.df['year'] = self.df['year'].fillna(0).astype(int)
            
        if 'explicit' in self.df.columns: # <--- Set explicit column to integer type, i.e. boolean value
            self.df['explicit'] = self.df['explicit'].astype(int)
            
        return self.df

    def prepare_preprocessor(self):
        """Create the preprocessing pipeline for new features"""
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), self.numeric_features),
                ('cat', OneHotEncoder(handle_unknown='ignore'), self.categorical_features)
            ]
        )
        return self.preprocessor

    def create_feature_matrix(self):
        """Create a feature matrix for similarity matching with new features"""
        print("Creating feature matrix for song similarity...")
        X = self.df[self.features].copy()  
        
        for feature in self.numeric_features:
            if feature == 'explicit':
                X[feature] = X[feature].astype(int).astype(float)
            else:
                X[feature] = X[feature].astype(float)
        
        
        for feature in self.categorical_features: # <--- Typecast categorical features to string
            X[feature] = X[feature].astype(str)
            
        if self.preprocessor is None:
            print("Preprocessing features...")
            self.prepare_preprocessor()
            self.preprocessor.fit(X)
        
        print("Transforming features...")
        self.feature_matrix = self.preprocessor.transform(X)
            
        print(f"Feature matrix shape: {self.feature_matrix.shape}")
        return self.feature_matrix
    
    def build_similarity_model(self, n_neighbors=20):
        """Build a nearest neighbors model for song recommendations"""
        if self.feature_matrix is None:
            self.create_feature_matrix()
            
        print("Building nearest neighbors model...")
        self.nn_model = NearestNeighbors(n_neighbors=n_neighbors, algorithm='auto', metric='cosine')
        self.nn_model.fit(self.feature_matrix)
            
        print("Nearest neighbors model built successfully!")
        return self.nn_model
        
    def recommend_songs(self, playlist_song_ids, n_recommendations=10, id_column='id'):
        """Recommend songs based on user's playlist songs"""
        if self.nn_model is None:
            self.build_similarity_model()
            
        print(f"Finding songs similar to {len(playlist_song_ids)} playlist tracks...")
        
        playlist_indices = []
        for song_id in playlist_song_ids:
            matching_indices = self.df.index[self.df[id_column] == song_id].tolist()
            if matching_indices:
                playlist_indices.append(matching_indices[0])
        
        if not playlist_indices:
            print("No matching songs found in dataset")
            return []
        
        playlist_features = self.feature_matrix[playlist_indices]
        all_recommendations = []
        for i, song_idx in enumerate(tqdm(playlist_indices, desc="Finding recommendations")):
            song_features = playlist_features[i].reshape(1, -1)
            distances, indices = self.nn_model.kneighbors(song_features, n_neighbors=n_recommendations+1)
            for idx in indices[0][1:]:
                all_recommendations.append(idx)
        
        unique_recommendations = list(set(all_recommendations))
        
        final_recommendations = [idx for idx in unique_recommendations if idx not in playlist_indices]
        
        final_recommendations = final_recommendations[:n_recommendations]
        
        recommended_songs = self.df.iloc[final_recommendations]
        
        print(f"Found {len(recommended_songs)} recommendations")
        return recommended_songs
    
    def recommend_similar_to_playlist(self, playlist_df, n_recommendations=50, id_column='id'):
        """Recommend songs similar to a DataFrame of playlist songs"""
        playlist_song_ids = playlist_df[id_column].tolist()
        return self.recommend_songs(playlist_song_ids, n_recommendations, id_column)
        
    def save_models(self, filename='spotify_recommender.pkl'):
        """Save the trained models"""
        print(f"Saving models to '{filename}'...")
        models_data = {
            'preprocessor': self.preprocessor,
            'nn_model': self.nn_model
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(models_data, f)
            
        print(f"✅ Models saved as '{filename}'")
        
    def load_models(self, filename='spotify_recommender.pkl'):
        """Load saved models"""
        print(f"Loading models from '{filename}'...")
        
        with open(filename, 'rb') as f:
            models_data = pickle.load(f)
            
        self.preprocessor = models_data['preprocessor']
        self.nn_model = models_data['nn_model']
        print("✅ Models loaded successfully")

    def plot_nearest_neighbors_efficient(self, sample_indices=3, n_neighbors=5, features_to_plot=None, sample_size=2000): # <--- This is for personal usage and validation checking, disregard for actual app
        """
        Memory-efficient visualization of nearest neighbors
        
        Parameters:
        -----------
        sample_indices : int or list
            Number of random samples to plot or specific indices of tracks
        n_neighbors : int
            Number of nearest neighbors to find for each sample
        features_to_plot : list
            List of two feature names to use for visualization
        sample_size : int
            Number of random background points to plot (to reduce memory usage)
        """
        if self.nn_model is None:
            print("Please build the similarity model first")
            return
        
        background_indices = np.random.choice(len(self.df), min(sample_size, len(self.df)), replace=False)
    
        if isinstance(sample_indices, int):
            sample_indices = np.random.choice(len(self.df), sample_indices, replace=False)
        
        all_indices = np.unique(np.concatenate([background_indices, np.array(sample_indices)]))
        
        if features_to_plot and len(features_to_plot) == 2 and all(f in self.numeric_features for f in features_to_plot):
            X_subset = self.df.iloc[all_indices][features_to_plot].values
            axis_labels = features_to_plot
        else:
            if hasattr(self.feature_matrix, 'toarray'):
                features_subset = self.feature_matrix[all_indices].toarray()
            else:
                features_subset = self.feature_matrix[all_indices]
                
            print("Performing PCA (Principle Component Analysis) on subset of data...")
            pca = PCA(n_components=2)
            X_subset = pca.fit_transform(features_subset)
            axis_labels = ['PCA Component 1', 'PCA Component 2']
            
        idx_mapping = {original_idx: i for i, original_idx in enumerate(all_indices)}
        
        plt.figure(figsize=(10, 8))
        
        background_subset_indices = [idx_mapping[i] for i in background_indices if i in idx_mapping]
        plt.scatter(
            X_subset[background_subset_indices, 0], 
            X_subset[background_subset_indices, 1], 
            c='lightgrey', alpha=0.3, s=10
        )
        
        colors = list(mcolors.TABLEAU_COLORS)
        
        for i, original_idx in enumerate(sample_indices):
            if original_idx not in idx_mapping:
                continue
                
            subset_idx = idx_mapping[original_idx]
            color = colors[i % len(colors)]
            
            plt.scatter(
                X_subset[subset_idx, 0], 
                X_subset[subset_idx, 1], 
                c=color, s=100, edgecolor='black', zorder=5
            )
            
            _, nn_indices = self.nn_model.kneighbors(
                self.feature_matrix[original_idx].reshape(1, -1), 
                n_neighbors=n_neighbors+1
            )
            
            neighbor_indices = nn_indices[0][1:]
            
            for neighbor_idx in neighbor_indices:
                if neighbor_idx in idx_mapping:
                    neighbor_subset_idx = idx_mapping[neighbor_idx]
                    
                    plt.scatter(
                        X_subset[neighbor_subset_idx, 0], 
                        X_subset[neighbor_subset_idx, 1], 
                        c=color, alpha=0.7, s=50, edgecolor='black'
                    )
                    
                    plt.plot(
                        [X_subset[subset_idx, 0], X_subset[neighbor_subset_idx, 0]],
                        [X_subset[subset_idx, 1], X_subset[neighbor_subset_idx, 1]],
                        c=color, alpha=0.5, linewidth=1
                    )
            
            track_name = self.df.iloc[original_idx]['name']
            plt.annotate(
                track_name[:15] + '...' if len(track_name) > 15 else track_name,
                (X_subset[subset_idx, 0], X_subset[subset_idx, 1]),
                xytext=(5, 5), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7),
                fontsize=8
            )
        
        plt.title('Nearest Neighbors Visualization')
        plt.xlabel(axis_labels[0])
        plt.ylabel(axis_labels[1])
        plt.tight_layout()
        plt.show()
        
        print("\nNote: This visualization is a 2D approximation of high-dimensional space.")
        print("Points that appear close in this visualization may not be actual nearest neighbors.")
        print("This is normal and does not necessarily indicate a problem with your model.")

# Usage example -- will be later integrated into the Flask app
if __name__ == "__main__":
    recommender = SpotifyRecommender()
    
    df = recommender.load_data('./datasets/tracks_features.csv')
    
    print(f"\nDataset loaded: {len(df)} songs")
    
    recommender.build_similarity_model()
    
    recommender.save_models('spotify_recommender.pkl')
    
    # Plotting of model for personal evaluation -- looking for hallucinations
    print("\n --- Plotting Model ---")
    recommender.plot_nearest_neighbors_efficient(sample_indices=20, n_neighbors=40, sample_size=2000)
    
    # Example: Simulate a user's playlist -- simulation to test responsiveness
    sample_playlist = df.sample(10)
    print("\nSample user playlist:")
    print(sample_playlist[['name', 'artists', 'album']])
    
    recommendations = recommender.recommend_similar_to_playlist(sample_playlist, n_recommendations=20, id_column='id')
    
    print("\nRecommended songs:")
    print(recommendations[['name', 'artists', 'album']])
    