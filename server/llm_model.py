from dotenv import load_dotenv
import os 
import base64
from requests import post, get
import json
from tqdm import tqdm
from ollama import chat
from ollama import ChatResponse
import re
import json

class SpotifyAPI:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.token = self.get_token()
        self.auth_header = self.get_auth_header(self.token)
        
    def get_token(self):
        auth_str = self.client_id + ":" + self.client_secret
        auth_bytes = auth_str.encode('utf-8')
        auth_b64 = str(base64.b64encode(auth_bytes), "utf-8")
        
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_b64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        result = post(url, headers=headers, data=data)
        json_result = json.loads(result.content)
        token = json_result["access_token"]
        return token

    def get_auth_header(self, token):
        return {"Authorization": "Bearer " + token}
    
    def fetch_current_user_playlists(self, token, user_id="rgjs2003"): #! This function is ONLY for testing purposes
        playlist = []
        url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        headers = self.get_auth_header(token)
        result = get(url, headers=headers)
        json_result = json.loads(result.content)['items']
        if len(json_result) == 0:
            return None
        else:
            for x in json_result:
                name = x['name']
                id = x['id']
                final = ({"name": name, "id": id})
                playlist.append(final)
        return playlist
    
    def fetch_current_user_playlist(self, token): #! Need to get AUTH working for this function
        playlist = []
        url = "https://api.spotify.com/v1/me/playlists"
        headers = self.get_auth_header(token)
        result = get(url, headers=headers)
        json_result = json.loads(result.content)['items']
        if len(json_result) == 0:
            return 'No playlists found'
        else:
            for playlist in json_result:
                name = playlist['name']
                id = playlist['id']
                final = ({"name": name, "id": id})
                playlist.append(final)
        return playlist

    def fetch_track_from_playlist(self, auth_token, playlist_id="0jc7n2yw8xjrRJORj4uGGm"): #! This is ONLY for testing purposes
        """
        Fetches track data from a Spotify playlist.
        Input: playlist_id (string), auth_token (string)
        Output: List of track dictionaries [{'name': ..., 'artist': ..., 'album': ...}, ...]
        """
        # Authenticate with Spotify API
        # Make GET request to /playlists/{playlist_id}/tracks
        # Parse response JSON for track details (name, artist, album)
        # Return list of tracks
        tracks = []
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        headers = self.get_auth_header(auth_token)
        result = get(url, headers=headers)
        json_result = json.loads(result.content)["items"]
        if len(json_result) == 0:
            return 'No tracks found'
        else:
            for track in json_result:
                name = track['track']['name']
                artist = track['track']['artists'][0]['name']
                album = track['track']['album']['name']
                final = ({"name": name, "artist": artist, "album": album})
                tracks.append(final)
        return tracks

class PlaylistManager:
    def __init__(self):
        self.spotify_api = SpotifyAPI()
        self.token = self.spotify_api.token
    
    def combining_playlist_and_track(self):
        """
        Combines playlist and track data into a dictionary or structured format.
        Input: Spotify API token
        Output: Dictionary of playlists and tracks or structured format
        
        """
        playlist_tracks= {}
        x = input("1 -> for dictionary format or 2 -> for structured format: ")
        x = int(x)
        if (x == 2):
            print("\nRetrieving your playlist and tracks, please wait patiently...\n")
            playlist = self.spotify_api.fetch_current_user_playlists(self.token)
            for value in tqdm(playlist, desc="Fetching playlists and tracks... ", unit="playlist", bar_format="{l_bar}{bar}✅ {n_fmt}/{total_fmt} [{elapsed}]", colour="green"):
                pl_id = value['id']
                pl_name = value['name']
                combined_name = pl_name + " - " + pl_id
                track = self.spotify_api.fetch_track_from_playlist(self.token, pl_id)
                playlist_tracks[combined_name] = track
            formatted_output = ""
            for key, values in playlist_tracks.items():
                formatted_output += f"{key}:\n"
                for val in values:
                    formatted_output += f"  - {val}\n"
                formatted_output += "\n\n"
            return formatted_output
        elif (x == 1):
            playlist = self.spotify_api.fetch_current_user_playlists(self.token)
            for value in tqdm(playlist, desc="Fetching playlists and tracks... ", unit="playlist", bar_format="{l_bar}{bar}✅ {n_fmt}/{total_fmt} [{elapsed}]", colour="green"):
                pl_id = value['id']
                pl_name = value['name']
                combined_name = pl_name + " - " + pl_id
                track = self.spotify_api.fetch_track_from_playlist(self.token, pl_id)
                playlist_tracks[combined_name] = track
            return playlist_tracks
        else:
            return "Invalid input, enter 1 or 2."
        
