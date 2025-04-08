require("dotenv").config();
const express = require("express");
const cors = require("cors");
const querystring = require("querystring");
const axios = require("axios");
const morgan = require("morgan");
// Session Information
const session = require("express-session");
// Database and session store
const mongoStore = require("connect-mongo");

const app = express();
app.use(morgan("tiny"));
app.use(
	cors({
		origin: ["http://localhost:3000", "http://localhost:5000"], // Explicitly allow your React app's origin
		credentials: true, // Allow credentials (cookies)
	})
);
app.use(express.json());
app.use(
	session({
		secret: process.env.SESSION_SECRET || "RANDOM STRING",
		resave: false,
		saveUninitialized: true,
		cookie: { maxAge: 60 * 60 * 1000 }, // 1 hour expiration on session
		store: new mongoStore({
			mongoUrl: process.env.MONGO_URL || "mongodb://localhost:27017/example",
		}),
	})
);

const PORT = process.env.PORT || 3001;

//Loading the environment variables

const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;
const REDIRECT_URI =
	process.env.SPOTIFY_REDIRECT_URI || "http://localhost:3001/callback";

// Middleware to check if access token expired and refresh
const refreshTokenIfExpired = async (req, res, next) => {
	if (!req.session.token) {
		return res.status(401).json({ error: "Not authenticated" });
	}

	const { accessToken, refreshToken, expiresIn, timestamp } = req.session.token;
	const isExpired = Date.now() - timestamp > expiresIn * 1000; // Check if token is expired

	if (!isExpired) {
		// Token is still valid
		req.accessToken = accessToken;
		return next();
	}

	try {
		// Token is expired, refresh it
		const response = await axios.post(
			"https://accounts.spotify.com/api/token",
			querystring.stringify({
				grant_type: "refresh_token",
				refresh_token: refreshToken,
			}),
			{
				headers: {
					"Content-Type": "application/x-www-form-urlencoded",
					Authorization: `Basic ${Buffer.from(
						`${CLIENT_ID}:${CLIENT_SECRET}`
					).toString("base64")}`,
				},
			}
		);

		// Update the session with the new token
		req.session.token = {
			accessToken: response.data.access_token,
			refreshToken: refreshToken, // Spotify may not return a new refresh token
			expiresIn: response.data.expires_in,
			timestamp: Date.now(),
		};

		req.accessToken = response.data.access_token;
		next();
	} catch (error) {
		console.error("Error refreshing token:", error.response.data);
		res.status(400).json({ error: "Failed to refresh token" });
	}
};

app.get("/api/check-auth", refreshTokenIfExpired, (req, res) => {
	// If the middleware passes, the user is authenticated
	res.json({ authenticated: true, access_token: req.accessToken });
});

app.get("/api/token", refreshTokenIfExpired, (req, res) => {
	res.json({
		access_token: req.accessToken
	});
});

// Step 1: Redirect user to Spotify for authentication

app.get("/login", (req, res) => {
	const scope =
		// playlist-read-private to see private playlists
		"user-read-private user-read-email playlist-modify-public playlist-modify-private playlist-read-private";
	const authURL =
		"https://accounts.spotify.com/authorize?" +
		querystring.stringify({
			response_type: "code",
			client_id: CLIENT_ID,
			scope: scope,
			redirect_uri: REDIRECT_URI,
		});
	res.redirect(authURL);
});

//Step 2: Handle Spotify callback and exchange code for access token

app.get("/callback", async (req, res) => {
	const code = req.query.code || null;
	try {
		const response = await axios.post(
			"https://accounts.spotify.com/api/token",
			querystring.stringify({
				code: code,
				redirect_uri: REDIRECT_URI,
				grant_type: "authorization_code",
			}),
			{
				headers: {
					"Content-Type": "application/x-www-form-urlencoded",
					Authorization: `Basic ${Buffer.from(
						`${CLIENT_ID}:${CLIENT_SECRET}`
					).toString("base64")}`,
				},
			}
		);
		// information gets added to session store
		req.session.token = {
			accessToken: response.data.access_token,
			refreshToken: response.data.refresh_token,
			expiresIn: response.data.expires_in,
			timestamp: Date.now(), // Store the time when the token was issued
		};

		console.log("Access Token:", response.data.access_token);
		// redirects token back to the app
		res.redirect(`http://localhost:3000/`);
	} catch (error) {
		console.error(
			"Error exchanging code for access token:",
			error.response.data
		);
		res.status(400).json({ error: "Authentication failed" });
	}
});

// Handle logout and destroy session
app.get("/logout", (req, res) => {
	req.session.destroy();
	res.redirect(`http://localhost:3000/`);
});

// Route to fetch user data from Spotify
app.get("/api/me", refreshTokenIfExpired, async (req, res) => {
	try {
		const response = await axios.get("https://api.spotify.com/v1/me", {
			headers: {
				Authorization: `Bearer ${req.accessToken}`,
			},
		});
		res.json(response.data); // need href for https://api.spotify.com/v1/users/{userId}
	} catch (error) {
		res.status(500).json({ error: "Failed to fetch user data" });
	}
});

// Route to fetch user playlists from Spotify
app.get("/api/playlists", refreshTokenIfExpired, async (req, res) => {
	console.log(link);
	try {
		const response = await axios.get(
			`https://api.spotify.com/v1/me/playlists`,
			{
				headers: {
					Authorization: `Bearer ${req.accessToken}`,
				},
			}
		);
		res.json(response.data);
	} catch (error) {
		res.status(500).json({ error: "Failed to fetch user data" });
	}
});

app.listen(PORT, () =>
	console.log(`Server runnning on "http://localhost:${PORT}`)
);
