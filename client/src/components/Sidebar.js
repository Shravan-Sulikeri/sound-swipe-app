import React, { useState } from "react";
import { IoIosClose } from "react-icons/io";
import { FaSyncAlt } from "react-icons/fa";

const Sidebar = ({
  isLoadingSongs,
  isSidebarCollapsed,
  playlists,
  activePlaylist,
  playlistSongs,
  handlePlaylistSelect,
  handleDeleteClick,
  openCreateModal,
  handleDeleteSong,
  onRefresh,
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const handleRefresh = async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    try {
      await onRefresh(); // Calls the refresh handler from Home
    } finally {
      setIsRefreshing(false);
    }
  };

  // Helper function to get optimistic song count
  const getOptimisticSongCount = (playlist) => {
    // If this is the active playlist, use the current playlistSongs length
    // which will reflect any additions or deletions immediately
    if (activePlaylist === playlist.id) {
      return playlistSongs.length;
    }
    // Otherwise use the count from the playlist data
    return playlist.songCount;
  };
  
  return (
    <aside className={`sidebar ${isSidebarCollapsed ? "collapsed" : ""}`}>
      <div className="sidebar-header">
        <h2 className="playlist-text">Your Playlists</h2>
        <div className="sidebar-actions">
          <button
            onClick={handleRefresh}
            className="refresh-btn"
            disabled={isRefreshing}
            title="Refresh playlists"
          >
            <FaSyncAlt className={isRefreshing ? "spinning" : ""} />
          </button>
          <button onClick={openCreateModal} className="add-playlist-btn">
            +
          </button>
        </div>
      </div>
      <div className="playlist-list">
        {isRefreshing && playlists.length === 0 ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p
              style={{ color: "rgba(255, 255, 255, 0.6)", textAlign: "center" }}
            >
              Loading playlists...
            </p>
          </div>
        ) : playlists.length === 0 ? (
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
                    {getOptimisticSongCount(playlist)} songs
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
                  {isLoadingSongs ? (
                    <div className="loading-spinner">Loading songs...</div>
                  ) : (
                    playlistSongs.map((song, index) => (
                      <div key={song.id} className="playlist-song-item">
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
                          <IoIosClose />
                        </button>
                      </div>
                    ))
                  )}
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