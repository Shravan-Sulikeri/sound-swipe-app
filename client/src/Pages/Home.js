import React, { useState, useRef, useEffect } from "react";
import useAudioControls from "../hooks/useAudioControls";
import "../styling/home.css";
import Sidebar from "../components/Sidebar";
import MainContent from "../components/Main";
import CreatePlaylistModal from "../components/CreateModal";
import DeletePlaylistModal from "../components/DeleteModal";
import SoundwaveLoader from "../components/SoundwaveLoader";
import NoSongsScreen from "../components/NoSongs";
// import ChunkingProgress from "../components/ChunkingLoading";
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
	loadAllChunks,
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

	// Optimistic state tracking
	const [optimisticPlaylistData, setOptimisticPlaylistData] = useState({});

	const loadPlaylists = async () => {
		// First try to load from cache for instant display
		const cached = localStorage.getItem("cachedPlaylists");
		if (cached) {
			const parsedCache = JSON.parse(cached);
			setPlaylists(parsedCache);

			// Initialize optimistic data from cache
			const initialOptimisticData = {};
			parsedCache.forEach((playlist) => {
				initialOptimisticData[playlist.id] = {
					songCount: playlist.songCount,
					coverImage: playlist.coverImage,
					songs: playlist.songs || [],
				};
			});
			setOptimisticPlaylistData(initialOptimisticData);
		}

		// Then fetch fresh data in background
		try {
			const fresh = await getPlaylists();
			setPlaylists(fresh);
			// Update optimistic data with fresh data
			const freshOptimisticData = {};
			fresh.forEach((playlist) => {
				freshOptimisticData[playlist.id] = {
					songCount: playlist.songCount,
					coverImage: playlist.coverImage,
					songs: playlist.songs || [],
				};
			});
			setOptimisticPlaylistData(freshOptimisticData);

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

	// Initialize optimistic data when playlists change
	useEffect(() => {
		const optimisticData = {};
		playlists.forEach((playlist) => {
			// Only initialize if not already tracked
			if (!optimisticPlaylistData[playlist.id]) {
				optimisticData[playlist.id] = {
					songCount: playlist.songCount,
					coverImage: playlist.coverImage,
					songs: playlist.songs || [],
				};
			}
		});

		// Merge with existing data
		if (Object.keys(optimisticData).length > 0) {
			setOptimisticPlaylistData((prev) => ({ ...prev, ...optimisticData }));
		}
	}, [playlists]);

	// Helper function to get optimistic song count
	const getOptimisticSongCount = (playlistId) => {
		// If this is the active playlist, use the playlistSongs length
		if (activePlaylist === playlistId) {
			return playlistSongs.length;
		}

		// Otherwise use the tracking object or fall back to the playlist data
		return optimisticPlaylistData[playlistId]?.songCount !== undefined
			? optimisticPlaylistData[playlistId].songCount
			: playlists.find((p) => p.id === playlistId)?.songCount || 0;
	};

	// Helper function to get optimistic cover image
	const getOptimisticCoverImage = (playlistId) => {
		return optimisticPlaylistData[playlistId]?.coverImage !== undefined
			? optimisticPlaylistData[playlistId].coverImage
			: playlists.find((p) => p.id === playlistId)?.coverImage ||
					"https://via.placeholder.com/100";
	};

	// Update playlists with optimistic data for components
	const getOptimisticPlaylists = () => {
		return playlists.map((playlist) => ({
			...playlist,
			songCount: getOptimisticSongCount(playlist.id),
			coverImage: getOptimisticCoverImage(playlist.id),
		}));
	};

	// Create derived playlists with optimistic data
	const optimisticPlaylists = getOptimisticPlaylists();

	const handleLogout = () => {
		window.location.href = `${API_BASE_URL}/logout`;
	};

	const handleCreatePlaylist = async (playlistName) => {
		try {
			// Default cover image
			const defaultCoverImage =
				likedSongs[0]?.coverImage || "https://via.placeholder.com/100";

			// Create an optimistic playlist ID (temporary)
			const temporaryId = `temp-${Date.now()}`;

			// Add optimistic playlist to UI immediately
			const optimisticPlaylist = {
				id: temporaryId,
				name: playlistName,
				songs: [],
				songCount: 0,
				coverImage: defaultCoverImage,
			};

			setPlaylists((prev) => [...prev, optimisticPlaylist]);
			setActivePlaylist(temporaryId);
			setOptimisticPlaylistData((prev) => ({
				...prev,
				[temporaryId]: {
					songCount: 0,
					coverImage: defaultCoverImage,
					songs: [],
				},
			}));

			// Actually create the playlist in the database
			const playlistData = await createPlaylist(playlistName);

			if (!playlistData?.id) {
				throw new Error("Failed to create playlist - no ID returned");
			}

			// Replace temporary playlist with real one from server
			setPlaylists((prev) =>
				prev.map((p) =>
					p.id === temporaryId
						? {
								...p,
								id: playlistData.id,
						  }
						: p
				)
			);

			// Update active playlist reference
			setActivePlaylist(playlistData.id);

			// Update optimistic data
			setOptimisticPlaylistData((prev) => {
				const newData = { ...prev };
				// Transfer data from temp ID to real ID
				newData[playlistData.id] = newData[temporaryId];
				// Remove temp ID
				delete newData[temporaryId];
				return newData;
			});

			setShowCreateModal(false);

			// Simple success feedback
			console.log("Playlist created successfully:", playlistData);
		} catch (error) {
			console.error("Playlist creation error:", error);

			// Remove optimistic playlist on error
			const temporaryId = `temp-${Date.now()}`;
			setPlaylists((prev) => prev.filter((p) => p.id !== temporaryId));
			setActivePlaylist(null);

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

			// First set optimistic songs if we have them cached
			if (optimisticPlaylistData[playlistId]?.songs?.length > 0) {
				setPlaylistSongs(optimisticPlaylistData[playlistId].songs);
			}

			// Then fetch from server
			const songs = await getSongsFromPlaylist(playlistId);
			setPlaylistSongs(songs);

			// Update optimistic data with actual value
			setOptimisticPlaylistData((prev) => ({
				...prev,
				[playlistId]: {
					...prev[playlistId],
					songCount: songs.length,
					songs: songs,
				},
			}));
		} catch (error) {
			console.error("Error handling playlist selection:", error);
		} finally {
			setIsLoadingSongs(false);
		}
	};

	const handleDeleteClick = async (e, playlistId) => {
		e.stopPropagation(); // Prevent playlist selection when clicking delete
		setPlaylistToDelete(playlistId);
	};

	const handleDeletePlaylist = async (playlistId) => {
		// Optimistically remove from UI first
		const playlistToRemove = playlists.find((p) => p.id === playlistId);

		setPlaylists((prev) => prev.filter((p) => p.id !== playlistId));
		if (activePlaylist === playlistId) {
			setActivePlaylist(null);
			setPlaylistSongs([]);
		}

		try {
			await deletePlaylist(playlistId);

			// Remove from optimistic data
			setOptimisticPlaylistData((prev) => {
				const newData = { ...prev };
				delete newData[playlistId];
				return newData;
			});

			console.log(`Playlist ${playlistToDelete} deleted successfully`);
		} catch (error) {
			console.error("Deletion failed:", error);

			// Restore the playlist if deletion fails
			if (playlistToRemove) {
				setPlaylists((prev) => [...prev, playlistToRemove]);
				setOptimisticPlaylistData((prev) => ({
					...prev,
					[playlistId]: {
						songCount: playlistToRemove.songCount,
						coverImage: playlistToRemove.coverImage,
						songs: playlistToRemove.songs || [],
					},
				}));
			}
		}
	};

	const handleDeleteSong = async (playlistId, songIndex) => {
		// Find the song to remove from local state
		if (!playlistSongs?.[songIndex]) {
			console.warn("No song found at index:", songIndex);
			return;
		}

		const songToRemove = playlistSongs[songIndex];

		// Check if we have the Spotify URI
		if (!songToRemove.uri) {
			console.error("Song missing Spotify URI:", songToRemove);
			return;
		}

		// Optimistically update the UI immediately
		const updatedSongs = [
			...playlistSongs.slice(0, songIndex),
			...playlistSongs.slice(songIndex + 1),
		];

		setPlaylistSongs(updatedSongs);

		// Update optimistic data
		setOptimisticPlaylistData((prev) => {
			const currentData = prev[playlistId] || {};
			const newCount = Math.max(0, (currentData.songCount || 0) - 1);

			// Determine new cover image - if we removed the first song and there are other songs,
			// use the new first song's cover image
			let newCoverImage = currentData.coverImage;
			if (songIndex === 0 && updatedSongs.length > 0) {
				newCoverImage = updatedSongs[0].coverImage;
			}

			return {
				...prev,
				[playlistId]: {
					...currentData,
					songCount: newCount,
					coverImage: newCoverImage,
					songs: updatedSongs,
				},
			};
		});

		try {
			// Call API to remove the track using the URI we already have
			const result = await removeTrack(songToRemove.uri, playlistId);

			if (!result.success) {
				throw new Error(result.error || "Failed to remove track");
			}

			console.log(
				`Track ${songToRemove.name} removed from playlist successfully`
			);
		} catch (error) {
			console.error("Error removing track from playlist:", error);

			// Rollback optimistic update on error
			setPlaylistSongs((prev) => [
				...prev.slice(0, songIndex),
				songToRemove,
				...prev.slice(songIndex),
			]);

			// Restore optimistic data
			setOptimisticPlaylistData((prev) => {
				const currentData = prev[playlistId] || {};
				return {
					...prev,
					[playlistId]: {
						...currentData,
						songCount: (currentData.songCount || 0) + 1,
						songs: [
							...playlistSongs.slice(0, songIndex),
							songToRemove,
							...playlistSongs.slice(songIndex),
						],
					},
				};
			});
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
				// Keep track of the current song for rollback if needed
				const songToAdd = currentSong;

				// Optimistically update song list
				const updatedSongs = [...playlistSongs, songToAdd];
				setPlaylistSongs(updatedSongs);

				// Optimistically update data - cover image only changes if this is the first song
				setOptimisticPlaylistData((prev) => {
					const currentData = prev[activePlaylist] || {};
					const newCount = (currentData.songCount || 0) + 1;
					const isFirstSong = newCount === 1;

					return {
						...prev,
						[activePlaylist]: {
							...currentData,
							songCount: newCount,
							// Only update cover image if this is the first song
							coverImage: isFirstSong
								? songToAdd.coverImage
								: currentData.coverImage,
							songs: updatedSongs,
						},
					};
				});

				try {
					// Extract artist name
					const artistName = Array.isArray(currentSong.artists)
						? currentSong.artists[0]
						: currentSong.artists;

					// Search for track in Spotify
					const searchResult = await searchSpotifyTrack(
						currentSong.name,
						artistName
					);

					if (!searchResult.success) {
						throw new Error(
							`Could not find ${currentSong.name} by ${artistName} on Spotify`
						);
					}

					// Use the track URI for adding to playlist
					const trackUri = searchResult.uri;

					// Call the API to add the track to the playlist
					const result = await addTrack(trackUri, activePlaylist);
					if (!result.success) {
						throw new Error(result.error || "Failed to add track to playlist");
					}

					console.log(
						`Track ${currentSong.name} added to playlist successfully`
					);
				} catch (error) {
					console.error("Error adding track to playlist:", error);

					// Rollback optimistic updates on failure
					setPlaylistSongs((prev) => prev.filter((song) => song !== songToAdd));

					setOptimisticPlaylistData((prev) => {
						const currentData = prev[activePlaylist] || {};
						const newCount = Math.max(0, (currentData.songCount || 0) - 1);

						// Determine if we need to rollback the cover image
						let coverImage = currentData.coverImage;
						if (newCount === 0) {
							coverImage = "https://via.placeholder.com/100"; // Default image when empty
						}

						return {
							...prev,
							[activePlaylist]: {
								...currentData,
								songCount: newCount,
								coverImage: coverImage,
								songs: playlistSongs.filter((song) => song !== songToAdd),
							},
						};
					});
				}
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
				{isSidebarCollapsed ? "☰" : "←"}
			</button>

			{/* Sidebar - Now using playlists with optimistic data */}
			<Sidebar
				isLoadingSongs={isLoadingSongs}
				isSidebarCollapsed={isSidebarCollapsed}
				playlists={optimisticPlaylists}
				activePlaylist={activePlaylist}
				playlistSongs={playlistSongs}
				handlePlaylistSelect={handlePlaylistSelect}
				handleDeleteClick={handleDeleteClick}
				openCreateModal={() => setShowCreateModal(true)}
				handleDeleteSong={handleDeleteSong}
				onRefresh={loadPlaylists}
			/>
	<div className="main-content">
  <div className="card-and-nextup">

    {/* Swipe Card */}
    <MainContent
      isSwiping={isSwiping}
      isSidebarCollapsed={isSidebarCollapsed}
      currentSong={currentSong}
      isDragging={isDragging}
      cardTransform={cardTransform}
      activePlaylist={activePlaylist}
      playlists={optimisticPlaylists}
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

    {/* Next Up */}
    {isSwiping && songQueue.length > 0 && (
      <div className="next-song-preview-side">
        <h4>Next Up</h4>
        <div className="mini-song-side">
          <img
            src={songQueue[0].coverImage || "https://via.placeholder.com/80"}
            alt={songQueue[0].name}
          />
          <p>{songQueue[0].name}</p>
        </div>
      </div>
    )}

  </div>
</div>

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
					optimisticPlaylists.find((p) => p.id === playlistToDelete)?.name || ""
				}
			/>

			<audio
				ref={audioRef}
				src={currentSong.previewUrl}
				onTimeUpdate={handleTimeUpdate}
				onLoadedMetadata={handleLoadedMetadata}
			/>

			{/* <ChunkingProgress
				isLoading={chunkingProgress.isLoading}
				progress={chunkingProgress.progress}
				totalLoaded={chunkingProgress.totalLoaded}
				totalProcessed={chunkingProgress.totalProcessed}
			/> */}
		</div>
	);
};

export default Home;
