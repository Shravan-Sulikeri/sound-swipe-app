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
import gc
import time
import logging
from functools import lru_cache
from spotipy.oauth2 import SpotifyOAuth
from concurrent.futures import ThreadPoolExecutor

# **IMPORTANT** please read the all NOTES
# NOTE: Feel free to test your own Spotify playlist if you have one, within the fetch_current_user function.
# NOTE: In prod fetch_current_user function will be disabled and fetch_logged_in_user_playlist will be used but NEEDS to be connected to cookie login.
# NOTE: The prompt engineering for llm is spotty will recommend song more than once, take with grain of salt.
# NOTE: When fetching track info errors will present, may notice 403 error simply do to not be able to get info not pertinent atm but will need to fix later.
# NOTE: Will later need to get songs back from added playlist to formulate new spotify playlist.
# NOTE: Work on separating the classes into their own files, this is a monolithic file and needs to be broken up for better readability and maintainability.
# **


class GlobalVariables:
    def __init__(self):
        self.tracks = None
        self.music = None
        self.finalized_data = None


class SpotifyAPI:
    def __init__(self, external_token=None):
        load_dotenv()
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = f'{os.getenv("REACT_APP")}/callback'
        self.token = external_token if external_token else self.get_token()
        self.auth_header = self.get_auth_header(self.token)
        if not external_token:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope="user-read-private user-read-email playlist-modify-public playlist-modify-private playlist-read-private"))
        else:
            self.sp = spotipy.Spotify(auth=external_token)

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

    def fetch_current_user_playlists(self, token, user_id="w5e01d35jtoh0qo6j060vr7jv"):
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

    def fetch_logged_in_user_playlist(self, token):
        playlist = []
        url = "https://api.spotify.com/v1/me/playlists"
        headers = self.get_auth_header(token)
        result = get(url, headers=headers)
        json_result = json.loads(result.content)['items']
        if len(json_result) == 0:
            return 'No playlists found'
        else:
            for x in json_result:
                name = x['name']
                id = x['id']
                final = ({"name": name, "id": id})
                playlist.append(final)
        return playlist

    def fetch_track_from_playlist(self, auth_token, playlist_id="3FCcErUVRSiCJl2J9stvhI"):
        tracks = []
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        headers = self.get_auth_header(auth_token)
        result = get(url, headers=headers)
        json_result = json.loads(result.content)["items"]
        if len(json_result) == 0:
            return 'No tracks found'
        else:
            for track in json_result:
                if track['track']:
                    name = track['track']['name']
                    artist = track['track']['artists'][0]['name']
                    album = track['track']['album']['name']
                    final = ({"name": name, "artist": artist, "album": album})
                    tracks.append(final)
        return tracks

    def fetch_new_releases(self):
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

    def __init__(self, user_token=None):
        self.spotify_api = SpotifyAPI(external_token=user_token)
        self.token = self.spotify_api.token
        self.user_token = user_token

    def combining_playlist_and_track(self):
        """
        Combines playlist and track data into a dictionary or structured format.
        Input: Spotify API token
        Output: Dictionary of playlists and tracks or structured format
        """
        playlist_tracks = {}
        # x = input("1 -> for dictionary format or 2 -> for structured format: ") #! Right now input is required lets change so input 1 will always be used in prod.
        x = 1
        if (x == 2):
            print("\nRetrieving your playlist and tracks, please wait patiently...\n")
            playlist = self.spotify_api.fetch_logged_in_user_playlist(
                self.token)
            for value in tqdm(playlist, desc="Fetching playlists and tracks... ", unit="playlist", bar_format="{l_bar}{bar}✅ {n_fmt}/{total_fmt} [{elapsed}]", colour="green"):
                pl_id = value['id']
                pl_name = value['name']
                combined_name = pl_name + " - " + pl_id
                track = self.spotify_api.fetch_track_from_playlist(
                    self.token, pl_id)
                playlist_tracks[combined_name] = track
            formatted_output = ""
            for key, values in playlist_tracks.items():
                formatted_output += f"{key}:\n"
                for val in values:
                    formatted_output += f"  - {val}\n"
                formatted_output += "\n\n"
            return formatted_output
        elif (x == 1):
            if self.user_token:
                playlist = self.spotify_api.fetch_logged_in_user_playlist(token=self.user_token)
            else:
                playlist = self.spotify_api.fetch_current_user_playlists(
                    self.token)
            for value in tqdm(playlist, desc="Fetching playlists and tracks... ", unit="playlist", bar_format="{l_bar}{bar}✅ {n_fmt}/{total_fmt} [{elapsed}]", colour="green"):
                pl_id = value['id']
                pl_name = value['name']
                combined_name = pl_name + " - " + pl_id
                track = self.spotify_api.fetch_track_from_playlist(
                    self.token, pl_id)
                playlist_tracks[combined_name] = track
            return playlist_tracks
        else:
            return "Invalid input, enter 1 or 2."


