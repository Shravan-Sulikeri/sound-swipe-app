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
from urllib.parse import quote
import re
import urllib
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pymongo import MongoClient

#**IMPORTANT** please read the all NOTES
#NOTE: Feel free to test your own Spotify playlist if you have one, within the fetch_current_user function.
#NOTE: In prod fetch_current_user function will be disabled and fetch_logged_in_user_playlist will be used but NEEDS to be connected to cookie login. 
#NOTE: The prompt engineering for llm is spotty will recommend song more than once, take with grain of salt.
#NOTE: When fetching track info errors will present, may notice 403 error simply do to not be able to get info not pertinent atm but will need to fix later.
#NOTE: Will later need to get songs back from added playlist to formulate new spotify playlist. 
#NOTE: Work on separating the classes into their own files, this is a monolithic file and needs to be broken up for better readability and maintainability.
#**
class GlobalVariables:
    def __init__(self):
        self.tracks = None
        self.music = None
        self.finalized_data = None

class MongoDB:
    def __init__(self):
        load_dotenv()
        self.mongo_auth = os.getenv("MONGO_AUTH")
    
    def get_token(self):
        cookies = {
        'connect.sid': 's%3A5Lm3YAz4_KO-GGLG0R1nTljaJYwIeYtO.gcgUhCXqH7K3rVsTGG3lknbdGkGYVtGnAAG5avJBXzw'  # replace with the actual cookie value
        }

        # Make the request to get the token, send the cookie along
        response = requests.get("http://localhost:3001/api/token", cookies=cookies)

        if response.status_code == 200:
            # If everything goes well, extract the token from the response
            print("Token:", response.json())  # Here you should get the token
        else:
            raise Exception("Failed to get token:", response.status_code, response.text)
        # try:
        #     result = requests.get(self.mongo_auth)
        #     response = result.json().get('access_token')
        #     print("Status code:", result.status_code)
        #     print("Headers:", result.headers)
        #     print("Content-Type:", result.headers.get('Content-Type'))

        #     # Check if it's JSON
        #     try:
        #         print("JSON Response:", response)
        #     except Exception as e:
        #         print("Not JSON. Raw Text Response:", result.text)

        #     # Check cookies
        #     print("Cookies:", result.cookies)
        #     return result.cookies
        # except Exception as e:
        #     print("Request error:", e)
        #     return None
        
        
class SpotifyAPI:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
        self.token = self.get_token()
        self.auth_header = self.get_auth_header(self.token)
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.client_id, client_secret=self.client_secret, redirect_uri=self.redirect_uri, scope="playlist-modify-public"))
        
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
    
    def fetch_new_releases(self):
        """
        gets new releases from the spotify api.
        """
        new_releases = []
        results = self.sp.new_releases(limit=50)
        for i, item in enumerate(results['albums']['items']):
            name = item['name']
            artist = item['artists'][0]['name']
            final = ({"name": name, "artist": artist})
            new_releases.append(final)
        return new_releases
        
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

class LastFmAPI: #! <---- This is the class that will be used to get the last.fm data, this is helping to increase the recommendations and get more data on the songs
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("LAST_FM_API_KEY")
    
    def get_similar_artist(self, artist_name): #! <---- This is the function that will be used to get the similar artist from last.fm
        """
        Fetches similar artist from Last.fm API.
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            List of similar artist or None if not found
        """
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist={quote(artist_name)}&api_key={self.api_key}&format=json"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if 'similarartists' in data and 'artist' in data['similarartists']:
                similar_artists = [x['name'] for x in data['similarartists']['artist']]
                return similar_artists
            else:
                print(f"No similar artists found for {artist_name}")
                return None
        else:
            print(f"LastFM API error {response.status_code} when finding similar artists for {artist_name}")
            return None
    
    def get_similar_tracks(self, track_name, artist_name): #! <---- This is the function that will be used to get the similar tracks from last.fm
        """
        Fetches similar tracks from Last.fm API.
        
        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            
        Returns:
            List of similar tracks or None if not found
        """
        url = f"http://ws.audioscrobbler.com/2.0/?method=track.getsimilar&track={quote(track_name)}&artist={quote(artist_name)}&api_key={self.api_key}&format=json"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if 'similartracks' in data and 'track' in data['similartracks']:
                similar_tracks = [
                    {"name": x['name'], "artist": x['artist']['name']}
                    for x in data['similartracks']['track']
                ]
                return similar_tracks
            else:
                print(f"No similar tracks found for {track_name} by {artist_name}")
                return None
        else:
            print(f"LastFM API error {response.status_code} when finding similar tracks for {track_name}")
            return None
    
    def get_track_info(self, track_name, artist_name): #! <---- This is the function that will be used to get the track info from last.fm
        """
        Fetches detailed track information from Last.fm API.
        
        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            
        Returns:
            Track info dictionary or None if not found
        """
        url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&track={quote(track_name)}&artist={quote(artist_name)}&api_key={self.api_key}&format=json"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if 'track' in data:
                return data['track']
            else:
                print(f"No track info found for {track_name} by {artist_name}")
                return None
        else:
            print(f"LastFM API error {response.status_code} when getting track info for {track_name}")
            return None
            
    def get_artist_top_tracks(self, artist_name, limit=10): #! <---- This is the function that will be used to get the top tracks from last.fm
        """
        Fetches top tracks from an artist from Last.fm API.
        
        Args:
            artist_name: Name of the artist
            limit: Maximum number of tracks to return
            
        Returns:
            List of top tracks or None if not found
        """
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getTopTracks&artist={quote(artist_name)}&api_key={self.api_key}&format=json&limit={limit}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if 'toptracks' in data and 'track' in data['toptracks']:
                top_tracks = [
                    {"name": track['name'], "artist": artist_name}
                    for track in data['toptracks']['track']
                ]
                return top_tracks
            else:
                print(f"No top tracks found for {artist_name}")
                return None
        else:
            print(f"LastFM API error {response.status_code} when getting top tracks for {artist_name}")
            return None
