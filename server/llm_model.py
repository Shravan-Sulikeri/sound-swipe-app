from dotenv import load_dotenv
import os 
import base64
from requests import post, get
import json
import requests
from tqdm import tqdm
import json
from groq import Groq
import traceback
import os 
import base64
from requests import post, get
import json
from tqdm import tqdm
from groq import Groq
from urllib.parse import quote
import re
import urllib

#**IMPORTANT** please read the all NOTES
#NOTE: Feel free to test your own Spotify playlist if you have one, within the fetch_current_user function.
#NOTE: In prod fetch_current_user function will be disabled and fetch_logged_in_user_playlist will be used but NEEDS to be connected to cookie login. 
#NOTE: The prompt engineering for llm is spotty will recommend song more than once, take with grain of salt.
#NOTE: When fetching track info errors will present, may notice 403 error simply do to not be able to get info not pertinent atm but will need to fix later.
#NOTE: Will later need to get songs back from added playlist to formulate new spotify playlist. 
#**
class GlobalVariables:
    def __init__(self):
        self.tracks = None
        self.music = None
        self.finalized_data = None
        
class SpotifyAPI:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.token = self.get_token()
        self.auth_header = self.get_auth_header(self.token)
        
    def get_token(self):
        """
        gets api key and returns a token for the user to use for authentication.
        client secret id : api key
        puts in byte format
        """
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
    
    def fetch_current_user_playlists(self, token, user_id="w5e01d35jtoh0qo6j060vr7jv"): #! This function is ONLY for testing purposes
        """
        what we're currently using. 
        Fetches all the current user after putting in account name.
        """

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
    
    def fetch_logged_in_user_playlist(self, token): #! Need to get AUTH working for this function
        """
        will eventually fetch playlists of whoever's logged in. 
        """
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

    def fetch_track_from_playlist(self, auth_token, playlist_id="3FCcErUVRSiCJl2J9stvhI"): #! This is ONLY for testing purposes
        """
        if not logged in: public playlists can be accessed with just the playlist id.
        gets songs from a designated playlist id. get id from link, thing before "?"
        
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
    """
        creates a dictionary of all the playlists and their respective tracks.
        
    """
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
        # x = input("1 -> for dictionary format or 2 -> for structured format: ") #! Right now input is required lets change so input 1 will always be used in prod.
        x = 1
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
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = 'llama-3.3-70b-versatile'
        self.combinator = PlaylistManager()
        self.groq = Groq(api_key=self.api_key)
        self.ai_response = None
        self.storage = GlobalVariables()
    
    def create_recommendation_prompt(self): #! <--- Found key error the more recommended songs, the llm will spazz and not correctly output. Keep it a max of 5 songs, may need to add dynamic altering for larger playlist 
        """
        Enhanced method with more robust error handling and debugging
        """
        try:
            playlists = self.combinator.combining_playlist_and_track()
            if isinstance(playlists, dict):
                print("Playlists Found:")
                for name, tracks in playlists.items():
                    print(f" 💽 {name}: {len(tracks)} tracks")
            else:
                print("Playlist retrieval returned non-dictionary type:", type(playlists))
                return None
            
            prompt = (
                "I have these music playlists:\n\n"
                + "\n".join(
                    f"- {name}: {len(tracks)} tracks"
                    for name, tracks in playlists.items()
                )
                + "\n\nProvide a minimum of 3 song recommendations for each playlist.\n" #! CRITICAL <---- prompt engineering is not sound recommendations are on avg %50-60% correct lets work on getting closer to %80 approval
                "IMPORTANT REQUIREMENTS:\n"
                "1. Recommend songs NOT in the existing playlists\n"
                "2. Each recommendation should be unique\n"
                "3. Prioritize the mood and styles of the song in the playlist to match\n\n"
                "4. Once a song has been recommended it should NOT be recommended again\n"
                "5. Songs should be a combination of new and old, popular and not as well\n"
                "6. Prioritize fitting the playlist's central theme, decide whether it is stylic, cultural, occasional, or pertains to a certain artist\n"
                "7. If a playlist consist of songs mostly by a particular artist, prioritize recommending songs by that artist\n\n"
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
            print("\n------------ RAW AI RESPONSE ------------")
            print(full_response)
            print("------------ END RAW RESPONSE -----------\n")
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
    """"
        takes ai recommedned tracks, goes to deezer, and completes info
        formats for frontend to use, including preview_url, cover_art, etc.
        This class is responsible for managing the entire process of
        fetching user playlists, generating song recommendations, and
        retrieving detailed track information using the Deezer API.
    """
    def __init__(self):
        self.recommendation_manager = RecommendationManager()
        self.spotify_api = SpotifyAPI()
        self.token = self.spotify_api.token
        self.storage_manager = GlobalVariables()
        self.tracks = None
    
    def get_tracks(self):
        """
        Retrieves tracks from the llm prompting.
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
    
    def simplify_track_name(self, track_name):
        simplified = re.sub(r'\([^)]*\)', '', track_name)
        simplified = re.sub(r'\[[^\]]*\]', '', simplified)
        simplified = re.sub(r'[^\w\s]', '', simplified)
        simplified = re.sub(r'\s+', ' ', simplified).strip()
        return simplified
    
    def extract_primary_artist(self, artist_string):
        feature_indicators = [
            " feat. ", " ft. ", " featuring ", " with ", " & ",
            " FEAT. ", " FT. ", " Feat. ", " Ft. ",
            " (feat. ", " (ft. ", " (Feat. ", " (Ft. ",
            " [feat. ", " [ft. ", " [Feat. ", " [Ft. "
        ]
        
        for indicator in feature_indicators:
            if indicator in artist_string:
                return artist_string.split(indicator)[0].strip()
        
        return artist_string.strip()
    
    def get_deezer_track_info(self, track_name, artist_name=''): #! This is the new method for getting data as alt to spotify safer and more accessible
        """
        Takes track info and uses deezer api to get necessary info that will be used when sending to frontend. 
        Returns:
            Track data details as a list.
        """
        try:
            query = track_name
            if artist_name:
                query = f"{track_name} artist:\"{artist_name}\""
            
            url = f"https://api.deezer.com/search?q={urllib.parse.quote(query)}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    return data['data'][0]
                else:
                    if artist_name:
                        query = f"{track_name} {artist_name}"
                        url = f"https://api.deezer.com/search?q={urllib.parse.quote(query)}"
                        response = requests.get(url)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('data') and len(data['data']) > 0:
                                return data['data'][0]
                    return None
            else:
                print(f"Failed to search: Status code {response.status_code}")
                return None
        except Exception as e:
            print(f"Error searching for track: {e}")
            return None
        
    def get_deezer_track_by_id(self, track_id):
        """
        Retrieves detailed track information directly by Deezer track ID.
        
        Args:
            track_id: The Deezer track ID
            
        Returns:
            Track information dictionary or None if not found
        """
        try:
            url = f"https://api.deezer.com/track/{track_id}"
            response = requests.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch track by ID {track_id}: Status code {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching track by ID {track_id}: {e}")
            return None
    
    def fetch_user_songs(self): #! This new fetching_users implementation uses deezer api, this will still work when sinking back to front end no worries
        """
        Takes data from get_tracks() function and uses deezer api to get rest of necessary data, ie. preview_url, cover_art, etc
        will later be stored and sent to frontend
    
        Returns:
            Track data as a dictionary.
        """
        self.tracks = self.get_tracks()
        print('\nFetching track data using deezer api instead of spotify, will take time so please be patient...\n')
        
        if not self.tracks:
            return []
            
        track_data = []
        for track in self.tracks:
            try:
                track_name = track['name']
                artist = track.get('artist', '')
                primary_artist = self.extract_primary_artist(artist)
                deezer_result = self.get_deezer_track_info(track_name, primary_artist)
                if not deezer_result:
                    deezer_result = self.get_deezer_track_info(track_name, "")
                    
                if not deezer_result:
                    simplified_name = self.simplify_track_name(track_name)
                    if simplified_name != track_name:
                        deezer_result = self.get_deezer_track_info(simplified_name, primary_artist)
                    
                if not deezer_result:
                    print(f"Could not find track: {track_name} by {artist}")
                    continue
                    
                track_id = deezer_result['id']
                track_details = self.get_deezer_track_by_id(track_id)
                
                if not track_details:
                    track_details = deezer_result
                    
                track_data.append({
                    'name': track_details['title'],
                    'id': track_details['id'],
                    'image': track_details['album']['cover_xl'],
                    'artist': track_details['artist']['name'],
                    'preview_url': track_details['preview'],
                    'deezer_url': track_details['link']
                })
                
            except Exception as e:
                print(f"Error processing {track['name']}: {e}")
                continue
                
        self.storage_manager.finalized_data = track_data
        return self.storage_manager.finalized_data
    
if __name__ == '__main__':
    
    # pm = PlaylistManager()
    # result = pm.combining_playlist_and_track()
    # print(result)
    
    # ai = RecommendationManager()
    # result = ai.format_recommendations()
    # print(result)
    
    sm = SpotifyManagement()
    result = sm.fetch_user_songs()
    print(result)
    
    # {
#   Example_Format ---> {"Xavier Playlist": [
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
#   ],}

#  Test_User_Name: {rgjs2003}