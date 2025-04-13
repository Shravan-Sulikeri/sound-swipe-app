import React, { useState, useRef, useEffect } from "react";
import useAudioControls from "../hooks/useAudioControls";
import "../styling/home.css";
import Sidebar from "../components/Sidebar";
import MainContent from "../components/Main";
import CreatePlaylistModal from "../components/CreateModal";
import DeletePlaylistModal from "../components/DeleteModal";
import SoundwaveLoader from "../components/SoundwaveLoader";
import NoSongsScreen from "../components/NoSongs";
import {
	getSampleTracks,
	getRecommendations,
	getSongsFromPlaylist,
	API_BASE_URL,
	getPlaylists,
	createPlaylist,
	deletePlaylist,
	addTrack,
	removeTrack,
	searchSpotifyTrack,
} from "../services/api";

const Home = () => {
	const [isSwiping, setIsSwiping] = useState(false);
	const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
	const [playlists, setPlaylists] = useState([]);
	const [currentSong, setCurrentSong] = useState(null);
	const [songQueue, setSongQueue] = useState([]);
	const [likedSongs, setLikedSongs] = useState([]);
	const [isDragging, setIsDragging] = useState(false);
	const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
	const [cardTransform, setCardTransform] = useState({ x: 0, y: 0, rotate: 0 });
	const [isLoading, setIsLoading] = useState(false);

	// Modal states
	const [showCreateModal, setShowCreateModal] = useState(false);
	const [activePlaylist, setActivePlaylist] = useState(null);
	const [isLoadingSongs, setIsLoadingSongs] = useState(false);

	// Delete confirmation modal
	const [playlistToDelete, setPlaylistToDelete] = useState(null);

	const audioRef = useRef(null);
	const cardRef = useRef(null);

	// audio controls
	const {
		isPlaying,
		progress,
		currentTime,
		duration,
		handleTimeUpdate,
		handleLoadedMetadata,
		controlAudio,
	} = useAudioControls(audioRef);

	const [playlistSongs, setPlaylistSongs] = useState([]);

	const loadPlaylists = async () => {
		// First try to load from cache for instant display
		const cached = localStorage.getItem("cachedPlaylists");
		if (cached) {
			setPlaylists(JSON.parse(cached));
		}

		// Then fetch fresh data in background
		try {
			const fresh = await getPlaylists();
			setPlaylists(fresh);
			localStorage.setItem("cachedPlaylists", JSON.stringify(fresh));
		} catch (error) {
			console.error("Playlist refresh failed:", error);
		}
	};

	// Initialize songs when component mounts
	useEffect(() => {
		const initializeData = async () => {
			setIsLoading(true);
			try {
				await Promise.all([
					getSampleTracks(20)
						.then((songs) => {
							if (songs?.length > 0) {
								setCurrentSong(songs[0]);
								setSongQueue(songs.slice(1));
							} else {
								console.error("No songs received from the API");
							}
						})
						.catch((error) =>
							console.error("Error loading initial songs:", error)
						),
					loadPlaylists(), // Handles both cache and fresh data
				]);
			} catch (error) {
				console.error("Error loading data:", error);
			} finally {
				setIsLoading(false);
			}
		};
		initializeData();
	}, []);

	const handleLogout = () => {
		window.location.href = `${API_BASE_URL}/logout`;
	};

	const handleCreatePlaylist = async (playlistName) => {
		try {
			const playlistData = await createPlaylist(playlistName);

			if (!playlistData?.id) {
				throw new Error("Failed to create playlist - no ID returned");
			}

			// Create the new playlist object
			const newPlaylist = {
				id: playlistData.id,
				name: playlistName,
				songs: [],
				songCount: 0,
				coverImage:
					likedSongs[0]?.coverImage || "https://via.placeholder.com/100",
			};

			// Update state
			setPlaylists([...playlists, newPlaylist]);
			setActivePlaylist(newPlaylist.id);
			setShowCreateModal(false);

			// Simple success feedback
			console.log("Playlist created successfully:", newPlaylist);
		} catch (error) {
			console.error("Playlist creation error:", error);

			// Basic error feedback
			let errorMessage = "Failed to create playlist";

			alert(errorMessage);

			// Reopen modal if error occurred
			setShowCreateModal(true);
		}
	};

	const handlePlaylistSelect = async (playlistId) => {
		setIsLoadingSongs(true);

		try {
			if (activePlaylist === playlistId) {
				setActivePlaylist(null);
				setPlaylistSongs([]);
				return;
			}

			setActivePlaylist(playlistId);
			const selected = playlists.find((p) => p.id === playlistId);
			if (!selected) {
				console.warn("Playlist not found");
				return;
			}

			const songs = await getSongsFromPlaylist(playlistId);
			setPlaylistSongs(songs);
		} catch (error) {
			console.error("Error handling playlist selection:", error);
			// Optional: Set error state
			// setPlaylistError(error.message);
		} finally {
			setIsLoadingSongs(false);
		}
	};

	const handleDeleteClick = async (e, playlistId) => {
		e.stopPropagation(); // Prevent playlist selection when clicking delete
		setPlaylistToDelete(playlistId);
	};

	const handleDeletePlaylist = async (playlistId) => {
		try {
			await deletePlaylist(playlistId);

			// Update UI state
			setPlaylists((prev) => prev.filter((p) => p.id !== playlistId));
			if (activePlaylist === playlistId) {
				setActivePlaylist(null);
			}
			console.log(`Playlist ${playlistToDelete} deleted successfully`);
		} catch (error) {
			console.error("Deletion failed:", error);
		}
	};

	const handleDeleteSong = async (playlistId, songIndex) => {
		// Find the song to remove from local state
		if (!playlistSongs?.[songIndex]) {
			console.warn("No song found at index:", songIndex);
			return;
		}

		const songToRemove = playlistSongs[songIndex];

		// Check if we have the Spotify URI (should always be true if coming from playlist)
		if (!songToRemove.uri) {
			console.error("Song missing Spotify URI:", songToRemove);
			return;
		}

		try {
			// Call API to remove the track using the URI we already have
			const result = await removeTrack(songToRemove.uri, playlistId);

			if (result.success) {
				console.log(
					`Track ${songToRemove.name} removed from playlist successfully`
				);

				// Update local state immediately (optimistic update)
				setPlaylistSongs((prevSongs) => [
					...prevSongs.slice(0, songIndex),
					...prevSongs.slice(songIndex + 1),
				]);

				// Optional: You might want to refresh the playlist data from server
				// const updatedSongs = await getSongsFromPlaylist(playlistId);
				// setPlaylistSongs(updatedSongs);
			} else {
				console.error("Failed to remove track from playlist:", result.error);
				// Optional: Show error to user
			}
		} catch (error) {
			console.error("Error removing track from playlist:", error);
			// Optional: Show error to user
		}
	};

	const handleExitSwiping = () => {
		setIsSwiping(false);
		controlAudio("pause");
	};

	const toggleSidebar = () => {
		setIsSidebarCollapsed(!isSidebarCollapsed);
	};

	const handleSwipe = async (direction) => {
		const card = cardRef.current;
		if (!card || !currentSong) return;

		card.classList.add(`swiped-${direction}`);
		// Song is liked
		if (direction === "right") {
			// Add to liked songs
			setLikedSongs((prev) => [...prev, currentSong]);

			// Add to active playlist if one is selected
			if (activePlaylist) {
				try {
					// Extract artist name - assuming artists is a string or array
					const artistName = Array.isArray(currentSong.artists)
						? currentSong.artists[0]
						: currentSong.artists;

					// Search for track in Spotify
					const searchResult = await searchSpotifyTrack(
						currentSong.name,
						artistName
					);

					if (searchResult.success) {
						// Use the track URI for adding to playlist
						const trackUri = searchResult.uri;

						// Call the API to add the track to the playlist
						const result = await addTrack(trackUri, activePlaylist);
						if (result.success) {
							console.log(
								`Track ${currentSong.name} added to playlist successfully`
							);
						} else {
							console.error("Failed to add track to playlist:", result.error);
						}
					} else {
						console.warn(
							`Could not find ${currentSong.name} by ${artistName} on Spotify`
						);
					}
				} catch (error) {
					console.error("Error adding track to playlist:", error);
				}

				// Update the UI regardless of API success
				setPlaylists((prevPlaylists) =>
					prevPlaylists.map((playlist) => {
						if (playlist.id === activePlaylist) {
							const updatedSongs = [...playlist.songs, currentSong];
							return {
								...playlist,
								songs: updatedSongs,
								songCount: updatedSongs.length,
								coverImage:
									playlist.songs.length === 0
										? currentSong.coverImage
										: playlist.coverImage,
							};
						}
						return playlist;
					})
				);
			}
		}
		controlAudio("stop");

		// Get next song from queue
		const nextSong = songQueue[0];
		if (nextSong) {
			setCurrentSong(nextSong);
			setSongQueue((prev) => prev.slice(1));
			// Autoplay new song
			setTimeout(() => {
				controlAudio("play", { resetTime: true });
			}, 300);
		} else {
			// If queue is empty, get new recommendations
			setIsLoading(true);
			try {
				const newRecommendations = await getRecommendations(
					likedSongs.map((song) => song.id),
					20
				);
				if (newRecommendations && newRecommendations.length > 0) {
					setCurrentSong(newRecommendations[0]);
					setSongQueue(newRecommendations.slice(1));
					// Autoplay new song
					setTimeout(() => {
						controlAudio("play");
					}, 300);
				} else {
					setCurrentSong(null);
					setSongQueue([]);
				}
			} catch (error) {
				console.error("Error getting recommendations:", error);
			} finally {
				setIsLoading(false);
			}
		}

		// Reset card position after animation
		setTimeout(() => {
			card.classList.remove(`swiped-${direction}`);
			setCardTransform({ x: 0, y: 0, rotate: 0 });
		}, 300);
	};

	const handleDragStart = (e) => {
		setIsDragging(true);
		setDragStart({
			x: e.clientX - cardTransform.x,
			y: e.clientY - cardTransform.y,
		});
	};

	const handleDragMove = (e) => {
		if (!isDragging) return;

		const x = e.clientX - dragStart.x;
		const y = e.clientY - dragStart.y;
		const rotate = x * 0.1;

		setCardTransform({ x, y, rotate });
	};

	const handleDragEnd = () => {
		if (!isDragging) return;
		setIsDragging(false);

		const { x } = cardTransform;
		if (Math.abs(x) > 100) {
			handleSwipe(x > 0 ? "right" : "left");
		} else {
			setCardTransform({ x: 0, y: 0, rotate: 0 });
		}
	};

	const handlePlayPause = () => controlAudio("toggle");

	const handleProgressClick = (e) => {
		if (audioRef.current) {
			const progressBar = e.currentTarget;
			const rect = progressBar.getBoundingClientRect();
			const percentage = (e.clientX - rect.left) / rect.width;
			const seekTo = percentage * audioRef.current.duration;
			controlAudio("seek", { seekTo });
		}
	};

	if (isLoading) {
		return <SoundwaveLoader />;
	}

	if (!currentSong) {
		return <NoSongsScreen />;
	}

	return (
		<div className="home-container">
			{/* Sidebar Toggle */}
			<button
				className={`sidebar-toggle ${isSidebarCollapsed ? "collapsed" : ""}`}
				onClick={toggleSidebar}
			>
				{isSidebarCollapsed ? "☰" : "⬅"}
			</button>

			{/* Sidebar */}
			<Sidebar
				isLoadingSongs={isLoadingSongs}
				isSidebarCollapsed={isSidebarCollapsed}
				playlists={playlists} // Fallback to empty array
				activePlaylist={activePlaylist}
				playlistSongs={playlistSongs}
				handlePlaylistSelect={handlePlaylistSelect}
				handleDeleteClick={handleDeleteClick}
				openCreateModal={() => setShowCreateModal(true)}
				handleDeleteSong={handleDeleteSong}
				onRefresh={loadPlaylists}
			/>

			{/* Main content */}
			<MainContent
				isSwiping={isSwiping}
				isSidebarCollapsed={isSidebarCollapsed}
				currentSong={currentSong}
				isDragging={isDragging}
				cardTransform={cardTransform}
				activePlaylist={activePlaylist}
				playlists={playlists}
				progress={progress}
				currentTime={currentTime}
				duration={duration}
				isPlaying={isPlaying}
				handleStartSwiping={() => setIsSwiping(true)}
				handleDragStart={handleDragStart}
				handleDragMove={handleDragMove}
				handleDragEnd={handleDragEnd}
				handlePlayPause={handlePlayPause}
				handleProgressClick={handleProgressClick}
				handleSwipe={handleSwipe}
				cardRef={cardRef}
			/>

			{/* Exit button */}
			{isSwiping ? (
				<button className="exit-button" onClick={handleExitSwiping}>
					✕
				</button>
			) : (
				<button className="logout-button" onClick={handleLogout}>
					Logout
				</button>
			)}

			{/* Playlist Creation Modal */}
			{showCreateModal && (
				<CreatePlaylistModal
					isOpen={showCreateModal}
					onClose={() => setShowCreateModal(false)}
					onCreate={handleCreatePlaylist}
				/>
			)}

			{/* Delete Confirmation Modal */}
			<DeletePlaylistModal
				isOpen={!!playlistToDelete}
				onClose={() => setPlaylistToDelete(null)}
				onDelete={() => handleDeletePlaylist(playlistToDelete)}
				playlistName={
					playlists.find((p) => p.id === playlistToDelete)?.name || ""
				}
			/>

			<audio
				ref={audioRef}
				src={currentSong.previewUrl}
				onTimeUpdate={handleTimeUpdate}
				onLoadedMetadata={handleLoadedMetadata}
			/>
		</div>
	);
};

export default Home;
