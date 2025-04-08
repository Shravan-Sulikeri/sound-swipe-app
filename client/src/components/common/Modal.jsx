import React from "react";
import useModal from "../../hooks/useModal";

const Modal = ({ isOpen, onClose, children, className = "", header = "" }) => {
	const modalRef = useModal(isOpen, onClose); // Using the custom hook

	if (!isOpen) return null;

	const Header = () => {
		return (
			<div className="modal-header">
				<h3>{header}</h3>
				<button className="close-modal" onClick={onClose}>
					✕
				</button>
			</div>
		);
	};

	return (
		<div className="modal-overlay">
			<div className={`${className}`} ref={modalRef}>
				<Header />
				{children}
			</div>
		</div>
	);
};

export default Modal;