"""
Enhanced LastFmAPI class with improved error handling and retry logic
"""

class LastFmAPI:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("LAST_FM_API_KEY")
        self.session = requests.Session()  # Use a session for connection pooling
        self.cache = {}  # Simple in-memory cache

    def _make_request(self, url, cache_key=None, max_retries=3, timeout=5):
        """
        Helper method to make API requests with retry logic and caching
        
        Args:
            url: URL to request
            cache_key: Optional key for caching (if None, no caching)
            max_retries: Number of retry attempts
            timeout: Request timeout in seconds
            
        Returns:
            JSON response data or None on failure
        """
        # Check cache first
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
            
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    # Cache successful responses
                    if cache_key:
                        self.cache[cache_key] = data
                    return data
                elif response.status_code == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', 1))
                    print(f"Rate limited by Last.fm API. Waiting {retry_after}s before retry")
                    time.sleep(retry_after)
                else:
                    print(f"LastFM API error {response.status_code} (attempt {attempt+1}/{max_retries})")
            except requests.exceptions.Timeout:
                print(f"Last.fm API timeout (attempt {attempt+1}/{max_retries})")
            except requests.exceptions.RequestException as e:
                print(f"Last.fm API request error: {str(e)} (attempt {attempt+1}/{max_retries})")
            except json.JSONDecodeError:
                print(f"Invalid JSON received from Last.fm API (attempt {attempt+1}/{max_retries})")
            
            # Wait before retrying, with exponential backoff
            if attempt < max_retries - 1:
                time.sleep(1 * (2 ** attempt))  # 1s, 2s, 4s, etc.
                
        return None

    def get_similar_artist(self, artist_name):
        """
        Fetches similar artist from Last.fm API with improved error handling.
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            List of similar artist or empty list if not found
        """
        if not artist_name:
            return []
            
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist={quote(artist_name)}&api_key={self.api_key}&format=json"
        cache_key = f"similar_artist_{artist_name}"
        
        data = self._make_request(url, cache_key)
        
        if data and 'similarartists' in data and 'artist' in data['similarartists']:
            similar_artists = [x['name'] for x in data['similarartists']['artist']]
            return similar_artists
        
        print(f"No similar artists found for {artist_name}")
        return []

    def get_similar_tracks(self, track_name, artist_name):
        """
        Fetches similar tracks from Last.fm API with improved error handling.
        
        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            
        Returns:
            List of similar tracks or empty list if not found
        """
        if not track_name or not artist_name:
            return []
            
        url = f"http://ws.audioscrobbler.com/2.0/?method=track.getsimilar&track={quote(track_name)}&artist={quote(artist_name)}&api_key={self.api_key}&format=json"
        cache_key = f"similar_tracks_{track_name}_{artist_name}"
        
        data = self._make_request(url, cache_key)
        
        if data and 'similartracks' in data and 'track' in data['similartracks']:
            similar_tracks = [
                {"name": x['name'], "artist": x['artist']['name']}
                for x in data['similartracks']['track']
            ]
            return similar_tracks
        
        print(f"No similar tracks found for {track_name} by {artist_name}")
        return []

    def get_track_info(self, track_name, artist_name):
        """
        Fetches detailed track information from Last.fm API with improved error handling.
        
        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            
        Returns:
            Track info dictionary or None if not found
        """
        if not track_name or not artist_name:
            return None
            
        url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&track={quote(track_name)}&artist={quote(artist_name)}&api_key={self.api_key}&format=json"
        cache_key = f"track_info_{track_name}_{artist_name}"
        
        data = self._make_request(url, cache_key)
        
        if data and 'track' in data:
            return data['track']
        
        print(f"No track info found for {track_name} by {artist_name}")
        return None

    def get_artist_top_tracks(self, artist_name, limit=10):
        """
        Fetches top tracks from an artist from Last.fm API with improved error handling.
        
        Args:
            artist_name: Name of the artist
            limit: Maximum number of tracks to return
            
        Returns:
            List of top tracks or empty list if not found
        """
        if not artist_name:
            return []
            
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getTopTracks&artist={quote(artist_name)}&api_key={self.api_key}&format=json&limit={limit}"
        cache_key = f"artist_top_tracks_{artist_name}_{limit}"
        
        data = self._make_request(url, cache_key)
        
        if data and 'toptracks' in data and 'track' in data['toptracks']:
            top_tracks = [
                {"name": track['name'], "artist": artist_name}
                for track in data['toptracks']['track']
            ]
            return top_tracks[:limit]  # Enforce limit here as well
        
        print(f"No top tracks found for {artist_name}")
        return []
