import React, { useState, useRef, useEffect } from 'react';
import '../styling/home.css';

const Home = () => {
    const [isSwiping, setIsSwiping] = useState(false);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [playlists, setPlaylists] = useState([]);
    const [currentSong, setCurrentSong] = useState({
        title: 'Sample Song Title',
        artist: 'Artist Name',
        coverImage: 'https://via.placeholder.com/400',
        previewUrl: 'https://example.com/preview.mp3',
    });
    const [isPlaying, setIsPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [cardTransform, setCardTransform] = useState({ x: 0, y: 0, rotate: 0 });
    const [isAdd, setIsAdd] = useState(false);

    const audioRef = useRef(null);
    const cardRef = useRef(null);

    const handleLogout = () => {
        window.location.href = "http://localhost:3001/logout";
    };

    const handleAddPlaylist = () => {
        setIsAdd(true);
    };

    const handleExitPlaylist = () => {
        setIsAdd(false);
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

    const handleSwipe = (direction) => {
        const card = cardRef.current;
        if (card) {
            card.classList.add(`swiped-${direction}`);
            setTimeout(() => {
                // TODO: Implement swipe logic
                console.log(`Swiped ${direction}`);
                // Reset card position
                card.classList.remove(`swiped-${direction}`);
                setCardTransform({ x: 0, y: 0, rotate: 0 });
            }, 300);
        }
    };

    const handleDragStart = (e) => {
        setIsDragging(true);
        setDragStart({
            x: e.clientX - cardTransform.x,
            y: e.clientY - cardTransform.y
        });
    };

    const handleDragMove = (e) => {
        if (!isDragging) return;

        const x = e.clientX - dragStart.x;
        const y = e.clientY - dragStart.y;
        const rotate = x * 0.1; // Rotate based on drag distance

        setCardTransform({ x, y, rotate });
    };

    const handleDragEnd = () => {
        if (!isDragging) return;
        setIsDragging(false);

        const { x } = cardTransform;
        if (Math.abs(x) > 100) {
            handleSwipe(x > 0 ? 'right' : 'left');
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
            setCurrentTime(audioRef.current.currentTime);
            setProgress((audioRef.current.currentTime / audioRef.current.duration) * 100);
        }
    };

    const handleLoadedMetadata = () => {
        if (audioRef.current) {
            setDuration(audioRef.current.duration);
        }
    };

    const formatTime = (time) => {
        const minutes = Math.floor(time / 60);
        const seconds = Math.floor(time % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
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

    return (
        <div className="home-container">
            {/* Sidebar Toggle */}
            <button 
                className={`sidebar-toggle ${isSidebarCollapsed ? 'collapsed' : ''}`}
                onClick={toggleSidebar}
            >
                {isSidebarCollapsed ? '☰' : '←'}
            </button>

            {/* Sidebar */}
            <aside className={`sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}>
                <div className="sidebar-header">
                    <h2 className='playlist-text'>Your Playlists</h2>
                    <button onClick={handleAddPlaylist} className="add-playlist-btn">+</button>
                    {isAdd ? (
                        <div className="add-playlist-form">
                            <input type="text" placeholder="Playlist Name" />
                            <button onClick={handleExitPlaylist} className="add-playlist-submit">Create</button>
                        </div>
                    ) : null}
                </div>
                <div className="playlist-list">
                    {playlists.length === 0 ? (
                        <p style={{ color: 'rgba(255, 255, 255, 0.6)', textAlign: 'center' }}>
                            No playlists yet. Create one to get started!
                        </p>
                    ) : (
                        playlists.map(playlist => (
                            <div key={playlist.id} className="playlist-item">
                                <img src={playlist.coverImage} alt={playlist.name} />
                                <div className="playlist-info">
                                    <div className="playlist-name">{playlist.name}</div>
                                    <div className="playlist-song-count">{playlist.songCount} songs</div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </aside>

            {/* Main content */}
            <main className={`main-content ${isSidebarCollapsed ? 'expanded' : ''}`}>
                <section className={`welcome-section ${isSwiping ? 'hidden' : ''}`}>
                            <h1>Welcome to 
                        <img alt="logo" 
                            className="logo"  
                            style={{ marginLeft: '10px', verticalAlign: 'middle', objectFit: 'contain'}}
                            src={require('../assets/soundswipe-logo-zip-file/png/logo-no-background.png')}/>
                        </h1>
                    <p className='paragraph-text'>Discover new music by swiping right on songs you like</p>
                    {!isSwiping && (
                        <button className="start-button" onClick={handleStartSwiping}>
                            Start Swiping
                        </button>
                    )}
                </section>

                <div className={`swipe-container ${!isSwiping ? 'hidden' : ''}`}>
                    <div 
                        ref={cardRef}
                        className={`song-card ${isDragging ? 'swiping' : ''}`}
                        style={{
                            transform: `translate(${cardTransform.x}px, ${cardTransform.y}px) rotate(${cardTransform.rotate}deg)`
                        }}
                        onMouseDown={handleDragStart}
                        onMouseMove={handleDragMove}
                        onMouseUp={handleDragEnd}
                        onMouseLeave={handleDragEnd}
                    >
                        <img 
                            src={currentSong.coverImage} 
                            alt={currentSong.title}
                            className="song-image"
                        />
                        <div className="song-info">
                            <div>
                                <h2 className="song-title">{currentSong.title}</h2>
                                <p className="artist-name">{currentSong.artist}</p>
                            </div>
                            
                            <div className="audio-controls">
                                <button className="play-pause-btn" onClick={handlePlayPause}>
                                    {isPlaying ? '⏸' : '▶'}
                                </button>
                                <div className="progress-bar" onClick={handleProgressClick}>
                                    <div 
                                        className="progress" 
                                        style={{ width: `${progress}%` }}
                                    />
                                </div>
                                <div className="time-info">
                                    <span>{formatTime(currentTime)}</span>
                                    <span>{formatTime(duration)}</span>
                                </div>
                            </div>

                            <div className="swipe-buttons">
                                <button 
                                    className="swipe-button dislike"
                                    onClick={() => handleSwipe('left')}
                                >
                                    ✕
                                </button>
                                <button 
                                    className="swipe-button like"
                                    onClick={() => handleSwipe('right')}
                                >
                                    ✓
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

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