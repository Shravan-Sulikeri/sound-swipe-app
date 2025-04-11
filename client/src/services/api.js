export const API_BASE_URL = "http://localhost:3001";

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

// TO TEST

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

export async function getSongsFromPlaylist(playlistId) {
	const response = await fetch(`${API_BASE_URL}/api/playlist/${playlistId}`);
	const data = await response.json();
	return data;
}

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
		const response = await fetch("/api/add-track", {
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
		const response = await fetch("/api/remove-track", {
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
