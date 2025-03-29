# SoundSwipe Server 

This is the backend server for the SoundSwipe application, which provides music recommendations using Spotify and Deezer APIs, enhanced with LLM-powered recommendations.

## Features

- Spotify playlist integration
- Deezer API integration for song previews and cover art
- LLM-powered music recommendations using Groq
- RESTful API endpoints for frontend communication
- Automatic song data enrichment with Deezer information

## Prerequisites

- Python 3.8 or higher
- Node.js
- API Keys (reach out for keys)

## Environment Setup

1. Create a `.env` file in the server directory with the following variables:
```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
GROQ_API_KEY=your_groq_api_key
API_BASE_URL=http://localhost:5000/api
PORT=5000
```

## Installation

1. Create and activate a virtual environment (recommended but not necessary --- skip this for now):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

IMPORTANT: The application must be started in this specific order:

1. Start the Node.js server:
```bash
node server.js
```

2. Start the Flask server:
```bash
python app.py
```

3. Start the React frontend:
```bash
npm start
```

The servers will:
- Initialize the Spotify and Deezer API connections
- Preload song recommendations
- Start listening on their respective ports

## API Endpoints

### GET /api/recommendations
Returns a list of recommended songs with:
- Song name
- Artist name
- Cover image URL
- Preview URL
- Deezer URL

### GET /api/playlists
Returns the user's Spotify playlists

## Project Structure

```
server/
├── app.py              # Main Flask application
├── llm_model.py        # LLM recommendation logic
├── requirements.txt    # Python dependencies
└── .env               # Environment variables (create this)
```

## Dependencies

- Flask
- Flask-CORS
- Groq
- Requests
- python-dotenv
- tqdm

## Error Handling

The server includes comprehensive error handling for:
- API connection issues
- Missing environment variables
- Invalid API responses
- LLM recommendation failures

## Development

To modify the recommendation logic:
1. Edit `llm_model.py`
2. Adjust the prompt in `create_recommendation_prompt()`
3. Modify the data processing in `fetch_user_songs()`

## Testing

To test the server:
1. Ensure all environment variables are set
2. Start the server
3. Use the provided `request.py` script to test endpoints

## Notes

- The server preloads song recommendations on startup
- Deezer API is used for song previews and cover art
- Groq LLM is used for intelligent song recommendations
- CORS is enabled for frontend communication 

## Issues to Address

1. **Duplicate Song Recommendations**

   - The recommendation logic currently suggests the same song multiple times across different playlists. This needs to be refined to ensure unique recommendations per playlist.

2. **Inconsistent Track Retrieval from Deezer**

   - Fetching track information from Deezer can be unreliable, particularly for songs featuring multiple artists. In these cases, a `403` error is returned, indicating that the song cannot be found. Investigate potential workarounds or alternative data sources.

3. **Playlist Integration with Spotify**
   - After retrieving tracks from Deezer, the next step is transforming the data back to the Spotify API to generate user playlists. This integration needs further development and testing.
 