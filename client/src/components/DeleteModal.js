import React, { useState } from "react";
import Modal from "./common/Modal";

const DeletePlaylistModal = ({
	isOpen,
	onClose,
	onDelete,
	playlistName = "", // Default empty string for safety
	isLoading = false, // Optional prop for parent-controlled loading
}) => {
	const [isDeleting, setIsDeleting] = useState(false);
	const [error, setError] = useState("");

	const handleDelete = async () => {
		setIsDeleting(true);
		setError("");

		try {
			await onDelete(); // Parent handles actual deletion
			onClose(); // Only close if successful
		} catch (err) {
			setError(err.message || "Failed to delete playlist");
		} finally {
			setIsDeleting(false);
		}
	};

	return (
		<Modal
			isOpen={isOpen}
			onClose={onClose}
			className="delete-modal"
			header="Confirm Deletion"
		>
			<div className="modal-content">
				<p>
					Are you sure you want to delete{" "}
					<strong>{playlistName || "this playlist"}</strong>? This action cannot
					be undone.
				</p>
				{error && <div className="error-message">{error}</div>}
			</div>
			<div className="modal-footer">
				<button
					onClick={onClose}
					disabled={isDeleting || isLoading}
					className="cancel-btn"
				>
					Cancel
				</button>
				<button
					onClick={handleDelete}
					disabled={isDeleting || isLoading}
					className="delete-btn"
				>
					{isDeleting ? "Deleting..." : "Delete"}
				</button>
			</div>
		</Modal>
	);
};

export default DeletePlaylistModal;
