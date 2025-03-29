import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class APIClient:
    def __init__(self):
        """Initialize API client with base URL"""
        self.base_url = os.getenv('API_BASE_URL')
    def get_recommendations(self):
        """
        Get music recommendations from the API
        
        Returns:
            dict: API response with recommendations data
        """
        try:
            response = requests.get(f'{self.base_url}/recommendations')
            response.raise_for_status() 
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching recommendations: {str(e)}")
            return {
                'status': 'error',
                'message': f'Connection error: {str(e)}',
                'data': []
            }
    
    def get_playlists(self):
        """
        Get user's playlists from the API
        
        Returns:
            dict: API response with playlists data
        """
        try:
            response = requests.get(f'{self.base_url}/playlists')
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching playlists: {str(e)}")
            return {
                'status': 'error',
                'message': f'Connection error: {str(e)}',
                'data': []
            }

# Example usage
if __name__ == "__main__":
    client = APIClient()
    
    # Get recommendations
    print("Fetching recommendations...")
    recommendations = client.get_recommendations()
    print(f"Status: {recommendations['status']}")
    print(f"Message: {recommendations['message']}")
    print(f"Total recommendations: {len(recommendations.get('data', []))}")
    print(f"Data: {recommendations.get('data')} ")
    
    # Get playlists
    # print("\nFetching playlists...")
    # playlists = client.get_playlists()
    # print(f"Status: {playlists['status']}")
    # print(f"Message: {playlists['message']}")
    # print(f"Total playlists: {(playlists.get('data', []))}")