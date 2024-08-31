import requests
import json
import urllib.parse

def create_google_books_url(query, max_results=4):
    # Convert the query to URL-friendly format
    encoded_query = urllib.parse.quote(query.strip())
    
    # Create the full URL
    base_url = "https://www.googleapis.com/books/v1/volumes"
    params = f"q={encoded_query}&maxResults={max_results}"
    
    # Handle empty query
    if not encoded_query:
        params = f"q=*&maxResults={max_results}"
    
    return f"{base_url}?{params}"

# Get user input
user_query = "Pearl Harbor during World War II"

# Create URL using the function
url = create_google_books_url(user_query)

# Send GET request to the API
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Limit the number of results to the top 3
    if 'items' in data:
        data['items'] = data['items'][:3]
    
    # Print the JSON structure with indentation
    print(json.dumps(data, indent=2))
else:
    print(f"Error: Unable to fetch data. Status code: {response.status_code}")