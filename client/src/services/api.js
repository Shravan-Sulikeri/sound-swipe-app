import { useEffect, useState, useRef } from "react";
export const API_BASE_URL = process.env.API_BASE_URL;

// recommendation model
export const getSampleTracks = async (count = 20) => {
	try {
		const response = await fetch(`${API_BASE_URL}/api/recommendations`, {
			credentials: "include",
		});
		if (!response.ok) {
			throw new Error("Failed to fetch sample tracks");
		}
		const data = await response.json();
		return data.data.map((track) => ({
			id: track.id,
			name: track.name,
			artists: track.artist,
			coverImage: track.image,
			previewUrl: track.preview_url,
		}));
	} catch (error) {
		console.error("Error fetching sample tracks:", error);
		throw error;
	}
};

export const getRecommendations = async (likedSongIds, count = 20) => {
	try {
		const response = await fetch(`${API_BASE_URL}/api/recommendations`);
		if (!response.ok) {
			throw new Error("Failed to get recommendations");
		}

		const data = await response.json();
		return data.data.map((track) => ({
			id: track.id,
			name: track.name,
			artists: track.artist,
			coverImage: track.image,
			previewUrl: track.preview_url,
		}));
	} catch (error) {
		console.error("Error getting recommendations:", error);
		throw error;
	}
};

// playlists
export async function getPlaylists() {
	try {
		const response = await fetch(`${API_BASE_URL}/api/playlists`, {
			credentials: "include",
		});

		if (!response.ok) {
			let errorMsg = "Failed to retrieve playlists";
			try {
				const errorData = await response.json();
				errorMsg = errorData.error || errorMsg;
			} catch (e) {
				// If JSON parsing fails, use status text
				errorMsg = response.statusText || errorMsg;
			}
			throw new Error(errorMsg);
		}

		const playlists = await response.json();

		return playlists.map((playlist) => ({
			id: playlist.id,
			name: playlist.name,
			songs: playlist.tracks?.href,
			songCount: playlist.tracks?.total || 0,
			coverImage:
				playlist.images?.[0]?.url || "https://via.placeholder.com/100",
		}));
	} catch (error) {
		console.error("Error getting playlists:", error);
		return [];
	}
}

export const createPlaylist = async (playlistName) => {
	try {
		const response = await fetch(`${API_BASE_URL}/api/create-playlist`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json", // Missing content type header
			},
			credentials: "include", // Missing credentials for cookies
			body: JSON.stringify({
				name: playlistName,
			}),
		});

		if (!response.ok) {
			const errorData = await response.json();
			console.error("Failed to create playlist:", errorData);
			throw new Error(errorData.error || "Failed to create playlist");
		}

		const data = await response.json();
		console.log("Playlist created successfully:", data);
		return data;
	} catch (error) {
		console.error("Error creating playlist:", error);
		throw error;
	}
};

