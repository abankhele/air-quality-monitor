import os
import requests
import time

API_KEY = '4ae4b2bd8d43ae5b61db36856ec3ad2a7b51a1a7376ee22dc99f7fb21e21a12a'
url = 'https://api.openaq.org/v3/locations'
headers = {'X-API-Key': API_KEY}

def count_usa_locations():
    page = 1
    limit = 1000  # Maximum allowed by API
    total_count = 0
    
    while True:
        params = {
            'countries_id': 155,  # USA
            'limit': limit,
            'page': page
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        # Handle rate limits
        if response.status_code == 429:
            reset_time = int(response.headers.get('x-ratelimit-reset', 60))
            print(f"Rate limited. Waiting {reset_time} seconds...")
            time.sleep(reset_time + 1)
            continue
            
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        count = len(results)
        
        if count == 0:
            break
            
        total_count += count
        print(f"Page {page}: Found {count} locations")
        
        page += 1
        time.sleep(1)  # Be nice to the API
    
    return total_count

try:
    count = count_usa_locations()
    print(f"Total number of USA locations: {count}")
except Exception as e:
    print(f"Error: {e}")
