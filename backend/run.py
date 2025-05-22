# run.py (fixed)
import os
import time
import requests
import json
import re
from tqdm import tqdm
from math import ceil

API_KEY = os.getenv('OPENAQ_API_KEY', '4ae4b2bd8d43ae5b61db36856ec3ad2a7b51a1a7376ee22dc99f7fb21e21a12a')
BASE_URL = 'https://api.openaq.org/v3'
US_COUNTRY_ID = 155  # Verified correct US country ID
OUTPUT_FILE = 'usa_locations.json'

def parse_found_value(found):
    """Handle OpenAQ's 'found' values which can be strings like '>1000'"""
    if isinstance(found, str):
        # Extract numeric part from strings like ">1000"
        match = re.search(r'\d+', found)
        return int(match.group()) if match else 0
    return found

def fetch_us_locations():
    """Fetch all US locations using country ID with proper pagination"""
    with requests.Session() as session:
        all_locations = []
        page = 1
        total_pages = None
        
        with tqdm(desc="Fetching US locations", unit="page") as pbar:
            while True:
                try:
                    response = session.get(
                        f"{BASE_URL}/locations",
                        params={
                            'countries_id': US_COUNTRY_ID,
                            'limit': 1000,
                            'page': page
                        },
                        headers={'X-API-Key': API_KEY}
                    )

                    # Handle rate limits
                    if response.status_code == 429:
                        reset = int(response.headers.get('x-ratelimit-reset', 60))
                        tqdm.write(f"Rate limited. Waiting {reset}s...")
                        time.sleep(reset + 2)
                        continue
                        
                    response.raise_for_status()
                    data = response.json()
                    
                    # Store results
                    all_locations.extend(data.get('results', []))
                    
                    # Update pagination metadata
                    meta = data.get('meta', {})
                    if not total_pages:
                        found = parse_found_value(meta.get('found', 0))
                        limit = meta.get('limit', 1000)
                        total_pages = ceil(found / limit) if found else 1
                        pbar.total = total_pages
                    
                    # Update progress bar
                    pbar.update(1)
                    pbar.set_postfix({
                        'total': len(all_locations),
                        'page': f"{page}/{total_pages}"
                    })

                    # Exit loop if we've fetched all pages
                    if page >= total_pages:
                        break
                        
                    page += 1
                    time.sleep(1)  # Rate limit buffer

                except requests.exceptions.RequestException as e:
                    tqdm.write(f"Error: {str(e)}")
                    break

        # Save results
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(all_locations, f, indent=2)
            
        print(f"\nFound {len(all_locations)} US locations")
        print(f"Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_us_locations()
