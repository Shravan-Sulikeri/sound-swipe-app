import React from "react";

const Sidebar = ({
	isSidebarCollapsed,
	playlists,
	activePlaylist,
	handlePlaylistSelect,
	handleDeleteClick,
	handleOpenModal,
	handleDeleteSong,
}) => {
	return (
		<aside className={`sidebar ${isSidebarCollapsed ? "collapsed" : ""}`}>
			<div className="sidebar-header">
				<h2 className="playlist-text">Your Playlists</h2>
				<button onClick={handleOpenModal} className="add-playlist-btn">
					+
				</button>
			</div>
			<div className="playlist-list">
				{playlists.length === 0 ? (
					<p style={{ color: "rgba(255, 255, 255, 0.6)", textAlign: "center" }}>
						No playlists yet. Create one to get started!
					</p>
				) : (
					playlists.map((playlist) => (
						<div key={playlist.id}>
							<div
								className={`playlist-item ${
									activePlaylist === playlist.id ? "active" : ""
								}`}
								onClick={() => handlePlaylistSelect(playlist.id)}
							>
								<img src={playlist.coverImage} alt={playlist.name} />
								<div className="playlist-info">
									<div className="playlist-name">{playlist.name}</div>
									<div className="playlist-song-count">
										{playlist.songCount} songs
									</div>
								</div>
								<button
									className="delete-playlist-btn"
									onClick={(e) => handleDeleteClick(e, playlist.id)}
									aria-label="Delete playlist"
								>
									<span className="delete-icon">×</span>
								</button>
							</div>

							{/* 🎵 Playlist Songs (only shown for selected playlist) */}
							{activePlaylist === playlist.id && playlist.songs.length > 0 && (
								<div className="playlist-songs">
									{playlist.songs.map((song, index) => (
										<div key={index} className="playlist-song-item">
											<img
												src={song.coverImage}
												alt={song.name}
												className="playlist-song-img"
											/>
											<span style={{ flex: 1 }}>{song.name}</span>
											<button
												className="delete-song-btn"
												onClick={() => handleDeleteSong(playlist.id, index)}
												title="Remove song"
											>
												❌
											</button>
										</div>
									))}
								</div>
							)}
						</div>
					))
				)}
			</div>
		</aside>
	);
};

export default Sidebar;
