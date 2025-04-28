import React, { useState, useRef, useEffect, useCallback } from "react";
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
	useStreamedRecommendations,
} from "../services/api";

const Home = () => {
	const [isSwiping, setIsSwiping] = useState(false);
	const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
	const [playlists, setPlaylists] = useState([]);
	const [likedSongs, setLikedSongs] = useState([]);
	const [isDragging, setIsDragging] = useState(false);
	const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
	const [cardTransform, setCardTransform] = useState({ x: 0, y: 0, rotate: 0 });
	const [isLoading, setIsLoading] = useState(false);

	// Enhanced song queue implementation
	const [processedSongIds, setProcessedSongIds] = useState(new Set()); // Track songs we've already shown
	const [songQueue, setSongQueue] = useState([]); // Keep as array for simplicity
	const [currentSong, setCurrentSong] = useState(null);
	
	// Enhanced batch tracking
	const [batchRegistry, setBatchRegistry] = useState({}); // Track which songs belong to which batch
	const [currentBatchId, setCurrentBatchId] = useState(null); // Track which batch we're currently processing
	const [songPosition, setSongPosition] = useState({ batch: null, position: 0, total: 0 }); // Track position within batch

	// Modal states
	const [showCreateModal, setShowCreateModal] = useState(false);
	const [activePlaylist, setActivePlaylist] = useState(null);
	const [isLoadingSongs, setIsLoadingSongs] = useState(false);

	// Delete confirmation modal
	const [playlistToDelete, setPlaylistToDelete] = useState(null);

	const audioRef = useRef(null);
	const cardRef = useRef(null);

	// Use the streamed recommendations hook
	const { tracks: streamedTracks, error: streamError, isLoading: isStreamLoading } = useStreamedRecommendations();

	// Process new tracks arriving from stream
	// This focuses on the key part that needs fixing
	// Process new tracks arriving from stream
	// Process new tracks arriving from stream
useEffect(() => {
  if (streamedTracks.length > 0) {
    console.log(`[Home] Received ${streamedTracks.length} new tracks`);
    
    // Create a batch ID to track this group of songs
    const batchId = `batch-${Date.now()}`;
    
    // Create a set of all song IDs we need to exclude:
    // 1. Already processed songs
    // 2. Current song (if any)
    // 3. Songs already in the queue
    const excludedSongIds = new Set(processedSongIds);
    
    // Add current song ID to excluded set if it exists
    if (currentSong?.id) {
      excludedSongIds.add(currentSong.id);
    }
    
    // Add all queue song IDs to excluded set
    songQueue.forEach(queuedSong => {
      if (queuedSong?.id) {
        excludedSongIds.add(queuedSong.id);
      }
    });
    
    // Filter out any songs we've already processed or queued (by Spotify ID)
    const newSongs = streamedTracks.filter(track => 
      track.id && !excludedSongIds.has(track.id)
    );
    
    // Skip if no new songs after filtering
    if (newSongs.length === 0) {
      console.log("[Home] No new unique tracks after filtering");
      return;
    }
    
    console.log(`[Home] ${newSongs.length} new unique tracks after filtering`);
    
    // Register this batch with ONLY the new songs
    setBatchRegistry(prev => ({
      ...prev,
      [batchId]: {
        timestamp: Date.now(),
        songIds: newSongs.map(song => song.id),
        totalSongs: newSongs.length,
        processed: 0,
        songs: newSongs // Store the actual songs in the batch
      }
    }));
    
    // If we don't have a current song, set it from the new batch
    if (!currentSong && newSongs.length > 0) {
      console.log("[Home] Setting first song from new batch");
      setCurrentSong(newSongs[0]);
      setCurrentBatchId(batchId);
      setSongPosition({ batch: batchId, position: 1, total: newSongs.length });
      
      // Mark this song as processed
      setProcessedSongIds(prev => {
        const newSet = new Set(prev);
        newSet.add(newSongs[0].id);
        return newSet;
      });
      
      // Add the rest to the queue
      if (newSongs.length > 1) {
        setSongQueue(prev => [...prev, ...newSongs.slice(1)]);
      }
      
      // Update batch processed count
      setBatchRegistry(prev => ({
        ...prev,
        [batchId]: {
          ...prev[batchId],
          processed: 1
        }
      }));
      
      // Handle artists display safely, checking if it's an array
      const artistInfo = Array.isArray(newSongs[0].artists) 
        ? newSongs[0].artists.join(', ') 
        : typeof newSongs[0].artists === 'string' 
          ? newSongs[0].artists 
          : 'Unknown Artist';
          
      // Log current song position
      console.log(`[Song Position] Now playing song 1/${newSongs.length} from batch ${batchId}`);
      console.log(`[Song Info] "${newSongs[0].name}" by ${artistInfo}`);
    } else if (newSongs.length > 0) {
      // Just add all new songs to the queue
      setSongQueue(prev => [...prev, ...newSongs]);
    }
  }
}, [currentSong, processedSongIds, songQueue, streamedTracks]);
	// Handle stream errors
	useEffect(() => {
		if (streamError) {
			console.error("Error in recommendation stream:", streamError);
		}
	}, [streamError]);

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
			parsedCache.forEach(playlist => {
				initialOptimisticData[playlist.id] = {
					songCount: playlist.songCount,
					coverImage: playlist.coverImage,
					songs: playlist.songs || []
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
			fresh.forEach(playlist => {
				freshOptimisticData[playlist.id] = {
					songCount: playlist.songCount,
					coverImage: playlist.coverImage,
					songs: playlist.songs || []
				};
			});
			setOptimisticPlaylistData(freshOptimisticData);
			
			localStorage.setItem("cachedPlaylists", JSON.stringify(fresh));
		} catch (error) {
			console.error("Playlist refresh failed:", error);
		}
	};

	useEffect(() => {
		const initializeData = async () => {
			setIsLoading(true);
			try {
				await loadPlaylists();
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
		playlists.forEach(playlist => {
			// Only initialize if not already tracked
			if (!optimisticPlaylistData[playlist.id]) {
				optimisticData[playlist.id] = {
					songCount: playlist.songCount,
					coverImage: playlist.coverImage,
					songs: playlist.songs || []
				};
			}
		});
		
		// Merge with existing data
		if (Object.keys(optimisticData).length > 0) {
			setOptimisticPlaylistData(prev => ({...prev, ...optimisticData}));
		}
	}, [optimisticPlaylistData, playlists]);

	// Helper function to get optimistic song count
	const getOptimisticSongCount = (playlistId) => {
		// If this is the active playlist, use the playlistSongs length
		if (activePlaylist === playlistId) {
			return playlistSongs.length;
		}
		
		// Otherwise use the tracking object or fall back to the playlist data
		return optimisticPlaylistData[playlistId]?.songCount !== undefined 
			? optimisticPlaylistData[playlistId].songCount 
			: playlists.find(p => p.id === playlistId)?.songCount || 0;
	};

	// Helper function to get optimistic cover image
	const getOptimisticCoverImage = (playlistId) => {
		return optimisticPlaylistData[playlistId]?.coverImage !== undefined 
			? optimisticPlaylistData[playlistId].coverImage 
			: playlists.find(p => p.id === playlistId)?.coverImage || "https://via.placeholder.com/100";
	};

	// Update playlists with optimistic data for components
	const getOptimisticPlaylists = () => {
		return playlists.map(playlist => ({
			...playlist,
			songCount: getOptimisticSongCount(playlist.id),
			coverImage: getOptimisticCoverImage(playlist.id)
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
			const defaultCoverImage = likedSongs[0]?.coverImage || "https://via.placeholder.com/100";
			
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
			
			setPlaylists(prev => [...prev, optimisticPlaylist]);
			setActivePlaylist(temporaryId);
			setOptimisticPlaylistData(prev => ({
				...prev,
				[temporaryId]: {
					songCount: 0,
					coverImage: defaultCoverImage,
					songs: []
				}
			}));
			
			// Actually create the playlist in the database
			const playlistData = await createPlaylist(playlistName);

			if (!playlistData?.id) {
				throw new Error("Failed to create playlist - no ID returned");
			}

			// Replace temporary playlist with real one from server
			setPlaylists(prev => 
				prev.map(p => p.id === temporaryId ? 
					{
						...p,
						id: playlistData.id
					} : p
				)
			);
			
			// Update active playlist reference
			setActivePlaylist(playlistData.id);
			
			// Update optimistic data
			setOptimisticPlaylistData(prev => {
				const newData = {...prev};
				// Transfer data from temp ID to real ID
				newData[playlistData.id] = newData[temporaryId];
				// Remove temp ID
				delete newData[temporaryId];
				return newData;
			});

			setShowCreateModal(false);
			console.log("Playlist created successfully:", playlistData);
		} catch (error) {
			console.error("Playlist creation error:", error);

			// Remove optimistic playlist on error
			const temporaryId = `temp-${Date.now()}`;
			setPlaylists(prev => prev.filter(p => p.id !== temporaryId));
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
			setOptimisticPlaylistData(prev => ({
				...prev,
				[playlistId]: {
					...prev[playlistId],
					songCount: songs.length,
					songs: songs
				}
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
		const playlistToRemove = playlists.find(p => p.id === playlistId);
		
		setPlaylists(prev => prev.filter(p => p.id !== playlistId));
		if (activePlaylist === playlistId) {
			setActivePlaylist(null);
			setPlaylistSongs([]);
		}
		
		try {
			await deletePlaylist(playlistId);
			
			// Remove from optimistic data
			setOptimisticPlaylistData(prev => {
				const newData = {...prev};
				delete newData[playlistId];
				return newData;
			});
			
			console.log(`Playlist ${playlistToDelete} deleted successfully`);
		} catch (error) {
			console.error("Deletion failed:", error);
			
			// Restore the playlist if deletion fails
			if (playlistToRemove) {
				setPlaylists(prev => [...prev, playlistToRemove]);
				setOptimisticPlaylistData(prev => ({
					...prev,
					[playlistId]: {
						songCount: playlistToRemove.songCount,
						coverImage: playlistToRemove.coverImage,
						songs: playlistToRemove.songs || []
					}
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
		setOptimisticPlaylistData(prev => {
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
					songs: updatedSongs
				}
			};
		});

		try {
			// Call API to remove the track using the URI we already have
			const result = await removeTrack(songToRemove.uri, playlistId);

			if (!result.success) {
				throw new Error(result.error || "Failed to remove track");
			}
			
			console.log(`Track ${songToRemove.name} removed from playlist successfully`);
		} catch (error) {
			console.error("Error removing track from playlist:", error);
			
			// Rollback optimistic update on error
			setPlaylistSongs(prev => [
				...prev.slice(0, songIndex),
				songToRemove,
				...prev.slice(songIndex)
			]);
			
			// Restore optimistic data
			setOptimisticPlaylistData(prev => {
				const currentData = prev[playlistId] || {};
				return {
					...prev,
					[playlistId]: {
						...currentData,
						songCount: (currentData.songCount || 0) + 1,
						songs: [
							...playlistSongs.slice(0, songIndex),
							songToRemove,
							...playlistSongs.slice(songIndex)
						]
					}
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

	// Debug function to check queue state
	// eslint-disable-next-line react-hooks/exhaustive-deps
	const debugQueueState = useCallback(() => {
		console.log(`Current song: ${currentSong?.name || 'None'}`);
		console.log(`Queue length: ${songQueue.length}`);
		console.log(`Processed songs: ${processedSongIds.size}`);
		console.log(`Current batch ID: ${currentBatchId}`);
		console.log(`Current song position: ${songPosition.position}/${songPosition.total} in batch ${songPosition.batch}`);
		console.log(`Batch registry:`, batchRegistry);
		
		// Check if we need to request more songs
		if (songQueue.length < 3) {
			console.log("[Debug] Queue running low, consider fetching more songs");
		}
		
		// Check if the current batch is nearly complete
		if (currentBatchId && batchRegistry[currentBatchId]) {
			const currentBatch = batchRegistry[currentBatchId];
			const remaining = currentBatch.totalSongs - currentBatch.processed;
			console.log(`[Debug] Current batch has ${remaining} songs remaining`);
		}
	});

	// Helper function to log current song info
	// eslint-disable-next-line react-hooks/exhaustive-deps
	const logSongInfo = useCallback((song, action) => {
		if (!song) return;
		
		const artistInfo = Array.isArray(song.artists) 
			? song.artists.join(', ') 
			: song.artists;
			
		console.log(`[Song ${action}] "${song.name}" by ${artistInfo}`);
		
		if (currentBatchId && batchRegistry[currentBatchId]) {
			console.log(`[Song Position] ${songPosition.position}/${songPosition.total} in batch ${songPosition.batch}`);
		}
	});

	// Enhanced swipe handler with song tracking and batch management
		const handleSwipe = async (direction) => {
	const card = cardRef.current;
	if (!card || !currentSong) return;

	card.classList.add(`swiped-${direction}`);
	
	// Log current song action
	logSongInfo(currentSong, direction === "right" ? "LIKED" : "SKIPPED");
	
	// If we have a current batch, update its processed count
	if (currentBatchId && batchRegistry[currentBatchId]) {
		setBatchRegistry(prev => {
		const updatedRegistry = {...prev};
		updatedRegistry[currentBatchId] = {
			...updatedRegistry[currentBatchId],
			processed: updatedRegistry[currentBatchId].processed + 1
		};
		
		return updatedRegistry;
		});
	}
	
	// Mark current song as processed
	if (currentSong.id) {
		setProcessedSongIds(prev => {
		const newSet = new Set(prev);
		newSet.add(currentSong.id);
		return newSet;
		});
	}
	
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

	// Move to next song in the queue
	if (songQueue.length > 0) {
		console.log("[Home] Moving to next song");
		const nextSong = songQueue[0];
		setCurrentSong(nextSong);
		setSongQueue((prev) => prev.slice(1));
		
		// Find which batch this next song belongs to
		let foundBatchId = null;
		let nextPosition = 1;
		let totalSongs = 0;
		
		// Search through all batches to find which one contains this song
		Object.entries(batchRegistry).forEach(([bid, batchData]) => {
		if (batchData.songIds.includes(nextSong.id)) {
			foundBatchId = bid;
			// Calculate position in batch (add 1 because arrays are 0-indexed)
			const batchSongIndex = batchData.songIds.indexOf(nextSong.id);
			nextPosition = batchSongIndex + 1;
			totalSongs = batchData.totalSongs;
		}
		});
		
		if (foundBatchId) {
		setCurrentBatchId(foundBatchId);
		setSongPosition({
			batch: foundBatchId,
			position: nextPosition,
			total: totalSongs
		});
		
		console.log(`[Home] Song belongs to batch: ${foundBatchId}`);
		console.log(`[Song Position] Now playing song ${nextPosition}/${totalSongs} from batch ${foundBatchId}`);
		} else {
		console.warn("[Home] Could not determine batch for next song");
		// If we can't determine the batch, just use the existing batch info
		// This is a fallback in case something goes wrong
		setSongPosition(prev => ({
			...prev,
			position: prev.position + 1
		}));
		}
		
		// Log the next song info
		setTimeout(() => {
		logSongInfo(nextSong, "NOW PLAYING");
		}, 300);
		
		// Autoplay new song
		setTimeout(() => {
		controlAudio("play", { resetTime: true });
		}, 300);
	} else {
		console.log("[Home] Queue is empty, waiting for new tracks");
		setCurrentSong(null);
		setCurrentBatchId(null);
		setSongPosition({ batch: null, position: 0, total: 0 });
		
		// Debug when we run out of songs
		setTimeout(() => {
		debugQueueState();
		}, 0);
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

	// Monitor queue length and trigger debugging when it runs low
	useEffect(() => {
		if (songQueue.length <= 2) {
			console.log("[Home] Queue running low, debugging state");
			debugQueueState();
		}
	}, [debugQueueState, songQueue.length]);

	// Log current song when it changes
	useEffect(() => {
		if (currentSong) {
			logSongInfo(currentSong, "CURRENT");
		}
	}, [currentSong, logSongInfo]);

	if (isStreamLoading) {
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

			{/* Sidebar */}
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

			{/* Main content */}
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
				src={currentSong?.previewUrl}
				onTimeUpdate={handleTimeUpdate}
				onLoadedMetadata={handleLoadedMetadata}
			/>
		</div>
	);
};

export default Home;