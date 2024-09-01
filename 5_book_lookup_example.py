import requests  # Import the requests library to handle HTTP requests
import json  # Import the json library to handle JSON data
import urllib.parse  # Import the urllib.parse library to handle URL encoding

def create_google_books_url(query, max_results=4):
    # Convert the query to URL-friendly format
    encoded_query = urllib.parse.quote(query.strip())
    
    # Create the full URL
    base_url = "https://www.googleapis.com/books/v1/volumes"  # Base URL for Google Books API
    params = f"q={encoded_query}&maxResults={max_results}"  # Parameters for the API request
    
    # Handle empty query
    if not encoded_query:
        params = f"q=*&maxResults={max_results}"  # Use a wildcard query if the input is empty
    
    return f"{base_url}?{params}"  # Return the complete URL

# Get user input
user_query = "Pearl Harbor during World War II"  # Example query string

# Create URL using the function
url = create_google_books_url(user_query)  # Generate the URL for the API request

# Send GET request to the API
response = requests.get(url)  # Make the HTTP GET request to the API

# Check if the request was successful
if response.status_code == 200:  # Check if the response status code is 200 (OK)
    # Parse the JSON response
    data = response.json()  # Convert the response to a JSON object
    
    # Limit the number of results to the top 3
    if 'items' in data:  # Check if 'items' key is in the JSON response
        data['items'] = data['items'][:3]  # Slice the list to get only the top 3 items
    
    # Print the JSON structure with indentation
    print(json.dumps(data, indent=2))  # Pretty-print the JSON data with an indentation of 2 spaces
else:
    print(f"Error: Unable to fetch data. Status code: {response.status_code}")  # Print an error message if the request failed
