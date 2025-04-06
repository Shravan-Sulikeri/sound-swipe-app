import { useRef, useEffect } from "react";

const useModal = (isOpen, onClose) => {
	const modalRef = useRef(null);

	// close modal when clicking outside
	useEffect(() => {
		const handleClickOutside = (event) => {
			if (modalRef.current && !modalRef.current.contains(event.target)) {
				onClose();
			}
		};

		if (isOpen) document.addEventListener("mousedown", handleClickOutside);
		return () => document.removeEventListener("mousedown", handleClickOutside);
	}, [isOpen]);

	return modalRef;
};

export default useModal;
