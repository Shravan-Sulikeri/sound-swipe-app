import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class APIClient:
    def __init__(self):
        """Initialize API client with base URL"""
        self.base_url = 'http://localhost:3001'
        
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
    
    def get_memory_usage(self):
        """
        Get memory usage statistics from the API
        Returns:
        dict: Memory usage statistics
        """
        try:
            response = requests.get(f'{self.base_url}/memory')
            response.raise_for_status()
            
            # Debug: Print response details
            print(f"Response status code: {response.status_code}")
            print(f"Response type: {type(response)}")
            print(f"Response content type: {response.headers.get('Content-Type', 'unknown')}")
            
            # Check if response contains valid JSON before parsing
            try:
                # Print the raw response for debugging
                print(f"Raw response text: {response.text[:100]}...")  # First 100 chars
                
                if not response.text.strip():
                    return {
                        'status': 'error',
                        'message': 'Empty response from server'
                    }
                
                # Parse the text content of the response
                return response.json()
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {str(e)}")
                print(f"Raw response content: {response.text[:200]}...")  # Print first 200 chars for debugging
                
                # If the response is a Response object itself, handle that case
                if "Response [" in response.text:
                    return {
                        'status': 'success',
                        'message': 'Server responded with status code 200',
                        'memory_info': 'Memory data not returned in proper JSON format'
                    }
                
                return {
                    'status': 'error',
                    'message': f'Invalid JSON response: {str(e)}',
                    'raw_response': response.text[:500]  # Include part of the response for debugging
                }
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching memory usage: {str(e)}")
            return {
                'status': 'error',
                'message': f'Connection error: {str(e)}'
            }

def print_tracks(data):  # takes dict, just prints title and artist
    max_length = 0
    print("Data: ")
    for x in data:
        if len(x['name']) > max_length:
            max_length = len(x['name'])
    for x in data:
        print(f'\'{x["name"] + "\'" + " "*(max_length - len(x["name"]))} - {x["artist"]}')  # Print title and artist with padding

def print_memory_stats(stats):
    """Print formatted memory statistics"""
    print("\n===== MEMORY USAGE STATISTICS =====")
    
    # Check if there was an error
    if 'status' in stats and stats['status'] == 'error':
        print(f"Error: {stats['message']}")
        if 'raw_response' in stats:
            print(f"Server response: {stats['raw_response']}")
        return
    
    # Format bytes to human-readable format
    def format_bytes(bytes_value):
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if bytes_value < 1024 or unit == 'GB':
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
    
    # Print RSS (Resident Set Size) - actual physical memory used
    rss = stats.get('rss', 0)
    print(f"RSS (Physical Memory): {format_bytes(rss)}")
    
    # Print VMS (Virtual Memory Size)
    vms = stats.get('vms', 0)
    print(f"VMS (Virtual Memory): {format_bytes(vms)}")
    
    # Print memory percentage if available
    if 'percent' in stats:
        print(f"Memory Usage: {stats['percent']:.2f}% of system memory")
        
    # Print USS if available (Unique Set Size - memory unique to this process)
    uss = stats.get('uss', 0)
    if uss > 0:
        print(f"USS (Unique Memory): {format_bytes(uss)}")
    
    # Print human-readable values if provided
    if 'rss_human' in stats:
        print(f"Human-readable RSS: {stats['rss_human']}")
    if 'vms_human' in stats:
        print(f"Human-readable VMS: {stats['vms_human']}")
    
    print("=====================================")

# Example usage
if __name__ == "__main__":
    client = APIClient()
    
    while True:
        print("\nOptions:")
        print("1. Check memory usage")
        print("2. Get recommendations")
        print("3. Exit")
        
        choice = input("Select an option (1-3): ")
        
        if choice == '1':
            # Get memory stats
            print("\nFetching memory usage...\n")
            memory_stats = client.get_memory_usage()
            print_memory_stats(memory_stats)
            
        elif choice == '2':
            # Get recommendations
            print("\nFetching recommendations...\n")
            recommendations = client.get_recommendations()
            print(f"Status: {recommendations.get('status', 'unknown')}")
            print(f"Total recommendations: {len(recommendations.get('data', []))}")
            data = recommendations.get('data', [])
            if data:
                print_tracks(data)  # Print the formatted recommendations
                
        elif choice == '3':
            print("Exiting...")
            break
            
        else:
            print("Invalid option. Please try again.")