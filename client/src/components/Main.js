// src/components/MainContent.jsx
import React from "react";

const MainContent = ({
	isSwiping,
	isSidebarCollapsed,
	currentSong,
	isDragging,
	cardTransform,
	activePlaylist,
	playlists,
	progress,
	currentTime,
	duration,
	isPlaying,
	handleStartSwiping,
	handleDragStart,
	handleDragMove,
	handleDragEnd,
	handlePlayPause,
	handleProgressClick,
	handleSwipe,
	cardRef,
}) => {
	const formatTime = (time) => {
		const minutes = Math.floor(time / 60);
		const seconds = Math.floor(time % 60);
		return `${minutes}:${seconds.toString().padStart(2, "0")}`;
	};

	const formatName = (name, maxLength=20) => {
		if(name.length <= maxLength) {
			return name;
		}
		return name.slice(0, maxLength) + "...";
	}

	return (
		<main className={`main-content ${isSidebarCollapsed ? "expanded" : ""}`}>
			<section className={`welcome-section ${isSwiping ? "hidden" : ""}`}>
				<h1>
					Welcome to
					<img
						alt="logo"
						className="logo"
						style={{
							marginLeft: "10px",
							verticalAlign: "middle",
							objectFit: "contain",
						}}
						src={require("../assets/soundswipe-logo-zip-file/png/logo-no-background.png")}
					/>
				</h1>
				<p className="paragraph-text">
					Discover new music by swiping right on songs you like
				</p>
				{!isSwiping && (
					<button className="start-button" onClick={handleStartSwiping}>
						Start Swiping
					</button>
				)}
			</section>

			<div className={`swipe-container ${!isSwiping ? "hidden" : ""}`}>
				{activePlaylist && (
					<div
						className={`active-playlist-indicator ${
							!isSidebarCollapsed ? "sidebar collapsed" : ""
						}`}
					>
						Adding to: {playlists.find((p) => p.id === activePlaylist)?.name}
					</div>
				)}
				<div
					ref={cardRef}
					className={`song-card ${isDragging ? "swiping" : ""}`}
					style={{
						transform: `translate(${cardTransform.x}px, ${cardTransform.y}px) rotate(${cardTransform.rotate}deg)`,
						backgroundImage: `url(${currentSong.coverImage})`,
						backgroundSize: "cover",
						backgroundPosition: "center",
						cursor: activePlaylist ? "grab" : "not-allowed",
					}}
					onMouseDown={activePlaylist ? handleDragStart : null}
					onMouseMove={activePlaylist ? handleDragMove : null}
					onMouseUp={activePlaylist ? handleDragEnd : null}
					onMouseLeave={activePlaylist ? handleDragEnd : null}
				>
					<div className="song-info">
						<div className="song-details">
							<h2 className="song-title">{formatName(currentSong.name)}</h2>
							<p className="artist-name">{currentSong.artists}</p>
						</div>

						<div className="audio-controls">
							<label className="play-label">
								<input
									type="checkbox"
									className="play-btn"
									checked={isPlaying}
									onChange={handlePlayPause}
								/>
								<div className="play-icon"></div>
								<div className="pause-icon"></div>
							</label>
							<div className="progress-container">
								<div className="progress-bar" onClick={handleProgressClick}>
									<div className="progress" style={{ width: `${progress}%` }} />
								</div>
								<div className="time-info">
									<span>{formatTime(currentTime)}</span>-
									<span>{formatTime(duration)}</span>
								</div>
							</div>
						</div>

						<div className="swipe-buttons">
							<button
								disabled={activePlaylist ? null : true}
								className="swipe-button dislike"
								onClick={() => handleSwipe("left")}
							>
								✕
							</button>
							<button
								disabled={activePlaylist ? null : true}
								className="swipe-button like"
								onClick={() => handleSwipe("right")}
							>
								✓
							</button>
						</div>
					</div>
				</div>
			</div>
		</main>
	);
};

export default MainContent;
