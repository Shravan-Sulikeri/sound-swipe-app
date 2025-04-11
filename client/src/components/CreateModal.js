import React, { useState } from "react";
import Modal from "../components/common/Modal";

const CreatePlaylistModal = ({ isOpen, onClose, onCreate }) => {
	const [newPlaylistName, setNewPlaylistName] = useState("");
	const [isSubmitting, setIsSubmitting] = useState(false);
	const [error, setError] = useState("");

	const handleSubmit = async () => {
		if (!newPlaylistName.trim()) {
			setError("Please enter a playlist name");
			return;
		}

		setIsSubmitting(true);
		setError("");

		try {
			await onCreate(newPlaylistName);
			setNewPlaylistName("");
			onClose();
		} catch (err) {
			setError(err.message || "Failed to create playlist");
		} finally {
			setIsSubmitting(false);
		}
	};

	return (
		<Modal
			isOpen={isOpen}
			onClose={onClose}
			className="playlist-modal"
			header="Create New Playlist"
		>
			<div className="modal-content">
				<p>
					Give your playlist a name. Songs you swipe right on will be added to
					this playlist.
				</p>
				<input
					type="text"
					className="playlist-name-input"
					placeholder="e.g Workout Playlist"
					value={newPlaylistName}
					onChange={(e) => setNewPlaylistName(e.target.value)}
					autoFocus
				/>
				{error && <p className="error-message">{error}</p>}
			</div>
			<div className="modal-footer">
				<button
					className="cancel-btn"
					onClick={onClose}
					disabled={isSubmitting}
				>
					Cancel
				</button>
				<button
					className="create-btn"
					onClick={handleSubmit}
					disabled={newPlaylistName.trim() === "" || isSubmitting}
				>
					{isSubmitting ? "Creating..." : "Create Playlist"}
				</button>
			</div>
		</Modal>
	);
};

export default CreatePlaylistModal;
