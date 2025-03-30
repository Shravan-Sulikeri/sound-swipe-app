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

def print_tracks(data): # takes dict, just prints title and artist     
    max = 0
    print("Data: ")
    for x in data:
        if len(x['name']) > max: 
            max = len(x['name'])
    for x in data:
        print(f'\'{x['name'] + "\'" + " "*(max - len(x["name"]))}    - {x["artist"]}')  # Print title and artist with padding

# Example usage
if __name__ == "__main__":
    client = APIClient()
    
    # Get recommendations
    print("\nFetching recommendations...\n")
    recommendations = client.get_recommendations()
    print(f"Status: {recommendations['status']}")
    print(f"Total recommendations: {len(recommendations.get('data', []))}")
    data = recommendations.get('data')
    print_tracks(data)  # Print the formatted recommendations
    # Get playlists
    # print("\nFetching playlists...")
    # playlists = client.get_playlists()
    # print(f"Status: {playlists['status']}")
    # print(f"Message: {playlists['message']}")
    # print(f"Total playlists: {(playlists.get('data', []))}")