class RecommendationManager:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = 'llama-3.3-70b-versatile'
        self.combinator = PlaylistManager()
        self.groq = Groq(api_key=self.api_key)
        self.ai_response = None
        self.storage = GlobalVariables()
        self.similarity = LastFmAPI()
    
    def create_recommendation_prompt(self):
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
                + "\n\nProvide a minimum of 3 song recommendations for each playlist.\n"
                "IMPORTANT REQUIREMENTS:\n"
                "1. Recommend songs NOT in the existing playlists\n"
                "2. Each recommendation should be unique\n"
                "3. Prioritize the mood and styles of the song in the playlist to match\n"
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
    
    def create_artist_recommendations_prompt(self, artist_name):
        """
        Generate song recommendations for a specific artist using LLM
        """
        try:
            prompt = (
                f"Recommend 3 popular songs by {artist_name} or music that sounds very similar to {artist_name}'s style.\n\n"
                "RESPOND EXACTLY IN THIS JSON FORMAT:\n"
                "[\n"
                "  {\"name\": \"Song1\", \"artist\": \"Artist1\"},\n"
                "  {\"name\": \"Song2\", \"artist\": \"Artist2\"},\n"
                "  {\"name\": \"Song3\", \"artist\": \"Artist3\"}\n"
                "]"
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
                max_tokens=1000,
                response_format={"type": "json_object"},  
                stream=False,
            )
            full_response = chat_completion.choices[0].message.content
            try:
                parsed_response = json.loads(full_response)
                return parsed_response
            except json.JSONDecodeError as json_err:
                print(f"JSON PARSING ERROR for artist {artist_name}:")
                print(json_err)
                return []

        except Exception as e:
            print(f"ERROR GENERATING RECOMMENDATIONS FOR ARTIST {artist_name}:")
            traceback.print_exc()
            return []
    
    def optimize_recommendations(self): #! <---- This is the function that will be used to optimize the recommendations using last.fm
        """
        Optimizes recommendations by creating triplets with no duplications:
        1. Original LLM recommendation
        2. Similar track from Last.fm
        3. Top track from similar artist
        """
        recommendations = self.format_recommendations()
        optimized_recommendations = {}
        all_recommended_tracks = set()
        
        for playlist_id, tracks in recommendations.items():
            optimized_tracks = []
            
            for track in tracks:
                track_name = track["track_name"]
                artist_name = track["artist_name"]
                
                print(f"\n🎧 Processing: {track_name} by {artist_name}")
                triplet = []
                
                # 1. Add the original LLM recommendation if not already added
                track_key = f"{track_name.lower()}|{artist_name.lower()}"
                if track_key not in all_recommended_tracks:
                    print(f"✅ Original LLM recommendation: {track_name} by {artist_name}")
                    triplet.append({
                        "track_name": track_name,
                        "artist_name": artist_name,
                        "source": "llm"
                    })
                    all_recommended_tracks.add(track_key)
                else:
                    print(f"⚠️ Skipping duplicate original recommendation: {track_name} by {artist_name}")
                    continue
                
                # 2. Find similar track from Last.fm
                similar_tracks = self.similarity.get_similar_tracks(track_name, artist_name)
                if similar_tracks:
                    for similar in similar_tracks:
                        similar_key = f"{similar['name'].lower()}|{similar['artist'].lower()}"
                        if similar_key not in all_recommended_tracks:
                            print(f"✅ Last.fm similar track: {similar['name']} by {similar['artist']}")
                            triplet.append({
                                "track_name": similar["name"],
                                "artist_name": similar["artist"],
                                "source": "lastfm_similar"
                            })
                            all_recommended_tracks.add(similar_key)
                            break
                
                if len(triplet) < 2:
                    simplified_name = re.sub(r'\([^)]*\)', '', track_name).strip()
                    simplified_name = re.sub(r'\[[^\]]*\]', '', simplified_name).strip()
                    if simplified_name != track_name:
                        similar_tracks = self.similarity.get_similar_tracks(simplified_name, artist_name)
                        if similar_tracks:
                            for similar in similar_tracks:
                                similar_key = f"{similar['name'].lower()}|{similar['artist'].lower()}"
                                if similar_key not in all_recommended_tracks:
                                    print(f"✅ Last.fm similar track (simplified name): {similar['name']} by {similar['artist']}")
                                    triplet.append({
                                        "track_name": similar["name"],
                                        "artist_name": similar["artist"],
                                        "source": "lastfm_similar"
                                    })
                                    all_recommended_tracks.add(similar_key)
                                    break
                                
                if len(triplet) < 2:
                    top_tracks = self.similarity.get_artist_top_tracks(artist_name, limit=5)
                    if top_tracks:
                        for top in top_tracks:
                            top_key = f"{top['name'].lower()}|{top['artist'].lower()}"
                            if top_key not in all_recommended_tracks:
                                print(f"✅ Last.fm artist top track: {top['name']} by {top['artist']}")
                                triplet.append({
                                    "track_name": top["name"],
                                    "artist_name": top["artist"],
                                    "source": "lastfm_artist_top"
                                })
                                all_recommended_tracks.add(top_key)
                                break
                
                # 3. Add a track from similar artist
                if len(triplet) < 3:
                    similar_artists = self.similarity.get_similar_artist(artist_name)
                    if similar_artists:
                        for similar_artist in similar_artists:
                            if len(triplet) >= 3:
                                break
                                
                            artist_top_tracks = self.similarity.get_artist_top_tracks(similar_artist, limit=5)
                            if artist_top_tracks:
                                for top in artist_top_tracks:
                                    top_key = f"{top['name'].lower()}|{top['artist'].lower()}"
                                    if top_key not in all_recommended_tracks:
                                        print(f"✅ Similar artist track: {top['name']} by {top['artist']}")
                                        triplet.append({
                                            "track_name": top["name"],
                                            "artist_name": top["artist"],
                                            "source": "lastfm_similar_artist"
                                        })
                                        all_recommended_tracks.add(top_key)
                                        break
                optimized_tracks.extend(triplet)
            
            optimized_recommendations[playlist_id] = optimized_tracks
        final_recommendations = {}
        for playlist_id, tracks in optimized_recommendations.items():
            seen_in_playlist = set()
            unique_tracks = []
            
            for track in tracks:
                track_key = f"{track['track_name'].lower()}|{track['artist_name'].lower()}"
                if track_key not in seen_in_playlist:
                    unique_tracks.append(track)
                    seen_in_playlist.add(track_key)
            
            final_recommendations[playlist_id] = unique_tracks
        self.storage.tracks = final_recommendations
        return final_recommendations
    
    def get_enhanced_recommendations(self):
        """
        Main method to get enhanced recommendations with LastFM validation
        and robust fallback mechanisms
        """
        try:
            initial_recommendations = self.format_recommendations()
            
            if not initial_recommendations:
                print("Failed to generate initial recommendations.")
                return {}
            
            try:
                print("\n🔍 Optimizing recommendations using LastFM data...")
                optimized_recommendations = self.optimize_recommendations()
                if optimized_recommendations and len(optimized_recommendations) > 0:
                    return optimized_recommendations
                else:
                    print("⚠️ Optimization failed, falling back to initial recommendations.")
                    return initial_recommendations
                    
            except Exception as e:
                print("⚠️ Error during optimization, falling back to initial recommendations:")
                traceback.print_exc()
                return initial_recommendations
                
        except Exception as e:
            print("❌ Critical error in recommendation process:")
            traceback.print_exc()
            return {}
