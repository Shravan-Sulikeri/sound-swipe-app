import React, { useState, useEffect } from "react";
import Login from "./Login";

function App() {
	const [userData, setUserData] = useState(null); // KEEPING USER DATA INSTEAD OF TOKEN
	const [isAuthenticated, setIsAuthenticated] = useState(false);
	// ALL TOKEN INFORMATION WILL BE HANDLED BY THE SERVER IF YOU NEED SOMETHING LET JONATHAN KNOW

	// step 1: Check if user is authenticated
	// SEE CHECKAUTH COMMAND

	// Step 2: Fetch user data from the backend
	const fetchUserData = async () => {
		try {
			const response = await fetch("http://localhost:3001/api/me", {
				credentials: "include",
			});
			if (response.status === 401) {
				// Session expired
				setIsAuthenticated(false);
				window.location.href = "http://localhost:3001/login"; // Redirect to login
			} else {
				const data = await response.json();
				setUserData(data);
			}
		} catch (error) {
			console.error("Error fetching user data:", error);
		}
	};

	// Step 2: Check if the user is already logged in (e.g., on page load)
	useEffect(() => {
		const checkAuth = async () => {
			try {
				const response = await fetch("http://localhost:3001/api/check-auth", {
					credentials: "include", // Include session cookies
				});
				const data = await response.json();
				if (data.authenticated) {
					setIsAuthenticated(true);
					fetchUserData(); // Fetch user data if authenticated
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

  return (
    <div>
      {isAuthenticated ? ( 
        <h1>Logged in! Now you can explore music.</h1>
      ): (
        <Login />
      )}
    </div>
  );
}
export default App;