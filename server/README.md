# SoundSwipe Server 

This is the backend server for the SoundSwipe application, which provides music recommendations using Spotify and Deezer APIs, enhanced with LLM-powered recommendations.

**IMPORTANT NOTE:** The server is now backed within flask, no more node.

## Features

- Spotify playlist integration
- Deezer API integration for song previews and cover art
- LLM-powered music recommendations using Groq
- Enhanced song recommendations through Last.fm API integration 
- RESTful API endpoints for frontend communication
- Automatic song data enrichment with Deezer information

## Prerequisites

- Python 3.8 or higher
~~- Node.js~~
- **API Keys (CONTACT FOR KEYS)**

## Environment Setup

1. Create a `.env` file in the server directory with the following variables:
```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri
LAST_FM_API_KEY=your_last_fm_key
GROQ_API_KEY=your_groq_api_key
API_BASE_URL=http://localhost:3001/api
PORT=3001
MONGO_URI=your_mongo_uri
MONGO_CLIENT=your_mongo_client
MONGO_SESSIONS=your_mongo_session
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

**IMPORTANT:** The application must be started in this specific order. No more need for running node.js as we migrated from node server to flask server.

**NOTE:** A new terminal is required for each command.

1. Start the Flask server:
```bash
sound-swipe-app/server
└── python app.py
```

2. Start the React frontend:
```bash
sound-swipe-app/client
└── npm start
```

The servers will:
- Initialize the Spotify, LastFM, Deezer API connections
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
3. Adjust order and method of optimization in `optimize_recommendations()`
4. Modify the data processing in `fetch_user_songs()`

## Testing

To test the server:
1. Ensure all environment variables are set
2. Start the server
3. Use the provided `request.py` script to test endpoints

## Notes

- The server preloads song recommendations on startup
- Deezer API is used for song previews and cover art
- Groq LLM is used for intelligent song recommendations
- Last.fm API is used for further recommendation enhancements after LLM
- CORS is enabled for frontend communication 

## Troubleshooting

### Port 5000 Issue on Mac [***Deprecated***]

>[!WARNING] 
> **DEPRECATED** - Port 5000 is no longer in use. We have moved to using port 3001.

###### ***This information can be completely disregarded.***

If you run into trouble with port 5000 being occupied on your Mac, it's often caused by AirPlay. Follow these steps to resolve the issue:

1. **Open System Preferences** on your Mac.
2. Go to **General**.
3. In the General panel, click **AirDrop & Handoff**.
4. In the AirDrop & Handoff panel, **uncheck** **_AirPlay Receiver_**.
5. Restart the **app.py** server that is using port 5000.



## Issues to Address ~ TODOS
###### ***NOTE ->** Once an issue has been resolved, either remove it from this list or mark it as completed to keep the to-do list up to date.*

&emsp;  ~~1. **Duplicate Song Recommendations**~~  
&emsp; &emsp; &emsp;
 ~~- The recommendation logic currently suggests the same song multiple times across different playlists. This needs to be refined to ensure unique recommendations per playlist.~~

1. **Inconsistent Track Retrieval from Deezer**

   - Fetching track information from Deezer can be unreliable, particularly for songs featuring multiple artists. In these cases, a `403` error is returned, indicating that the song cannot be found. Investigate potential workarounds or alternative data sources.

2. **Playlist Integration with Spotify**
   - After retrieving tracks from Deezer, the next step is transforming the data back to the Spotify API to generate user playlists. This integration needs further development and testing.

3. **Enhance Recommendation Accuracy Using Last.fm** 
   - The recommendation logic has been significantly enhanced with the current integration of Last.fm data. Moving forward, lets aim to enrich the system by incorporating additional sources such as top 500 charts, trending songs, and popular artists to provide even more accurate and diverse recommendations.


