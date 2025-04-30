import React, { useState, useEffect } from "react";
import Login from "./Pages/Login";
import Home from "./Pages/Home";
import { API_BASE_URL } from "./services/api";

function App() {
	const [isAuthenticated, setIsAuthenticated] = useState(false);

	useEffect(() => {
		const checkAuth = async () => {
			try {
				const response = await fetch(`${API_BASE_URL}/api/check-auth`, {
					credentials: "include",
				});
				const data = await response.json();
				if (data.authenticated) {
					setIsAuthenticated(true);
				} else {
					setIsAuthenticated(false);
				}
			} catch (error) {
				console.error("Error checking authentication:", error);
				setIsAuthenticated(false);
			}
		};
		checkAuth();
	}, []);

	return <div> {isAuthenticated ? <Home /> : <Login />} </div>;
}
export default App;
