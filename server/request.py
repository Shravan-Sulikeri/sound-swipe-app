import requests
import json
import pandas as pd

# API URL
base_url = 'http://127.0.0.1:5000'

def get_sample_tracks(count=10):
    """Get sample tracks from the API for testing"""
    url = f'{base_url}/tracks?count={count}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['tracks']
    else:
        print("Error:", response.status_code)
        print(response.text)
        return []

def get_recommendations(playlist_ids, count=20):
    """Get song recommendations based on playlist IDs"""
    url = f'{base_url}/recommend'
    data = {
        'playlist_ids': playlist_ids,
        'count': count,
        'id_column': 'id'  
    }
    response = requests.post(url, json=data)
    
    playlist = get_sample_tracks(input("Enter the number of songs you want to add to your playlist: "))
    print("\nYOUR PLAYLIST:")
    playlist_ids = []
    for i, track in enumerate(playlist):
        print(f"{i+1}. {track['name']} by {track['artists']} - {track['album']}")
        playlist_ids.append(track['id'])
    
    if response.status_code == 200:
        recommendations = response.json()
        print(f'Received {recommendations["count"]} recommendations')
        print("\nRECOMMENDED SONGS:")
        for i, track in enumerate(recommendations['recommendations']):
            print(f"{i+1}. {track['name']} by {track['artists']} - {track['album']}")
        return recommendations['recommendations']
    else:
        print("Error:", response.status_code)
        print(response.text)
        return []

def simulate_tinder_for_songs(): # <--- Simulate for testing out the typical app flow, not for actual use
    """Simulate the Tinder-like song recommendation flow"""
    print("\n=== TINDER FOR SPOTIFY SONGS SIMULATION ===\n")
    
    # 1. Get some sample tracks to create an initial "playlist"
    print("Step 1: Getting sample tracks to create an initial playlist...")
    sample_tracks = get_sample_tracks(10)
    if not sample_tracks:
        print("Failed to get sample tracks")
        return
    
    # 2. Show the user's "playlist"
    print("\nYOUR PLAYLIST:")
    playlist_ids = []
    for i, track in enumerate(sample_tracks):
        print(f"{i+1}. {track['name']} by {track['artists']} - {track['album']}")
        playlist_ids.append(track['id'])
    
    # 3. Get recommendations based on the playlist
    print("\nStep 2: Getting recommendations based on your playlist...")
    recommendations = get_recommendations(playlist_ids, 20)
    if not recommendations:
        print("Failed to get recommendations")
        return
    
    # 4. Simulate user swiping --- Demo purposes only
    print("\nStep 3: Simulating swiping on recommended songs...")
    liked_songs = []
    for i, song in enumerate(recommendations):
        import random
        swipe = random.choice(["RIGHT", "LEFT"])
        
        print(f"\nSong {i+1}: {song['name']} by {song['artists']}")
        print(f"Album: {song['album']}")
        print(f"You swiped: {swipe}")
        
        if swipe == "RIGHT":
            liked_songs.append(song)
            print("✅ Added to your playlist!")
        else:
            print("❌ Skipped")
            
        if i >= 19:
            break
    
    # 5. Show final playlist with new liked songs
    print("\nYOUR UPDATED PLAYLIST:")
    for i, track in enumerate(sample_tracks + liked_songs):
        print(f"{i+1}. {track['name']} by {track['artists']} - {track['album']}")
    
    print("\n=== END OF SIMULATION ===")

if __name__ == "__main__":
    choice = input("Choose test (1=Get Recommendations, 2=Full Simulation): ")
    if choice == "1":
        tracks = get_sample_tracks(5)
        if tracks:
            track_ids = [track['id'] for track in tracks]
            get_recommendations(track_ids)
    elif choice == "2":
        simulate_tinder_for_songs()
    else:
        print("Invalid choice")