class SpotifyManagement:
    """"
        Takes AI recommended tracks, uses the optimized flow with LastFM,
        and completes info using Deezer API.
        Formats everything for frontend use, including preview_url, cover_art, etc.
    """
    def __init__(self):
        self.recommendation_manager = RecommendationManager()
        self.spotify_api = SpotifyAPI()
        self.token = self.spotify_api.token
        self.storage_manager = GlobalVariables()
        self.tracks = None
    
    def get_tracks(self):
        """
        Retrieves tracks from the optimized LLM + LastFM recommendation process.
        Returns:
            List of dictionaries with track details.
        """
        # Use the optimized recommendations instead of just format_recommendations
        optimized_playlists = self.recommendation_manager.get_enhanced_recommendations()
        self.storage_manager.tracks = optimized_playlists
        
        if not optimized_playlists:
            print("No recommendations available.")
            return []
        
        all_tracks = []
        for key, value in optimized_playlists.items():
            for track in value:
                track_name = track['track_name']
                artist_name = track['artist_name']
                all_tracks.append({
                    "name": track_name,
                    "artist": artist_name
                })
        
        self.storage_manager.music = all_tracks
        print(f"Successfully retrieved {len(all_tracks)} optimized tracks.")
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
    
    def get_deezer_track_info(self, track_name, artist_name=''):
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
    
    def fetch_user_songs(self):
        """
        Takes data from optimized get_tracks() function and uses deezer api to get rest of necessary data.
        Ensures no duplications in the final output.
        
        Returns:
            Track data as a dictionary.
        """
        self.tracks = self.get_tracks()
        print('\nFetching track data using deezer api for optimized recommendations...\n')
        
        if not self.tracks:
            return []
                
        track_data = []
        track_ids_seen = set() 
        
        for track in tqdm(self.tracks, desc="Processing tracks", unit="track"):
            try:
                track_name = track['name']
                artist = track.get('artist', '')
                primary_artist = self.extract_primary_artist(artist)
                
                print(f"\nProcessing: {track_name} by {primary_artist}")
                deezer_result = self.get_deezer_track_info(track_name, primary_artist)
                if not deezer_result:
                    print(f"  Trying broader search without artist constraint...")
                    deezer_result = self.get_deezer_track_info(track_name, "")
                    
                if not deezer_result:
                    simplified_name = self.simplify_track_name(track_name)
                    if simplified_name != track_name:
                        print(f"  Trying simplified name: '{simplified_name}'")
                        deezer_result = self.get_deezer_track_info(simplified_name, primary_artist)
                    
                if not deezer_result:
                    print(f"Could not find track: {track_name} by {artist}")
                    continue
                    
                track_id = deezer_result['id']
                if track_id in track_ids_seen:
                    print(f"Skipping duplicate track ID: {track_id} for {track_name}")
                    continue
                    
                track_ids_seen.add(track_id)
                
                track_details = self.get_deezer_track_by_id(track_id)
                
                if not track_details:
                    track_details = deezer_result
                    
                track_data.append({
                    'name': track_details['title'],
                    'id': track_details['id'],
                    'image': track_details['album']['cover_xl'],
                    'artist': track_details['artist']['name'],
                    'preview_url': track_details['preview'],
                    'deezer_url': track_details['link'],
                    'album': track_details['album']['title'],
                    'duration': track_details.get('duration', 0),
                    'lastfm_verified': True
                })
                
            except Exception as e:
                print(f"Error processing {track['name']}: {e}")
                continue
                    
        self.storage_manager.finalized_data = track_data
        print(f"\nSuccessfully processed {len(track_data)} unique tracks with Deezer data")
        return self.storage_manager.finalized_data

    def organize_by_playlist(self): #! <---- Dont know why this is added, this cn be removed it not needed or planned to be used 
        """
        Organizes the finalized track data back into playlist structure
        Returns:
            Dictionary with playlist IDs as keys and track lists as values
        """
        if not self.storage_manager.finalized_data or not self.storage_manager.tracks:
            print("No data available to organize by playlist")
            return {}
            
        organized_data = {}
        track_mapping = {}
        for track in self.storage_manager.finalized_data:
            key = f"{track['name'].lower()} - {track['artist'].lower()}"
            track_mapping[key] = track
        for playlist_id, tracks in self.storage_manager.tracks.items():
            playlist_tracks = []
            for track in tracks:
                track_name = track['track_name']
                artist_name = track['artist_name']
                key = f"{track_name.lower()} - {artist_name.lower()}"
                if key in track_mapping:
                    playlist_tracks.append(track_mapping[key])
                else:
                    for map_key, map_track in track_mapping.items():
                        if track_name.lower() in map_key:
                            playlist_tracks.append(map_track)
                            break
            
            organized_data[playlist_id] = playlist_tracks
            
        return organized_data  
if __name__ == '__main__':
    
    # pm = PlaylistManager()
    # result = pm.combining_playlist_and_track()
    # print(result)
    
    # ai = RecommendationManager()
    # result = ai.format_recommendations()
    # print(result)
    
    # sm = SpotifyManagement()
    # result = sm.fetch_user_songs()
    # print(result)
    
    md = MongoDB()
    result = md.get_token()
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