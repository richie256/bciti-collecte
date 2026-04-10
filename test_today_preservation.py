import os
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock
from scraper import get_next_collections, Config

# Mock Config
Config.CACHE_FILE = "test_cache.json"
Config.BROSSARD_SECTOR = "m"

def test_today_preservation():
    today = datetime.now(ZoneInfo("America/Toronto"))
    today_str = today.isoformat()
    
    # 1. Setup a cache file where 'garbage' is today
    cache_data = {
        "timestamp": time.time(),
        "sector": "m",
        "data": {
            "garbage": {"next_date": today_str, "collection_days": "Friday"},
            "recycling": {"next_date": "2026-04-01T00:00:00-04:00", "collection_days": "Wednesday"}
        }
    }
    with open(Config.CACHE_FILE, 'w') as f:
        json.dump(cache_data, f)

    # 2. Mock parse_web_page to return a DIFFERENT (future) date for garbage
    # This simulates the website rolling over to the next week
    future_date = datetime(2026, 4, 15, 0, 0, 0, tzinfo=ZoneInfo("America/Toronto"))
    mock_web_dates = {
        "garbage": {"next_date": future_date, "collection_days": "Friday"},
        "recycling": {"next_date": datetime(2026, 4, 8, 0, 0, 0, tzinfo=ZoneInfo("America/Toronto")), "collection_days": "Wednesday"}
    }

    with patch('scraper.fetch_web_page', return_value="<html></html>"), \
         patch('scraper.parse_web_page', return_value=mock_web_dates):
        
        # force_refresh=True to trigger fetching and merging
        result = get_next_collections(force_refresh=True)
        
        print(f"Today is: {today.date()}")
        print(f"Web said garbage is: {future_date.date()}")
        print(f"Result for garbage: {result['garbage']['next_date'].date()}")
        
        assert result['garbage']['next_date'].date() == today.date()
        print("Verification successful: Today's date was preserved from cache!")
        
        # 3. Verify that recycling was updated to web date (because cache recycling wasn't today or tomorrow)
        assert result['recycling']['next_date'].date() == datetime(2026, 4, 8).date()
        print(f"Result for recycling: {result['recycling']['next_date'].date()}")
        print("Verification successful: Future date was updated from web!")

    # Cleanup
    if os.path.exists(Config.CACHE_FILE):
        os.remove(Config.CACHE_FILE)
