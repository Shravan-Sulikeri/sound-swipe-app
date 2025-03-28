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
from groq import Groq
from pydantic import BaseModel
from typing import List, Dict, Any
import traceback

import os 
import base64
from requests import post, get
import json
from tqdm import tqdm
from groq import Groq

class GlobalVariables:
    def __init__(self):
        self.tracks = None
        self.music = None
class SpotifyAPI:
    def __init__(self):
        from dotenv import load_dotenv
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
        from dotenv import load_dotenv
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = 'llama3-8b-8192'
        self.combinator = PlaylistManager()
        self.groq = Groq(api_key=self.api_key)
        self.ai_response = None
        self.storage = GlobalVariables()
    
    def create_recommendation_prompt(self): #! <--- Found key error the more recommended songs, the llm will spazz and not correctly output. Keep it a max of 5 songs 
        """
        Enhanced method with more robust error handling and debugging
        """
        try:
            playlists = self.combinator.combining_playlist_and_track()
            if isinstance(playlists, dict):
                print("Playlists Found:")
                for name, tracks in playlists.items():
                    print(f"- {name}: {len(tracks)} tracks")
            else:
                print("Playlist retrieval returned non-dictionary type:", type(playlists))
                return None
            prompt = (
                "I have these music playlists:\n\n"
                + "\n".join(
                    f"- {name}: {len(tracks)} tracks"
                    for name, tracks in playlists.items()
                )
                + "\n\nProvide a minimum of 5 song recommendations for each playlist.\n"
                "IMPORTANT REQUIREMENTS:\n"
                "1. Recommend songs NOT in the existing playlists\n"
                "2. Each recommendation should be unique\n"
                "3. Match the mood and genre of each playlist\n\n"
                "RESPOND EXACTLY IN THIS JSON FORMAT:\n"
                "{\n"
                "  \"Playlist Name 1\": [\n"
                "    {\"name\": \"Song1\", \"artist\": \"Artist1\"},\n"
                "    {\"name\": \"Song2\", \"artist\": \"Artist2\"}\n"
                "  ],\n"
                "  \"Playlist Name 2\": [\n"
                "    {\"name\": \"Song3\", \"artist\": \"Artist3\"}\n"
                "  ]\n"
                "}"
            )

            chat_completion = self.groq.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise music recommendation AI. ONLY return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=8000,
                response_format={"type": "json_object"},  
                stream=False,
            )
            full_response = chat_completion.choices[0].message.content
            print("\n--- RAW AI RESPONSE ---")
            print(full_response)
            print("--- END RAW RESPONSE ---\n")
            try:
                parsed_response = json.loads(full_response)
                return parsed_response
            except json.JSONDecodeError as json_err:
                print("JSON PARSING ERROR:")
                print(json_err)
                print("Problematic JSON content:", full_response)
                return None

        except Exception as e:
            print("UNEXPECTED ERROR IN RECOMMENDATION GENERATION:")
            traceback.print_exc()
            return None

    def format_recommendations(self):
        """
        Enhanced recommendation formatting with extensive error handling
        """
        try:
            if not hasattr(self, 'ai_response') or not self.ai_response:
                print("Generating recommendations...")
                self.ai_response = self.create_recommendation_prompt()
            if not self.ai_response:
                print("No recommendations could be generated.")
                return {}
            formatted_tracks = {}
            for playlist_name, tracks in self.ai_response.items():
                playlist_id = playlist_name.replace(' ', '_').lower()
                formatted_tracks[playlist_id] = [
                    {
                        "track_name": track.get('name', 'Unknown Track'),
                        "artist_name": track.get('artist', 'Unknown Artist')
                    } 
                    for track in tracks
                ]
            self.storage.tracks = formatted_tracks
            return self.storage.tracks

        except Exception as e:
            print("ERROR IN FORMATTING RECOMMENDATIONS:")
            traceback.print_exc()
            return {}
class SpotifyManagement:
    def __init__(self):
        self.recommendation_manager = RecommendationManager()
        self.spotify_api = SpotifyAPI()
        self.token = self.spotify_api.token
        self.storage_manager = GlobalVariables()
    
    def get_tracks(self):
        """
        Retrieves tracks from the Spotify API.
        Returns:
            List of dictionaries with track details.
        """
        storage = self.storage_manager.tracks
        playlists = self.recommendation_manager.format_recommendations()
        storage = playlists
        transformed_playlists = storage
        if not transformed_playlists:
            print("No recommendations available.")
            return []
        
        all_tracks = []
        for key, value in transformed_playlists.items():
            for track in value:
                track_name = track['track_name']
                artist_name = track['artist_name']
                all_tracks.append({
                    "name": track_name,
                    "artist": artist_name
                })
        
        self.storage_manager.music = all_tracks
        print("Tracks retrieved successfully.")
        return self.storage_manager.music
    
    def fetch_user_songs(self): #! <--- Working on searching for song id
        fetched_songs = []
        url = "https://api.spotify.com/v1/search"
        for song in self.storage_manager.music:
            pass
            
        # playlist = []
        # url = "https://api.spotify.com/v1/me/playlists"
        # headers = self.get_auth_header(token)
        # result = get(url, headers=headers)
        # json_result = json.loads(result.content)['items']
        # if len(json_result) == 0:
        #     return 'No playlists found'
        # else:
        #     for playlist in json_result:
        #         name = playlist['name']
        #         id = playlist['id']
        #         final = ({"name": name, "id": id})
        #         playlist.append(final)
        # return playlist
            
    
if __name__ == '__main__':
    # pm = PlaylistManager()
    # result = pm.combining_playlist_and_track()
    # print(result)
    
    # ai = RecommendationManager()
    # result = ai.format_recommendations()
    # print(result)
    
    sm = SpotifyManagement()
    result = sm.get_tracks()
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
    
    # {
#   "Xavier Playlist": [
#     {"name": "Lemonade", "artist": "Internet Money ft. Don Toliver & Gunna"},
#     {"name": "Peaches", "artist": "Justin Bieber ft. Daniel Caesar & Giveon"},
#     {"name": "WAP", "artist": "Cardi B ft. Megan Thee Stallion"},
#     {"name": "Savage", "artist": "Megan Thee Stallion ft. Beyoncé"},
#     {"name": "Body", "artist": "Tion Wayne ft. Russ Millions"},
#     {"name": "Kiss Me More", "artist": "Doja Cat ft. SZA"},
#     {"name": "Traitor", "artist": "Twenty One Pilots"},
#     {"name": "Good 4 U", "artist": "Olivia Rodrigo"},
#     {"name": "Stay", "artist": "The Kid LAROI & Justin Bieber"},
#     {"name": "MONTERO (Call Me By Your Name)", "artist": "Lil Nas X"}
#   ],
#   "Vibes Like Stuck": [
#     {"name": "Dance Monkey", "artist": "Tones and I"},
#     {"name": "Roses", "artist": "SAINt JHN"},
#     {"name": "Blinding Lights", "artist": "The Weeknd"},
#     {"name": "Before You Go", "artist": "Lauv"},
#     {"name": "Sucker", "artist": "Jonas Brothers"},
#     {"name": "Senorita", "artist": "Shawn Mendes & Camila Cabello"},
#     {"name": "Eastside", "artist": "Benny Blanco, Halsey, & Khalid"},
#     {"name": "High Hopes", "artist": "Panic! At The Disco"},
#     {"name": "Truth Hurts", "artist": "Lizzo"},
#     {"name": "Old Town Road", "artist": "Lil Nas X ft. Billy Ray Cyrus"}
#   ],

#  rgjs2003