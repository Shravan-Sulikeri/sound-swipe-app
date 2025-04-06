import React from "react";
import useModal from "../../hooks/useModal";

const Modal = ({ isOpen, onClose, children, className = "" }) => {
	const modalRef = useModal(isOpen, onClose); // Using the custom hook

	if (!isOpen) return null;

	return (
		<div className="modal-overlay">
			<div className={`${className}`} ref={modalRef}>
				{children}
			</div>
		</div>
	);
};

export default Modal;
