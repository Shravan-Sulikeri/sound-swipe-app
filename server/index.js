const express = require('express');
const cors = require('cors');
const session = require('express-session');
require('dotenv').config();
const axios = require('axios');
const app = express();

app.use(cors({
  origin: process.env.FRONTEND_URI,
  credentials: true
}));

app.use(session({
  secret: 'sound-swipe-secret',
  resave: false,
  saveUninitialized: true,
}));

app.get('/login', (req, res) => {
  const scopes = 'user-read-private user-read-email playlist-modify-public';
  res.redirect('https://accounts.spotify.com/authorize?' +
    new URLSearchParams({
      response_type: 'code',
      client_id: process.env.SPOTIFY_CLIENT_ID,
      scope: scopes,
      redirect_uri: process.env.REDIRECT_URI,
    }).toString());
});

app.get('/callback', async (req, res) => {
  const code = req.query.code || null;

  try {
    const response = await axios.post('https://accounts.spotify.com/api/token',
      new URLSearchParams({
        grant_type: 'authorization_code',
        code: code,
        redirect_uri: process.env.REDIRECT_URI,
        client_id: process.env.SPOTIFY_CLIENT_ID,
        client_secret: process.env.SPOTIFY_CLIENT_SECRET,
      }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );

    req.session.access_token = response.data.access_token;
    req.session.refresh_token = response.data.refresh_token;

    res.redirect(process.env.FRONTEND_URI);
  } catch (error) {
    console.error(error.response?.data || error.message);
    res.status(500).json({ error: 'Failed to get tokens from Spotify' });
  }
});

app.get('/api/check-auth', (req, res) => {
  res.json({ authenticated: !!req.session.access_token });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
