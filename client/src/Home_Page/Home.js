import React, { useState, useRef, useEffect } from "react";
import Modal from "../components/common/Modal";
import "../styling/home.css";
import Sidebar from "./components/Sidebar";
import MainContent from "./components/Main";
import { getSampleTracks, getRecommendations } from "../services/api";

import { getSongsFromPlaylist } from "../services/api";

const Home = () => {
	const [isSwiping, setIsSwiping] = useState(false);
	const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
	const [playlists, setPlaylists] = useState([]);
	const [currentSong, setCurrentSong] = useState(null);
	const [songQueue, setSongQueue] = useState([]);
	const [likedSongs, setLikedSongs] = useState([]);
	const [isPlaying, setIsPlaying] = useState(false);
	const [progress, setProgress] = useState(0);
	const [currentTime, setCurrentTime] = useState(0);
	const [duration, setDuration] = useState(0);
	const [isDragging, setIsDragging] = useState(false);
	const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
	const [cardTransform, setCardTransform] = useState({ x: 0, y: 0, rotate: 0 });
	const [isLoading, setIsLoading] = useState(false);

	// Modal states
	const [showCreateModal, setShowCreateModal] = useState(false);
	const [newPlaylistName, setNewPlaylistName] = useState("");
	const [activePlaylist, setActivePlaylist] = useState(null);

	// Delete confirmation modal
	const [showDeleteModal, setShowDeleteModal] = useState(false);
	const [playlistToDelete, setPlaylistToDelete] = useState(null);

	const audioRef = useRef(null);
	const cardRef = useRef(null);
	const createModalRef = useRef(null);
	const deleteModalRef = useRef(null);

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
		window.location.href = "http://localhost:3001/logout";
	};

	const handleOpenModal = () => {
		setShowCreateModal(true);
	};

	const handleCloseModal = () => {
		setShowCreateModal(false);
		setNewPlaylistName("");
	};

	const handleCreatePlaylist = () => {
		if (newPlaylistName.trim() === "") return;

		const newPlaylist = {
			id: Date.now().toString(),
			name: newPlaylistName,
			songs: [],
			songCount: 0,
			coverImage:
				likedSongs.length > 0
					? likedSongs[0].coverImage
					: "https://via.placeholder.com/100",
		};

		setPlaylists([...playlists, newPlaylist]);
		setActivePlaylist(newPlaylist.id);
		setNewPlaylistName("");
		setShowCreateModal(false);
	};

	const handlePlaylistSelect = (playlistId) => {
		if (activePlaylist === playlistId) {
			setActivePlaylist(null);
		} else {
			setActivePlaylist(playlistId);
			const selected = playlists.find((p) => p.id === playlistId);
			setPlaylistSongs(selected?.songs || []);
		}
	};

	const handleDeleteClick = (e, playlistId) => {
		e.stopPropagation(); // Prevent playlist selection when clicking delete
		setPlaylistToDelete(playlistId);
		setShowDeleteModal(true);
	};
	const handleDeleteSong = (playlistId, songIndex) => {
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

	const handleConfirmDelete = () => {
		// If deleting the active playlist, clear the active state
		if (playlistToDelete === activePlaylist) {
			setActivePlaylist(null);
		}

		// Remove the playlist
		setPlaylists(
			playlists.filter((playlist) => playlist.id !== playlistToDelete)
		);
		setShowDeleteModal(false);
		setPlaylistToDelete(null);
	};

	const handleCancelDelete = () => {
		setShowDeleteModal(false);
		setPlaylistToDelete(null);
	};

	const handleStartSwiping = () => {
		setIsSwiping(true);
	};

	const handleExitSwiping = () => {
		setIsSwiping(false);
		if (audioRef.current) {
			audioRef.current.pause();
			setIsPlaying(false);
		}
	};

	const toggleSidebar = () => {
		setIsSidebarCollapsed(!isSidebarCollapsed);
	};

	const handleSwipe = async (direction) => {
		const card = cardRef.current;
		if (!card || !currentSong) return;

		card.classList.add(`swiped-${direction}`);

		if (direction === "right") {
			// Add to liked songs
			setLikedSongs((prev) => [...prev, currentSong]);

			// Add to active playlist if one is selected
			if (activePlaylist) {
				setPlaylists((prevPlaylists) =>
					prevPlaylists.map((playlist) => {
						if (playlist.id === activePlaylist) {
							const updatedSongs = [...playlist.songs, currentSong];
							return {
								...playlist,
								songs: updatedSongs,
								songCount: updatedSongs.length,
								// Update cover image to the first song's image if this is the first song
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

		// Reset audio
		if (audioRef.current) {
			audioRef.current.pause();
			audioRef.current.currentTime = 0;
			setIsPlaying(false);
		}

		// Get next song from queue
		const nextSong = songQueue[0];
		if (nextSong) {
			setCurrentSong(nextSong);
			setSongQueue((prev) => prev.slice(1));
			// Autoplay new song
			setTimeout(() => {
				if (audioRef.current) {
					audioRef.current.play();
					setIsPlaying(true);
				}
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
						if (audioRef.current) {
							audioRef.current.play();
							setIsPlaying(true);
						}
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

	const handlePlayPause = () => {
		if (audioRef.current) {
			if (isPlaying) {
				audioRef.current.pause();
			} else {
				audioRef.current.play();
			}
			setIsPlaying(!isPlaying);
		}
	};

	const handleTimeUpdate = () => {
		if (audioRef.current) {
			const currentTime = audioRef.current.currentTime;
			setCurrentTime(currentTime);
			setProgress((currentTime / audioRef.current.duration) * 100);
		}
	};

	const handleLoadedMetadata = () => {
		if (audioRef.current) {
			setDuration(audioRef.current.duration);
		}
	};

	const handleProgressClick = (e) => {
		if (audioRef.current) {
			const progressBar = e.currentTarget;
			const rect = progressBar.getBoundingClientRect();
			const x = e.clientX - rect.left;
			const percentage = x / rect.width;
			audioRef.current.currentTime = percentage * audioRef.current.duration;
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
				handleOpenModal={handleOpenModal}
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
				handleStartSwiping={handleStartSwiping}
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
				<Modal
					isOpen={createModalRef}
					onClose={handleCloseModal}
					className="playlist-modal"
				>
					<div className="modal-header">
						<h3>Create New Playlist</h3>
						<button className="close-modal" onClick={handleCloseModal}>
							✕
						</button>
					</div>
					<div className="modal-content">
						<p>
							Give your playlist a name. Songs you swipe right on will be added
							to this playlist.
						</p>
						<input
							type="text"
							className="playlist-name-input"
							placeholder="e.g Workout Playlist"
							value={newPlaylistName}
							onChange={(e) => setNewPlaylistName(e.target.value)}
							autoFocus
						/>
					</div>
					<div className="modal-footer">
						<button className="cancel-btn" onClick={handleCloseModal}>
							Cancel
						</button>
						<button
							className="create-btn"
							onClick={handleCreatePlaylist}
							disabled={newPlaylistName.trim() === ""}
						>
							Create Playlist
						</button>
					</div>
				</Modal>
			)}

			{/* Delete Confirmation Modal */}
			{showDeleteModal && (
				<Modal
					isOpen={deleteModalRef}
					onClose={handleCancelDelete}
					className="delete-modal"
				>
					<div className="modal-header">
						<h3>Delete Playlist</h3>
						<button className="close-modal" onClick={handleCancelDelete}>
							✕
						</button>
					</div>
					<div className="modal-content">
						<p>
							Are you sure you want to delete
							<strong>
								{" "}
								{playlists.find((p) => p.id === playlistToDelete)?.name}
							</strong>
							? This cannot be undone.
						</p>
					</div>
					<div className="modal-footer">
						<button className="cancel-btn" onClick={handleCancelDelete}>
							Cancel
						</button>
						<button className="delete-btn" onClick={handleConfirmDelete}>
							Delete Playlist
						</button>
					</div>
				</Modal>
			)}

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
