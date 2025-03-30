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

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

**IMPORTANT:** The application must be started in this specific order.

**NOTE:** A new terminal is required for each command.

1. Start the Node.js server:
```bash
sound-swipe-app
└── node server.js
```

2. Start the Flask server:
```bash
sound-swipe-app/server
└── python app.py
```

3. Start the React frontend:
```bash
sound-swipe-app/client
└── npm start
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
- If on Mac and you run into trouble with port 5000, to fix it, you need to turn off AirPlay Receiver. This can be done by unchecking AirPlay Receiver in the General section of System Preferences.

## Troubleshooting

### Port 5000 Issue on Mac

If you run into trouble with port 5000 being occupied on your Mac, it’s often caused by AirPlay. Follow these steps to resolve the issue:

1. **Open System Preferences** on your Mac.
2. Go to **General**.
3. In the General panel, click **AirDrop & Handoff**. 
4. In the AirDrop & Handoff panel, **uncheck** ***AirPlay Receiver***.
4. Restart the **app.py** server that is using port 5000.

If the issue persists, a system reboot may be required.


## Issues to Address -- TODOS
###### ***NOTE ->** When issue has been solved simply remove remove from the list or mark **DONE***

1. **Duplicate Song Recommendations**

   - The recommendation logic currently suggests the same song multiple times across different playlists. This needs to be refined to ensure unique recommendations per playlist.

2. **Inconsistent Track Retrieval from Deezer**

   - Fetching track information from Deezer can be unreliable, particularly for songs featuring multiple artists. In these cases, a `403` error is returned, indicating that the song cannot be found. Investigate potential workarounds or alternative data sources.

3. **Playlist Integration with Spotify**
   - After retrieving tracks from Deezer, the next step is transforming the data back to the Spotify API to generate user playlists. This integration needs further development and testing.
 