class RecommendationManager:
    def __init__(self, user_token=None):
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = 'llama-3.3-70b-versatile'
        self.combinator = PlaylistManager(user_token=user_token)
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
                print("Playlist retrieval returned non-dictionary type:",
                      type(playlists))
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
            print(
                f"ERROR GENERATING RECOMMENDATIONS FOR ARTIST {artist_name}:")
            traceback.print_exc()
            return []

    def incorporate_new_releases(self):
        """
        Fetches new releases from Spotify and incorporates them into the recommendation process
        """
        try:
            print("Fetching new music releases from Spotify...")
            new_releases = self.combinator.spotify_api.fetch_new_releases()

            if not new_releases or len(new_releases) == 0:
                print("No new releases found or error fetching them.")
                return None

            print(f"Found {len(new_releases)} new releases")
            import random
            if len(new_releases) > 15:
                sampled_releases = random.sample(new_releases, 15)
            else:
                sampled_releases = new_releases

            if not hasattr(self, 'new_releases_pool') or not self.new_releases_pool:
                self.new_releases_pool = sampled_releases

            return self.new_releases_pool
        except Exception as e:
            print("ERROR FETCHING NEW RELEASES:")
            traceback.print_exc()
            return None

    # ! <---- This is the function that will be used to optimize the recommendations using last.fm
    def optimize_recommendations(self):
        """
        Optimizes recommendations using LLM seeds and LastFM data with improved
        error handling and memory management.
        
        1. Use original LLM recommendation as seed only (not included in final output)
        2. Get 3 tracks from similar artists (primary source)
        3. Get 1 similar track from Last.fm (secondary source)
        4. Get 1 top track from original artist (tertiary source)
        """
        try:
            recommendations = self.format_recommendations()
            optimized_recommendations = {}
            all_recommended_tracks = set()
            
            # Process one playlist at a time to reduce memory pressure
            for playlist_id, tracks in recommendations.items():
                print(f"\n📋 Processing playlist: {playlist_id} with {len(tracks)} seed tracks")
                optimized_tracks = []
                
                for track in tracks:
                    track_name = track.get("track_name", "Unknown Track")
                    artist_name = track.get("artist_name", "Unknown Artist")
                    
                    try:
                        print(f"\n🎧 Processing seed: {track_name} by {artist_name}")
                        lastfm_recommendations = []
                        
                        # Track the seed to avoid recommending it
                        seed_track_key = f"{track_name.lower()}|{artist_name.lower()}"
                        all_recommended_tracks.add(seed_track_key)  # Add to seen but don't include in output
                        
                        # 1. First priority: Get tracks from similar artists (3 tracks)
                        similar_artists_count = 0
                        try:
                            similar_artists = self.similarity.get_similar_artist(artist_name)
                            
                            if similar_artists:
                                for similar_artist in similar_artists[:8]:  # Try up to 8 similar artists to find 3 good tracks
                                    if similar_artists_count >= 3:
                                        break
                                        
                                    try:
                                        artist_top_tracks = self.similarity.get_artist_top_tracks(similar_artist, limit=3)
                                        
                                        if artist_top_tracks:
                                            for top in artist_top_tracks:
                                                top_key = f"{top['name'].lower()}|{top['artist'].lower()}"
                                                if top_key not in all_recommended_tracks:
                                                    print(f"✅ Similar artist track: {top['name']} by {top['artist']}")
                                                    lastfm_recommendations.append({
                                                        "track_name": top["name"],
                                                        "artist_name": top["artist"],
                                                        "source": "lastfm_similar_artist"
                                                    })
                                                    all_recommended_tracks.add(top_key)
                                                    similar_artists_count += 1
                                                    
                                                if similar_artists_count >= 3:  # Get exactly 3 tracks from similar artists
                                                    break
                                    except Exception as artist_error:
                                        print(f"⚠️ Error processing similar artist {similar_artist}: {str(artist_error)}")
                                        continue  # Try next artist
                        except Exception as similar_error:
                            print(f"⚠️ Error getting similar artists for {artist_name}: {str(similar_error)}")
                            
                        # Proceed even if similar artists failed
                        
                        # 2. Second priority: Get 1 similar track from Last.fm
                        similar_track_found = False
                        try:
                            similar_tracks = self.similarity.get_similar_tracks(track_name, artist_name)
                            
                            if similar_tracks:
                                for similar in similar_tracks:
                                    similar_key = f"{similar['name'].lower()}|{similar['artist'].lower()}"
                                    if similar_key not in all_recommended_tracks:
                                        print(f"✅ Last.fm similar track: {similar['name']} by {similar['artist']}")
                                        lastfm_recommendations.append({
                                            "track_name": similar["name"],
                                            "artist_name": similar["artist"],
                                            "source": "lastfm_similar"
                                        })
                                        all_recommended_tracks.add(similar_key)
                                        similar_track_found = True
                                        break
                                
                            # If no similar track found with full name, try simplified name
                            if not similar_track_found:
                                simplified_name = re.sub(r'\([^)]*\)', '', track_name).strip()
                                simplified_name = re.sub(r'\[[^\]]*\]', '', simplified_name).strip()
                                
                                if simplified_name != track_name:
                                    similar_tracks = self.similarity.get_similar_tracks(simplified_name, artist_name)
                                    
                                    if similar_tracks:
                                        for similar in similar_tracks:
                                            similar_key = f"{similar['name'].lower()}|{similar['artist'].lower()}"
                                            if similar_key not in all_recommended_tracks:
                                                print(f"✅ Last.fm similar track (simplified name): {similar['name']} by {similar['artist']}")
                                                lastfm_recommendations.append({
                                                    "track_name": similar["name"],
                                                    "artist_name": similar["artist"],
                                                    "source": "lastfm_similar"
                                                })
                                                all_recommended_tracks.add(similar_key)
                                                similar_track_found = True
                                                break
                        except Exception as similar_error:
                            print(f"⚠️ Error getting similar tracks for {track_name}: {str(similar_error)}")
                        
                        # 3. Third priority: Get 1 top track from the original artist
                        top_track_found = False
                        try:
                            top_tracks = self.similarity.get_artist_top_tracks(artist_name, limit=8)
                            
                            if top_tracks:
                                for top in top_tracks:
                                    top_key = f"{top['name'].lower()}|{top['artist'].lower()}"
                                    if top_key not in all_recommended_tracks:
                                        print(f"✅ Last.fm artist top track: {top['name']} by {top['artist']}")
                                        lastfm_recommendations.append({
                                            "track_name": top["name"],
                                            "artist_name": top["artist"],
                                            "source": "lastfm_artist_top"
                                        })
                                        all_recommended_tracks.add(top_key)
                                        top_track_found = True
                                        break
                        except Exception as top_error:
                            print(f"⚠️ Error getting top tracks for {artist_name}: {str(top_error)}")
                        
                        # If we didn't get any recommendations from LastFM for this seed, log it
                        if not lastfm_recommendations:
                            print(f"⚠️ No LastFM recommendations found for {track_name} by {artist_name}")
                        
                        optimized_tracks.extend(lastfm_recommendations)
                        
                        # Force garbage collection after processing each track
                        gc.collect()
                        
                    except Exception as track_error:
                        print(f"⚠️ Error processing track {track_name} by {artist_name}: {str(track_error)}")
                        continue  # Skip to next track
                        
                # Store the optimized tracks for this playlist
                optimized_recommendations[playlist_id] = optimized_tracks
                
            # Add new releases with error handling
            try:
                new_releases = self.incorporate_new_releases()
                
                if new_releases:
                    for playlist_id, tracks in optimized_recommendations.items():
                        if len(tracks) < 12:
                            added_count = 0
                            for release in new_releases:
                                if added_count >= 3:  # Add up to 3 new releases
                                    break
                                    
                                try:
                                    release_key = f"{release['name'].lower()}|{release['artist'].lower()}"
                                    
                                    if release_key not in all_recommended_tracks:
                                        print(f"✅ Adding new release: {release['name']} by {release['artist']} to playlist {playlist_id}")
                                        tracks.append({
                                            "track_name": release["name"],
                                            "artist_name": release["artist"],
                                            "source": "new_release"
                                        })
                                        all_recommended_tracks.add(release_key)
                                        added_count += 1
                                except Exception as release_error:
                                    print(f"⚠️ Error adding new release: {str(release_error)}")
                                    continue
            except Exception as new_release_error:
                print(f"⚠️ Error incorporating new releases: {str(new_release_error)}")
                # Continue without new releases
                
            # Remove any duplicates that might have slipped through
            final_recommendations = {}
            
            for playlist_id, tracks in optimized_recommendations.items():
                seen_in_playlist = set()
                unique_tracks = []
                
                for track in tracks:
                    try:
                        track_key = f"{track['track_name'].lower()}|{track['artist_name'].lower()}"
                        
                        if track_key not in seen_in_playlist:
                            unique_tracks.append(track)
                            seen_in_playlist.add(track_key)
                    except Exception:
                        # Skip malformed tracks
                        continue
                        
                final_recommendations[playlist_id] = unique_tracks
                
            self.storage.tracks = final_recommendations
            return final_recommendations
            
        except Exception as e:
            print(f"❌ Critical error in optimization process: {str(e)}")
            traceback.print_exc()
            # Return empty dict as fallback
            return {}
        
    def get_enhanced_recommendations(self):
        """
        Main method to get enhanced recommendations with LastFM validation
        and robust fallback mechanisms, now including new releases
        """
        try:
            initial_recommendations = self.format_recommendations()

            if not initial_recommendations:
                print("Failed to generate initial recommendations.")
                return {}

            self.incorporate_new_releases()

            try:
                print(
                    "\n🔍 Optimizing recommendations using LastFM data and new releases...")
                optimized_recommendations = self.optimize_recommendations()
                if optimized_recommendations and len(optimized_recommendations) > 0:
                    return optimized_recommendations
                else:
                    print(
                        "⚠️ Optimization failed, falling back to initial recommendations.")
                    return initial_recommendations

            except Exception as e:
                print(
                    "⚠️ Error during optimization, falling back to initial recommendations:")
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

    def __init__(self, user_token=None):
        self.recommendation_manager = RecommendationManager(
            user_token=user_token)
        self.spotify_api = SpotifyAPI(external_token=user_token)
        self.token = self.spotify_api.token
        self.storage_manager = GlobalVariables()
        self.tracks = None
        self.user_token = user_token

    def get_tracks(self):
        """
        Generator that yields track dictionaries one at a time for streaming.
        """
        optimized_playlists = self.recommendation_manager.get_enhanced_recommendations()
        self.storage_manager.tracks = optimized_playlists

        if not optimized_playlists:
            print("No recommendations available.")
            return

        count = 0
        for key, value in optimized_playlists.items():
            for track in value:
                track_name = track['track_name']
                artist_name = track['artist_name']
                count += 1
                yield {
                    "name": track_name,
                    "artist": artist_name
                }

        print(f"Successfully yielded {count} optimized tracks.")

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

    @lru_cache(maxsize=100)
    def get_deezer_track_info(self, track_name, artist_name=''):
        """
        Takes track info and uses deezer api to get necessary info.
        Now with caching, better error handling and retries.
        
        Args:
            track_name: Name of the track
            artist_name: Optional artist name
            
        Returns:
            Track data or None if not found
        """
        if not track_name:
            return None
            
        try:
            query = track_name
            if artist_name:
                query = f"{track_name} artist:\"{artist_name}\""
                
            url = f"https://api.deezer.com/search?q={urllib.parse.quote(query)}"
            
            # Implement retry logic
            max_retries = 2
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=5)  # Increased timeout from 3 to 5 seconds
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('data') and len(data['data']) > 0:
                            return data['data'][0]
                        break  # No results, no need to retry
                    elif response.status_code == 429:  # Rate limit
                        retry_after = int(response.headers.get('Retry-After', 1))
                        time.sleep(retry_after)
                    else:
                        logging.warning(f"Deezer API error {response.status_code} (attempt {attempt+1})")
                        
                except requests.exceptions.Timeout:
                    logging.warning(f"Deezer API timeout (attempt {attempt+1})")
                except requests.exceptions.RequestException as e:
                    logging.warning(f"Deezer API request error: {str(e)} (attempt {attempt+1})")
                except json.JSONDecodeError:
                    logging.warning(f"Invalid JSON from Deezer API (attempt {attempt+1})")
                    
                # Only sleep if we're going to retry
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
            # If exact artist search failed, try a more general search
            if artist_name:
                query = f"{track_name} {artist_name}"
                url = f"https://api.deezer.com/search?q={urllib.parse.quote(query)}"
                
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('data') and len(data['data']) > 0:
                            return data['data'][0]
                except Exception as e:
                    logging.warning(f"Error in fallback search: {str(e)}")
                    
            return None
            
        except Exception as e:
            logging.error(f"Error searching for track: {str(e)}")
            return None

    @lru_cache(maxsize=50)
    def get_deezer_track_by_id(self, track_id):
        """
        Retrieves detailed track information by Deezer track ID with caching.
        
        Args:
            track_id: The Deezer track ID
            
        Returns:
            Track information dictionary or None if not found
        """
        if not track_id:
            return None
            
        try:
            url = f"https://api.deezer.com/track/{track_id}"
            
            max_retries = 2
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=5)  # Increased timeout
                    
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 429:  # Rate limit
                        retry_after = int(response.headers.get('Retry-After', 1))
                        time.sleep(retry_after)
                    else:
                        logging.warning(f"Failed to fetch track by ID {track_id}: Status code {response.status_code} (attempt {attempt+1})")
                        
                except requests.exceptions.Timeout:
                    logging.warning(f"Timeout fetching track by ID {track_id} (attempt {attempt+1})")
                except requests.exceptions.RequestException as e:
                    logging.warning(f"Request error fetching track by ID {track_id}: {str(e)} (attempt {attempt+1})")
                except json.JSONDecodeError:
                    logging.warning(f"Invalid JSON for track ID {track_id} (attempt {attempt+1})")
                    
                # Only sleep if we're going to retry
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
            return None
            
        except Exception as e:
            logging.error(f"Error fetching track by ID {track_id}: {str(e)}")
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
            response = requests.get(url, timeout=3)

            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f"Failed to fetch track by ID {track_id}: Status code {response.status_code}")
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
                deezer_result = self.get_deezer_track_info(
                    track_name, primary_artist)
                if not deezer_result:
                    print(f"  Trying broader search without artist constraint...")
                    deezer_result = self.get_deezer_track_info(track_name, "")

                if not deezer_result:
                    simplified_name = self.simplify_track_name(track_name)
                    if simplified_name != track_name:
                        print(f"  Trying simplified name: '{simplified_name}'")
                        deezer_result = self.get_deezer_track_info(
                            simplified_name, primary_artist)

                if not deezer_result:
                    print(f"Could not find track: {track_name} by {artist}")
                    continue

                track_id = deezer_result['id']
                if track_id in track_ids_seen:
                    print(
                        f"Skipping duplicate track ID: {track_id} for {track_name}")
                    continue

                track_ids_seen.add(track_id)

                track_details = self.get_deezer_track_by_id(track_id)

                if not track_details:
                    track_details = deezer_result

                is_new_release = track.get('source') == 'new_release'

                track_data.append({
                    'name': track_details['title'],
                    'id': track_details['id'],
                    'image': track_details['album']['cover_xl'],
                    'artist': track_details['artist']['name'],
                    'preview_url': track_details['preview'],
                    'deezer_url': track_details['link'],
                    'album': track_details['album']['title'],
                    'duration': track_details.get('duration', 0),
                    'lastfm_verified': True,
                    'is_new_release': is_new_release
                })

            except Exception as e:
                print(f"Error processing {track['name']}: {e}")
                continue

        self.storage_manager.finalized_data = track_data
        print(
            f"\nSuccessfully processed {len(track_data)} unique tracks with Deezer data")
        return self.storage_manager.finalized_data

    def fetch_user_songs_streamed(self):
        """
        Enhanced version of fetch_user_songs_streamed with better error handling,
        memory management, and timeouts.
        
        This is a generator that yields processed track data one at a time to 
        prevent memory buildup.
        """
        # Set up logging
        logging.info("Starting streaming recommendations process")
        
        # Clear memory before starting
        gc.collect()
        
        try:
            # Get optimized tracks - use a try/except to prevent generator from failing
            try:
                self.tracks = self.get_tracks()
                if not self.tracks:
                    logging.warning("No recommendations available")
                    yield {"error": "No recommendations available"}
                    return
            except Exception as e:
                logging.error(f"Error getting tracks: {str(e)}")
                yield {"error": "Error generating recommendations"}
                return
            
            logging.info('Fetching track data using deezer api for optimized recommendations...')
            
            track_ids_seen = set()
            processed_count = 0
            error_count = 0
            max_errors = 5  # Maximum consecutive errors before giving up
            consecutive_errors = 0
            
            for track in self.get_tracks():
                try:
                    # Add a small delay between tracks to prevent API rate limiting
                    if processed_count > 0:
                        time.sleep(0.2)
                    
                    # Basic validation
                    if not isinstance(track, dict):
                        continue
                        
                    track_name = track.get('name', '')
                    artist = track.get('artist', '')
                    
                    if not track_name or not artist:
                        continue
                    
                    logging.info(f"Processing track: {track_name} by {artist}")
                    
                    primary_artist = self.extract_primary_artist(artist)
                    
                    # Try multiple search strategies with error handling
                    deezer_result = None
                    
                    try:
                        # Strategy 1: Exact match
                        deezer_result = self.get_deezer_track_info(track_name, primary_artist)
                    except Exception as search_error:
                        logging.warning(f"Error in exact search: {str(search_error)}")
                    
                    if not deezer_result:
                        try:
                            # Strategy 2: Without artist
                            deezer_result = self.get_deezer_track_info(track_name, "")
                        except Exception as search_error:
                            logging.warning(f"Error in no-artist search: {str(search_error)}")
                    
                    if not deezer_result:
                        try:
                            # Strategy 3: Simplified track name
                            simplified_name = self.simplify_track_name(track_name)
                            if simplified_name != track_name:
                                deezer_result = self.get_deezer_track_info(simplified_name, primary_artist)
                        except Exception as search_error:
                            logging.warning(f"Error in simplified search: {str(search_error)}")
                    
                    # If no result after all strategies, continue to next track
                    if not deezer_result:
                        logging.warning(f"Could not find track: {track_name} by {artist}")
                        consecutive_errors += 1
                        
                        if consecutive_errors >= max_errors:
                            logging.error(f"Too many consecutive errors ({max_errors}). Stopping processing.")
                            yield {"error": "Too many lookup failures. Please try again later."}
                            break
                            
                        continue
                    
                    # Reset consecutive error counter on success
                    consecutive_errors = 0
                    
                    # Prevent duplicates
                    track_id = deezer_result.get('id')
                    if not track_id or track_id in track_ids_seen:
                        continue
                        
                    track_ids_seen.add(track_id)
                    
                    # Get detailed track info with error handling
                    try:
                        track_details = self.get_deezer_track_by_id(track_id)
                    except Exception as detail_error:
                        logging.warning(f"Error getting detailed track info: {str(detail_error)}")
                        track_details = None
                        
                    if not track_details:
                        track_details = deezer_result
                    
                    # Check if we have all required fields before yielding
                    required_fields = ['title', 'id', 'album', 'artist', 'preview', 'link']
                    for field in required_fields:
                        if field not in track_details:
                            if field == 'album' or field == 'artist':
                                if not isinstance(track_details.get(field, {}), dict):
                                    logging.warning(f"Missing or invalid {field} in track details")
                                    continue
                            else:
                                logging.warning(f"Missing {field} in track details")
                                continue
                    
                    # Format the result
                    is_new_release = track.get('source') == 'new_release'
                    
                    result = {
                        'name': track_details['title'],
                        'id': track_details['id'],
                        'image': track_details['album'].get('cover_xl', ''),
                        'artist': track_details['artist'].get('name', artist),
                        'preview_url': track_details.get('preview', ''),
                        'deezer_url': track_details.get('link', ''),
                        'album': track_details['album'].get('title', ''),
                        'duration': track_details.get('duration', 0),
                        'lastfm_verified': True,
                        'is_new_release': is_new_release
                    }
                    
                    # Yield the track and increment counter
                    processed_count += 1
                    logging.info(f"Successfully processed track: {result['name']} by {result['artist']}")
                    
                    yield result
                    
                    # Force garbage collection every 5 tracks
                    if processed_count % 5 == 0:
                        gc.collect()
                        
                except Exception as e:
                    error_count += 1
                    logging.error(f"Error processing track {track.get('name', 'unknown')}: {str(e)}")
                    consecutive_errors += 1
                    
                    if consecutive_errors >= max_errors:
                        logging.error(f"Too many consecutive errors ({max_errors}). Stopping processing.")
                        yield {"error": "Too many processing failures. Please try again later."}
                        break
                        
                    continue
            
            logging.info(f"Streaming complete. Processed {processed_count} tracks with {error_count} errors")
            
        except Exception as e:
            logging.error(f"Critical error in streaming process: {str(e)}")
            yield {"error": "An error occurred during recommendation streaming"}
        finally:
            # Final cleanup
            gc.collect()
            
    # ! <---- Dont know why this is added, this cn be removed it not needed or planned to be used
    def organize_by_playlist(self):
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
    pass

    # pm = PlaylistManager()
    # result = pm.combining_playlist_and_track()
    # print(result)

    # ai = RecommendationManager()
    # result = ai.format_recommendations()
    # print(result)

    # sm = SpotifyManagement()
    # result = sm.fetch_user_songs()
    # print(result)
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
