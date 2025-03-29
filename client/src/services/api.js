const API_BASE_URL = 'http://localhost:5000';

export const getSampleTracks = async (count = 20) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/recommendations`);
        if (!response.ok) {
            throw new Error('Failed to fetch sample tracks');
        }
        const data = await response.json();
        return data.data.map(track => ({
            id: track.id,
            name: track.name,
            artists: track.artist,
            coverImage: track.image,
            previewUrl: track.preview_url
        }));
    } catch (error) {
        console.error('Error fetching sample tracks:', error);
        throw error;
    }
};

export const getRecommendations = async (likedSongIds, count = 20) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/recommendations`);
        if (!response.ok) {
            throw new Error('Failed to get recommendations');
        }
        
        const data = await response.json();
        return data.data.map(track => ({
            id: track.id,
            name: track.name,
            artists: track.artist,
            coverImage: track.image,
            previewUrl: track.preview_url
        }));
    } catch (error) {
        console.error('Error getting recommendations:', error);
        throw error;
    }
}; 