require("dotenv").config();
const express = require("express");
const cors = require("cors");
const querystring = require("querystring");
const axios = require("axios");
// Session Information
const session = require("express-session");
// Database and session store
const mongoose = require("mongoose");
const mongoStore = require("connect-mongo");

const app = express();
app.use(cors());
app.use(express.json());
app.use(
	session({
		secret: "TO REPLACE THIS", // Might need to add to environment variables
		resave: false,
		saveUninitialized: false,
		cookie: { maxAge: 5 * 60 * 1000 }, // 5 minute expiration on session
		store: new mongoStore({
			mongoUrl: "mongodb://localhost:27017/example",
		}),
	})
);

const PORT = process.env.PORT || 3001;

//Loading the environment variables

const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;
const REDIRECT_URI =
	process.env.SPOTIFY_REDIRECT_URI || "http://localhost:3001/callback";

// Step 1: Redirect user to Spotify for authentication

app.get("/login", (req, res) => {
	const scope =
		"user-read-private user-read-email playlist-modify-public playlist-modify-private";
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
		};
		// redirects token back to the app
		res.redirect(
			`http://localhost:3000/?access_token=${response.data.access_token}`
		);
	} catch (error) {
		console.error(
			"Error exchanging code for access token:",
			error.response.data
		);
		res.status(400).json({ error: "Authentication failed" });
	}
});

// Step 3: Refresh access token when it expires

app.post("/refresh", async (req, res) => {
	const refreshToken = req.session.token.refreshToken;
	try {
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

		res.json({
			accessToken: response.data.access_token,
			expiresIn: response.data.expires_in,
		});
	} catch (error) {
		res.status(400).json({ error: "Failed to refresh token" });
	}
});

app.listen(PORT, () =>
	console.log(`Server runnning on "http://localhost:${PORT}`)
);
