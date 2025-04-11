import React, { useState, useRef, useEffect } from "react";
import useAudioControls from "../hooks/useAudioControls";
import "../styling/home.css";
import Sidebar from "../components/Sidebar";
import MainContent from "../components/Main";
import CreatePlaylistModal from "../components/CreateModal";
import DeletePlaylistModal from "../components/DeleteModal";
import {
	getSampleTracks,
	getRecommendations,
	getSongsFromPlaylist,
	API_BASE_URL,
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

	const [selectedPlaylistId, setSelectedPlaylistId] = useState(null);
	const [playlistSongs, setPlaylistSongs] = useState([]);

	const handlePlaylistClick = async (playlist) => {
		setSelectedPlaylistId(playlist.id);
		const songs = await getSongsFromPlaylist(playlist.id);
		setPlaylistSongs(songs.data || []);
	};

	// Initialize songs when component mounts
	useEffect(() => {
		const initializeSongs = async () => {
			setIsLoading(true);
			try {
				const initialSongs = await getSampleTracks(20);
				if (initialSongs && initialSongs.length > 0) {
					setCurrentSong(initialSongs[0]);
					setSongQueue(initialSongs.slice(1));
				} else {
					console.error("No songs received from the API");
				}
			} catch (error) {
				console.error("Error loading initial songs:", error);
			} finally {
				setIsLoading(false);
			}
		};
		initializeSongs();
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

	const handlePlaylistSelect = (playlistId) => {
		if (activePlaylist === playlistId) {
			setActivePlaylist(null);
		} else {
			setActivePlaylist(playlistId);
			// find playlist
			const selected = playlists.find((p) => p.id === playlistId);
			//get songs from playlist and set playlist songs
			setPlaylistSongs(selected?.songs || []);
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
		// Find the song to remove
		const playlist = playlists.find((p) => p.id === playlistId);
		if (!playlist || !playlist.songs[songIndex]) return;

		const songToRemove = playlist.songs[songIndex];

		try {
			// Extract artist name
			const artistName = Array.isArray(songToRemove.artists)
				? songToRemove.artists[0]
				: songToRemove.artists;

			// Search for track in Spotify
			const searchResult = await searchSpotifyTrack(
				songToRemove.name,
				artistName
			);

			if (searchResult.success) {
				// Call API to remove the track using the URI
				const result = await removeTrack(searchResult.uri, playlistId);
				if (result.success) {
					console.log(
						`Track ${songToRemove.name} removed from playlist successfully`
					);
				} else {
					console.error("Failed to remove track from playlist:", result.error);
				}
			} else {
				console.warn(
					`Could not find ${songToRemove.name} by ${artistName} on Spotify for removal`
				);
			}
		} catch (error) {
			console.error("Error removing track from playlist:", error);
		}

		// Update UI regardless of API success
		setPlaylists((prevPlaylists) =>
			prevPlaylists.map((playlist) => {
				if (playlist.id === playlistId) {
					const updatedSongs = [...playlist.songs];
					updatedSongs.splice(songIndex, 1);
					return {
						...playlist,
						songs: updatedSongs,
						songCount: updatedSongs.length,
						coverImage:
							updatedSongs.length > 0
								? updatedSongs[0].coverImage
								: "https://via.placeholder.com/100",
					};
				}
				return playlist;
			})
		);
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
		return (
			<div className="home-container">
				<div className="welcome-section">
					<h1>Loading...</h1>
					<p>Getting your next song ready...</p>
				</div>
			</div>
		);
	}

	if (!currentSong) {
		return (
			<div className="home-container">
				<div className="welcome-section">
					<h1>No more songs to swipe!</h1>
					<p>Try refreshing or starting over.</p>
				</div>
			</div>
		);
	}

	return (
		<div className="home-container">
			{/* Sidebar Toggle */}
			<button
				className={`sidebar-toggle ${isSidebarCollapsed ? "collapsed" : ""}`}
				onClick={toggleSidebar}
			>
				{isSidebarCollapsed ? "☰" : "←"}
			</button>

			{/* Sidebar */}
			<Sidebar
				isSidebarCollapsed={isSidebarCollapsed}
				playlists={playlists} // Fallback to empty array
				activePlaylist={activePlaylist}
				handlePlaylistSelect={handlePlaylistSelect}
				handleDeleteClick={handleDeleteClick}
				openCreateModal={() => setShowCreateModal(true)}
				handleDeleteSong={handleDeleteSong}
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
