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
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
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

    # ! This function is ONLY for testing purposes
    def fetch_current_user_playlists(self, token, user_id="w5e01d35jtoh0qo6j060vr7jv"):
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

    # ! Need to get AUTH working for this function
    def fetch_logged_in_user_playlist(self, token):
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
            for x in json_result:
                name = x['name']
                id = x['id']
                final = ({"name": name, "id": id})
                playlist.append(final)
        return playlist

    # ! This is ONLY for testing purposes
    def fetch_track_from_playlist(self, auth_token, playlist_id="3FCcErUVRSiCJl2J9stvhI"):
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
                if track['track']:
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
                playlist = self.spotify_api.fetch_logged_in_user_playlist(
                    self.token)
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


class LastFmAPI:  # ! <---- This is the class that will be used to get the last.fm data, this is helping to increase the recommendations and get more data on the songs
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("LAST_FM_API_KEY")

    # ! <---- This is the function that will be used to get the similar artist from last.fm
    def get_similar_artist(self, artist_name):
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
                similar_artists = [x['name']
                                   for x in data['similarartists']['artist']]
                return similar_artists
            else:
                print(f"No similar artists found for {artist_name}")
                return None
        else:
            print(
                f"LastFM API error {response.status_code} when finding similar artists for {artist_name}")
            return None

    # ! <---- This is the function that will be used to get the similar tracks from last.fm
    def get_similar_tracks(self, track_name, artist_name):
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
                print(
                    f"No similar tracks found for {track_name} by {artist_name}")
                return None
        else:
            print(
                f"LastFM API error {response.status_code} when finding similar tracks for {track_name}")
            return None

    # ! <---- This is the function that will be used to get the track info from last.fm
    def get_track_info(self, track_name, artist_name):
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
            print(
                f"LastFM API error {response.status_code} when getting track info for {track_name}")
            return None

    # ! <---- This is the function that will be used to get the top tracks from last.fm
    def get_artist_top_tracks(self, artist_name, limit=10):
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
            print(
                f"LastFM API error {response.status_code} when getting top tracks for {artist_name}")
            return None


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
        Optimizes recommendations using LLM seeds to get better recommendations:
        1. Use original LLM recommendation as seed only (not included in final output)
        2. Get 3 tracks from similar artists (primary source)
        3. Get 1 similar track from Last.fm (secondary source)
        4. Get 1 top track from original artist (tertiary source)
        """
        recommendations = self.format_recommendations()
        optimized_recommendations = {}
        all_recommended_tracks = set()

        for playlist_id, tracks in recommendations.items():
            optimized_tracks = []

            for track in tracks:
                track_name = track["track_name"]
                artist_name = track["artist_name"]

                print(f"\n🎧 Processing seed: {track_name} by {artist_name}")
                lastfm_recommendations = []
                
                # Track the seed to avoid recommending it
                seed_track_key = f"{track_name.lower()}|{artist_name.lower()}"
                all_recommended_tracks.add(seed_track_key)  # Add to seen but don't include in output

                # 1. First priority: Get tracks from similar artists (3 tracks)
                similar_artists_count = 0
                similar_artists = self.similarity.get_similar_artist(artist_name)
                if similar_artists:
                    for similar_artist in similar_artists[:8]:  # Try up to 8 similar artists to find 3 good tracks
                        if similar_artists_count >= 3:
                            break

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

                # 2. Second priority: Get 1 similar track from Last.fm
                similar_track_found = False
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

                # 3. Third priority: Get 1 top track from the original artist
                top_track_found = False
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
                                            
                optimized_tracks.extend(lastfm_recommendations)

            optimized_recommendations[playlist_id] = optimized_tracks

        # Add new releases
        new_releases = self.incorporate_new_releases()
        if new_releases:
            for playlist_id, tracks in optimized_recommendations.items():
                if len(tracks) < 12:
                    added_count = 0
                    for release in new_releases:
                        if added_count >= 3:  # Add up to 3 new releases
                            break

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

        # Remove any duplicates that might have slipped through
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
        Retrieves tracks from the optimized LLM + LastFM recommendation process.
        Returns:
            List of dictionaries with track details.
        """
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
class UserPreferenceRecommender: #! <----- NOTE DISREGARD HAS NOT BEEN TESTED COMPLETE AI SLOP 
    def __init__(self, user_token=None):
        self.spotify_api = SpotifyAPI(external_token=user_token)
        self.lastfm_api = LastFmAPI()
        self.storage = GlobalVariables()
        self.user_token = user_token
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = 'llama-3.3-70b-versatile'
        self.groq = Groq(api_key=self.api_key)
        self.seen_tracks = set()  # Track IDs the user has already seen
        
    def get_more_recommendations(self, playlist_id=None, count=10):
        """
        Generate more recommendations when a user runs out of songs to swipe,
        based on the original playlist structure but with new tracks.
        
        Args:
            playlist_id: Optional specific playlist to get more recommendations for
            count: Number of recommendations to generate
            
        Returns:
            List of track dictionaries with complete track info
        """
        print(f"Generating {count} more recommendations for swiping...")
        
        # 1. Get the original recommendations to use as seeds
        original_recommender = RecommendationManager(user_token=self.user_token)
        recommendations = original_recommender.get_enhanced_recommendations()
        
        if not recommendations:
            print("No original recommendations found to use as seeds")
            return []
            
        # 2. If playlist_id is specified, only use that playlist's seeds
        if playlist_id and playlist_id in recommendations:
            seed_tracks = recommendations[playlist_id]
            selected_playlist = {playlist_id: seed_tracks}
        else:
            # Otherwise, use tracks from all playlists
            selected_playlist = recommendations
            
        # 3. Generate new recommendations using existing tracks as seeds
        new_tracks = []
        
        for pl_id, tracks in selected_playlist.items():
            # Limit seeds to avoid too many similar recommendations
            seed_limit = min(5, len(tracks))
            
            for i, track in enumerate(tracks[:seed_limit]):
                if len(new_tracks) >= count:
                    break
                    
                track_name = track['track_name']
                artist_name = track['artist_name']
                print(f"Using seed: {track_name} by {artist_name}")
                
                # Get recommendations from similar artists
                similar_artists = self.lastfm_api.get_similar_artist(artist_name)
                if similar_artists:
                    for similar_artist in similar_artists[:3]:
                        if len(new_tracks) >= count:
                            break
                            
                        # Get top tracks from this similar artist
                        artist_tracks = self.lastfm_api.get_artist_top_tracks(similar_artist, 3)
                        if artist_tracks:
                            for artist_track in artist_tracks:
                                track_key = f"{artist_track['name'].lower()}|{artist_track['artist'].lower()}"
                                
                                # Check if we've already seen this track
                                if track_key not in self.seen_tracks:
                                    new_tracks.append({
                                        "track_name": artist_track["name"],
                                        "artist_name": artist_track["artist"],
                                        "source": "more_recommendations"
                                    })
                                    self.seen_tracks.add(track_key)
                                    
                                    if len(new_tracks) >= count:
                                        break
        
        # 4. If we still don't have enough tracks, get similar tracks to seeds
        if len(new_tracks) < count:
            for pl_id, tracks in selected_playlist.items():
                for track in tracks[:seed_limit]:
                    if len(new_tracks) >= count:
                        break
                        
                    track_name = track['track_name']
                    artist_name = track['artist_name']
                    
                    # Get tracks similar to this seed
                    similar_tracks = self.lastfm_api.get_similar_tracks(track_name, artist_name)
                    if similar_tracks:
                        for similar in similar_tracks:
                            similar_key = f"{similar['name'].lower()}|{similar['artist'].lower()}"
                            
                            if similar_key not in self.seen_tracks:
                                new_tracks.append({
                                    "track_name": similar["name"],
                                    "artist_name": similar["artist"],
                                    "source": "more_recommendations"
                                })
                                self.seen_tracks.add(similar_key)
                                
                                if len(new_tracks) >= count:
                                    break
        
        # 5. As a last resort, add some new releases
        if len(new_tracks) < count:
            spotify_mgmt = SpotifyManagement(user_token=self.user_token)
            new_releases = spotify_mgmt.spotify_api.fetch_new_releases()
            
            if new_releases:
                for release in new_releases:
                    release_key = f"{release['name'].lower()}|{release['artist'].lower()}"
                    
                    if release_key not in self.seen_tracks:
                        new_tracks.append({
                            "track_name": release["name"],
                            "artist_name": release["artist"],
                            "source": "new_release"
                        })
                        self.seen_tracks.add(release_key)
                        
                        if len(new_tracks) >= count:
                            break
        
        # 6. Get full track info using Deezer API
        spotify_mgmt = SpotifyManagement(user_token=self.user_token)
        spotify_mgmt.storage_manager.music = new_tracks
        full_track_data = spotify_mgmt.fetch_user_songs()
        
        return full_track_data
    
    def recommend_from_liked_songs(self, liked_songs, count=15):
        """
        Generate personalized recommendations based on the songs a user has liked/swiped right on.
        
        Args:
            liked_songs: List of track dictionaries the user has liked
            count: Number of recommendations to generate
            
        Returns:
            List of track dictionaries with complete track info
        """
        if not liked_songs or len(liked_songs) == 0:
            print("No liked songs available to base recommendations on")
            return []
            
        print(f"Generating {count} recommendations based on {len(liked_songs)} liked songs...")
        
        # 1. Analyze liked songs to identify patterns/preferences
        artists = {}
        genres = set()
        
        for song in liked_songs:
            artist = song.get('artist', '')
            if artist:
                artists[artist] = artists.get(artist, 0) + 1
        
        # Find top artists (most frequently liked)
        top_artists = sorted(artists.items(), key=lambda x: x[1], reverse=True)
        top_artists = [artist for artist, count in top_artists[:5]]
        
        # 2. Generate recommendations based on top artists and liked songs
        new_recommendations = []
        
        # First try: get tracks from similar artists to top artists
        for artist in top_artists:
            if len(new_recommendations) >= count:
                break
                
            similar_artists = self.lastfm_api.get_similar_artist(artist)
            if similar_artists:
                for similar_artist in similar_artists[:3]:
                    if len(new_recommendations) >= count:
                        break
                        
                    top_tracks = self.lastfm_api.get_artist_top_tracks(similar_artist, 3)
                    if top_tracks:
                        for track in top_tracks:
                            track_key = f"{track['name'].lower()}|{track['artist'].lower()}"
                            
                            # Check if we've already seen this track
                            if track_key not in self.seen_tracks:
                                new_recommendations.append({
                                    "track_name": track["name"],
                                    "artist_name": track["artist"],
                                    "source": "liked_songs_recommendation"
                                })
                                self.seen_tracks.add(track_key)
                                
                                if len(new_recommendations) >= count:
                                    break
        
        # Second try: get similar tracks to liked songs
        if len(new_recommendations) < count:
            # Use a sample of liked songs to get similar tracks
            sample_size = min(5, len(liked_songs))
            for song in liked_songs[:sample_size]:
                if len(new_recommendations) >= count:
                    break
                    
                track_name = song.get('name', '')
                artist_name = song.get('artist', '')
                
                if track_name and artist_name:
                    similar_tracks = self.lastfm_api.get_similar_tracks(track_name, artist_name)
                    if similar_tracks:
                        for similar in similar_tracks:
                            similar_key = f"{similar['name'].lower()}|{similar['artist'].lower()}"
                            
                            if similar_key not in self.seen_tracks:
                                new_recommendations.append({
                                    "track_name": similar["name"],
                                    "artist_name": similar["artist"],
                                    "source": "liked_songs_recommendation"
                                })
                                self.seen_tracks.add(similar_key)
                                
                                if len(new_recommendations) >= count:
                                    break
        
        # Third try: Use LLM to analyze patterns and generate more diverse recommendations
        if len(new_recommendations) < count:
            try:
                # Create a sample of liked songs for the prompt
                liked_sample = liked_songs[:10] if len(liked_songs) > 10 else liked_songs
                liked_songs_text = "\n".join([f"- {song.get('name', 'Unknown')} by {song.get('artist', 'Unknown')}" for song in liked_sample])
                
                prompt = (
                    f"Based on these songs the user likes:\n\n{liked_songs_text}\n\n"
                    f"Recommend {count - len(new_recommendations)} more songs that match their taste. "
                    "Ensure recommendations are diverse but still match the user's preferences.\n\n"
                    "RESPOND EXACTLY IN THIS JSON FORMAT:\n"
                    "[\n"
                    "  {\"name\": \"Song1\", \"artist\": \"Artist1\"},\n"
                    "  {\"name\": \"Song2\", \"artist\": \"Artist2\"}\n"
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
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                    stream=False,
                )
                
                llm_response = chat_completion.choices[0].message.content
                try:
                    llm_recommendations = json.loads(llm_response)
                    
                    # Use these recommendations to find real songs in LastFM
                    for rec in llm_recommendations:
                        if len(new_recommendations) >= count:
                            break
                            
                        rec_name = rec.get('name', '')
                        rec_artist = rec.get('artist', '')
                        
                        if rec_name and rec_artist:
                            # Check if we've already seen this track
                            rec_key = f"{rec_name.lower()}|{rec_artist.lower()}"
                            
                            if rec_key not in self.seen_tracks:
                                # Try to verify this exists via LastFM
                                track_info = self.lastfm_api.get_track_info(rec_name, rec_artist)
                                
                                if track_info:
                                    new_recommendations.append({
                                        "track_name": rec_name,
                                        "artist_name": rec_artist,
                                        "source": "liked_songs_recommendation"
                                    })
                                    self.seen_tracks.add(rec_key)
                                else:
                                    # If track not found, try getting similar artists' tracks
                                    similar_artists = self.lastfm_api.get_similar_artist(rec_artist)
                                    if similar_artists and len(similar_artists) > 0:
                                        top_tracks = self.lastfm_api.get_artist_top_tracks(similar_artists[0], 1)
                                        if top_tracks and len(top_tracks) > 0:
                                            top_track = top_tracks[0]
                                            top_key = f"{top_track['name'].lower()}|{top_track['artist'].lower()}"
                                            
                                            if top_key not in self.seen_tracks:
                                                new_recommendations.append({
                                                    "track_name": top_track["name"],
                                                    "artist_name": top_track["artist"],
                                                    "source": "liked_songs_recommendation"
                                                })
                                                self.seen_tracks.add(top_key)
                                
                                if len(new_recommendations) >= count:
                                    break
                                    
                except json.JSONDecodeError:
                    print("LLM did not return valid JSON")
                    
            except Exception as e:
                print(f"Error using LLM for recommendations: {e}")
        
        # 6. Get full track info using Deezer API
        spotify_mgmt = SpotifyManagement(user_token=self.user_token)
        spotify_mgmt.storage_manager.music = new_recommendations
        full_track_data = spotify_mgmt.fetch_user_songs()
        
        return full_track_data

# ! <--- This is a tester function but keep in mind that if there is no logged in user it will not work.
def main():
    fetch = SpotifyManagement()
    fetch_songs = fetch.fetch_user_songs()
    return fetch_songs


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