class RecommendationManager:
    def __init__(self):
        self.model = 'deepseek-r1'
        self.combinator = PlaylistManager()
        self.ai_response = None
    
    def create_recommendation_prompt(self): #! Need to test this function not to sure if ai is working properly...
        """
        Creates a natural language prompt from playlist tracks.
        Input: List of track dictionaries
        Output: Formatted string prompt
        """
        playlists = self.combinator.combining_playlist_and_track()

        if isinstance(playlists, str):
            print("Unexpected format: Ensure the function returns a dictionary.")
            return None  
        
        summarized_playlists = []
        names = set()
        artist_name = "name"
        
        playlist_items = list(playlists.items())
        for playlist_name, tracks in playlist_items:
            for artist in tracks:
                if artist_name in artist:
                    names.add(artist[artist_name])
            track_count = len(tracks) 
            genres = "varied genres"  
            mood = "energetic, chill, or emotional mix" 

            summarized_playlists.append(
                f"**{playlist_name}**: {track_count} songs, featuring artists like {', '.join(list(names)[:5])}. "
                f"The overall vibe is {mood} with {genres}."
            )

        playlist_summary = "\n".join(summarized_playlists)
        
        print("\nCreating recommendation prompt, this will take time please wait patiently...")
        
        response: ChatResponse = chat(model=self.model, messages=[
            {
                "role": "user",
                "content": (
                    "Here is a summary of all user playlists, including key artists and overall mood:\n\n"
                    f"{playlist_summary}\n\n"
                    "Based on these playlists, recommend **10 new songs per playlist** that align with the overall vibe. "
                    "Ensure that none of the recommended songs are already in the playlists. "
                    "Ensure that recommended songs are from the same genre or similar genres, and are not already in another recommended playlist. "
                    "Include a mix of popular and lesser-known artists. The most important feature is to ensure that recommended songs do NOT show up more than once in the recommendations overall. "
                    "Return results in a structured format, like the following; recommendations: [{\"name\": \"Song X\", \"artist\": \"Artist X\"}, ...]."
                )
            }
        ])
        
        self.ai_response = response.message.content
        return self.ai_response
    
    def formating_of_recommendations(self):
        """
        Formats recommendations into JSON structure for the frontend.
        Input: List of recommended songs
        Output: JSON response structure
        """
        track_list = {}
        
        self.ai_response = self.create_recommendation_prompt()
        
        print("\nFormatting recommendations, please wait patiently...")

        # Extract playlist sections using regex
        playlists = re.findall(r"### Playlist: (.*?)\n\*\*Recommendations:\*\*\s*\n(\[.*?\])", self.ai_response, re.DOTALL)
        
        print(playlists)

        for playlist_name, songs_json in playlists:
            try:
                # Convert the song list from string to dictionary
                track_list[playlist_name] = json.loads(songs_json)
            except json.JSONDecodeError:
                print(f"Error parsing JSON for playlist: {playlist_name}")

        return {"recommendations": track_list}
    

if __name__ == '__main__':
    # pm = PlaylistManager()
    # result = pm.combining_playlist_and_track()
    # print(result)
    
    ai = RecommendationManager()
    result = ai.create_recommendation_prompt()
    print(result)
    
    # 1. "The Definition" (various album versions)
    # 2. "War of Hearts"
    # 3. "Ooh"
    # 4. "Woke The F*ck Up"
    # 5. "All Time Low"
    # 6. "Simple & Sweet"
    # 7. "Munny Right"
    # 8. "Human"
    # 9. "Carry Your Throne"