export const deletePlaylist = async (playlistId, accessToken) => {
	try {
		const response = await fetch(`${API_BASE_URL}/api/delete-playlist`, {
			method: "DELETE",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${accessToken}`,
			},
			credentials: "include",
			body: JSON.stringify({ playlist_id: playlistId }),
		});

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.details || "Failed to delete playlist");
		}

		return await response.json();
	} catch (error) {
		console.error("Delete playlist error:", error);
		throw error;
	}
};

//tracks
export const addTrack = async (trackId, playlistId) => {
	try {
		// Make sure we have a trackId and playlistId
		if (!trackId) {
			throw new Error("Track ID is required");
		}

		if (!playlistId) {
			throw new Error("Playlist ID is required");
		}

		// Format the track URI if it's not already formatted
		const trackUri = trackId.startsWith("spotify:track:")
			? trackId
			: `spotify:track:${trackId}`;

		// Call the backend API to add the track to the playlist
		const response = await fetch(`${API_BASE_URL}/api/add-track`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			credentials: "include",
			body: JSON.stringify({
				playlist_id: playlistId,
				track_uris: [trackUri],
			}),
		});

		// Parse and check the response
		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.error || "Failed to add track to playlist");
		}

		const data = await response.json();

		// Return the response data
		return {
			success: true,
			playlistId: data.playlist_id,
			tracksAdded: data.tracks_added,
			snapshotId: data.snapshot_id,
		};
	} catch (error) {
		console.error("Error adding track to playlist:", error);
		return {
			success: false,
			error: error.message || "Unknown error occurred",
		};
	}
};

export const removeTrack = async (trackId, playlistId) => {
	try {
		// Make sure we have a trackId and playlistId
		if (!trackId) {
			throw new Error("Track ID is required");
		}

		if (!playlistId) {
			throw new Error("Playlist ID is required");
		}

		// Format the track URI if it's not already formatted
		const trackUri = trackId.startsWith("spotify:track:")
			? trackId
			: `spotify:track:${trackId}`;

		// Call the backend API to remove the track from the playlist
		const response = await fetch(`${API_BASE_URL}/api/remove-track`, {
			method: "DELETE",
			headers: {
				"Content-Type": "application/json",
			},
			credentials: "include",
			body: JSON.stringify({
				playlist_id: playlistId,
				track_uris: [trackUri],
			}),
		});

		// Parse and check the response
		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(
				errorData.error || "Failed to remove track from playlist"
			);
		}

		const data = await response.json();

		// Return the response data
		return {
			success: true,
			playlistId: data.playlist_id,
			tracksRemoved: data.tracks_removed,
			snapshotId: data.snapshot_id,
		};
	} catch (error) {
		console.error("Error removing track from playlist:", error);
		return {
			success: false,
			error: error.message || "Unknown error occurred",
		};
	}
};

export const searchSpotifyTrack = async (trackName, artistName) => {
	try {
		const response = await fetch(`${API_BASE_URL}/api/search-track`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			credentials: "include",
			body: JSON.stringify({
				track: trackName,
				artist: artistName,
			}),
		});

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.error || "Failed to search for track");
		}

		const data = await response.json();
		return {
			id: data.spotifyId,
			uri: data.uri, // Store the full URI for adding to playlists
			name: data.name,
			artist: data.artist,
			albumArt: data.albumArt,
			success: !!data.spotifyId,
		};
	} catch (error) {
		console.error("Error searching for track:", error);
		return { success: false, error: error.message };
	}
};

export async function getSongsFromPlaylist(playlistId) {
	try {
		const response = await fetch(`${API_BASE_URL}/api/playlist/${playlistId}`, {
			credentials: "include",
		});

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.error || "Failed to fetch playlist songs");
		}

		const data = await response.json();
		return data.tracks || [];
	} catch (error) {
		console.error("Error fetching playlist songs:", error);
		throw error; // Re-throw for the caller to handle
	}
};

// Make sure to import this function where needed
export const getDisplayName = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/display_name`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/json'
      }
    });
    
    console.log('Display name response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => null);
      console.error('Error response body:', errorText);
      throw new Error(`Failed to fetch display name: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('Display name response data:', data);
    
    if (!data.display_name) {
      console.warn('Response does not contain display_name:', data);
      return 'Spotify User';
    }
    
    return data.display_name;
  } catch (error) {
    console.error('Error getting display name:', error);
    return 'Spotify User';
  }
};

export const useStreamedRecommendations = () => {
  const [tracks, setTracks] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const seenTrackIds = useRef(new Set());
  const isInitialBatch = useRef(true);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 3;

  useEffect(() => {
    let eventSource;

    const connect = () => {
      console.log(`[Stream] Connecting to recommendations stream (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);
      eventSource = new EventSource(`${API_BASE_URL}/api/recommendations-stream`, {
        withCredentials: true,
      });

      eventSource.onopen = () => {
        console.log("[Stream] Successfully connected to recommendations stream");
        reconnectAttempts.current = 0;
      };

      eventSource.onmessage = (event) => {
        try {
          const batch = JSON.parse(event.data);
          if (Array.isArray(batch)) {
            console.log(`[Stream] Received batch of ${batch.length} tracks`);
            
            // Filter out tracks we've already seen
            const newTracks = batch.filter(track => {
              if (seenTrackIds.current.has(track.id)) {
                console.log(`[Stream] Skipping duplicate track: ${track.name} by ${track.artist}`);
                return false;
              }
              seenTrackIds.current.add(track.id);
              console.log(`[Stream] New track: ${track.name} by ${track.artist}`);
              return true;
            });

            if (newTracks.length > 0) {
              const formattedTracks = newTracks.map(track => ({
                id: track.id,
                name: track.name,
                artists: track.artist,
                coverImage: track.image,
                previewUrl: track.preview_url,
              }));

              if (isInitialBatch.current) {
                console.log(`[Stream] Setting initial batch of ${formattedTracks.length} tracks`);
                setTracks(formattedTracks);
                isInitialBatch.current = false;
                setIsLoading(false);
              } else {
                console.log(`[Stream] Adding ${formattedTracks.length} new tracks to existing queue`);
                setTracks(prev => [...prev, ...formattedTracks]);
              }
            } else {
              console.log("[Stream] No new tracks in this batch");
            }
          } else if (batch.error) {
            console.error("[Stream] Error in recommendation stream:", batch.error);
            setError(batch.error);
            setIsLoading(false);
          }
        } catch (err) {
          console.error("[Stream] Failed to parse track batch:", err);
          setIsLoading(false);
        }
      };

      eventSource.onerror = (err) => {
        console.error("[Stream] EventSource error:", err);
        eventSource.close();
        
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
          console.log(`[Stream] Attempting to reconnect in ${delay/1000} seconds... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
          setTimeout(connect, delay);
        } else {
          console.error("[Stream] Max reconnection attempts reached");
          setError("Failed to connect to recommendations stream after multiple attempts");
          setIsLoading(false);
        }
      };
    };

    connect();

    return () => {
      console.log("[Stream] Cleaning up stream connection");
      if (eventSource) {
        eventSource.close();
      }
      seenTrackIds.current.clear();
      isInitialBatch.current = true;
      reconnectAttempts.current = 0;
    };
  }, []);

  return { tracks, error, isLoading };
};