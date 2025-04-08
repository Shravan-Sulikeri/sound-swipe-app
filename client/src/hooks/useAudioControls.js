// src/hooks/useAudioControls.js
import { useState, useCallback } from "react";

const useAudioControls = (audioRef) => {
	const [isPlaying, setIsPlaying] = useState(false);
	const [progress, setProgress] = useState(0);
	const [currentTime, setCurrentTime] = useState(0);
	const [duration, setDuration] = useState(0);

	const handleTimeUpdate = useCallback(() => {
		if (!audioRef.current) return;
		const newTime = audioRef.current.currentTime;
		setCurrentTime(newTime);
		setProgress((newTime / duration) * 100);
	}, [duration]);

	const handleLoadedMetadata = useCallback(() => {
		if (audioRef.current) {
			setDuration(audioRef.current.duration);
		}
	}, []);

	const controlAudio = useCallback(
		(action, options = {}) => {
			if (!audioRef.current) return;

			const { resetTime = false, seekTo } = options;

			switch (action) {
				case "play":
					if (resetTime) audioRef.current.currentTime = 0;
					if (typeof seekTo === "number") {
						audioRef.current.currentTime = seekTo;
					}
					audioRef.current
						.play()
						.then(() => setIsPlaying(true))
						.catch((error) => {
							console.error("Playback failed:", error);
							setIsPlaying(false);
						});
					break;

				case "pause":
					audioRef.current.pause();
					setIsPlaying(false);
					break;

				case "stop":
					audioRef.current.pause();
					audioRef.current.currentTime = 0;
					setIsPlaying(false);
					break;

				case "toggle":
					audioRef.current.paused
						? controlAudio("play", options)
						: controlAudio("pause");
					break;

				case "seek":
					if (typeof seekTo === "number") {
						audioRef.current.currentTime = seekTo;
						setCurrentTime(seekTo);
						setProgress((seekTo / duration) * 100);
					}
					break;

				default:
					break;
			}
		},
		[duration]
	);

	return {
		isPlaying,
		progress,
		currentTime,
		duration,
		handleTimeUpdate,
		handleLoadedMetadata,
		controlAudio,
	};
};

export default useAudioControls;
