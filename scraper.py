import requests
import json
import time
import os
from bs4 import BeautifulSoup
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
import logging
from config import Config

logger = logging.getLogger(__name__)

# Mapping of English titles on website to internal keys
COLLECTION_MAPPING = {
    "Garbage": "garbage",
    "Recycling": "recycling",
    "Food residues": "food_residues",
    "Wooden bulky items": "wooden_bulky_items",
    "Branches and tree trimmings": "branches",
    "Green waste": "green_waste",
    "Fir trees": "fir_trees",
    "Surplus recovery": "surplus_recovery"
}

def fetch_web_page():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(Config.WEB_URL, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch web data: {e}")
        return None

def parse_web_page(html_content):
    if not html_content:
        return {}

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        next_collections = {key: None for key in COLLECTION_MAPPING.values()}
        
        cards = soup.find_all("div", class_="collect-card")
        for card in cards:
            title_tag = card.find("h4")
            if not title_tag:
                continue
            
            title_span = title_tag.find("span", class_="span-title")
            if not title_span:
                continue
            
            title = title_span.get_text(strip=True)
            en_key = COLLECTION_MAPPING.get(title)
            if not en_key:
                # Try partial match if exact match fails
                for k, v in COLLECTION_MAPPING.items():
                    if k in title:
                        en_key = v
                        break
            
            if en_key:
                # Find the "Next collection:" section
                day_items = card.find_all("div", class_="card-collect-item")
                for item in day_items:
                    label_span = item.find("span", class_="span-title")
                    if label_span and "Next collection" in label_span.get_text():
                        date_span = item.find("span", class_="info")
                        if date_span:
                            date_str = date_span.get_text(strip=True)
                            try:
                                # Date format is DD/MM/YYYY based on curl output
                                next_date = datetime.strptime(date_str, "%d/%m/%Y").replace(tzinfo=ZoneInfo("America/Toronto"))
                                current_next = next_collections[en_key]
                                if current_next is None or next_date < current_next:
                                    next_collections[en_key] = next_date
                            except ValueError as ve:
                                logger.error(f"Failed to parse date string '{date_str}': {ve}")

        return next_collections
    except Exception as e:
        logger.error(f"Failed to parse web data: {e}")
        return {}

def save_cache(next_dates):
    # Convert datetimes to strings for JSON
    serializable_dates = {k: v.isoformat() if v else None for k, v in next_dates.items()}
    cache_data = {
        "timestamp": time.time(),
        "sector": Config.BROSSARD_SECTOR,
        "data": serializable_dates
    }
    try:
        with open(Config.CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
        logger.info(f"Cache saved to {Config.CACHE_FILE}")
    except Exception as e:
        logger.error(f"Failed to save cache: {e}")

def load_cache_raw():
    if not os.path.exists(Config.CACHE_FILE):
        return None
    
    try:
        with open(Config.CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        # Check if cache is for the same sector
        if cache_data.get("sector") != Config.BROSSARD_SECTOR:
            return None
            
        # Convert strings back to datetimes
        next_dates = {}
        for k, v in cache_data.get("data", {}).items():
            if v:
                next_dates[k] = datetime.fromisoformat(v)
            else:
                next_dates[k] = None
        
        return {
            "timestamp": cache_data.get("timestamp", 0),
            "data": next_dates
        }
    except Exception as e:
        logger.error(f"Failed to load raw cache: {e}")
        return None

def load_cache():
    raw_cache = load_cache_raw()
    if not raw_cache:
        return None
    
    # Check if cache is too old (12 hours by default)
    if time.time() - raw_cache["timestamp"] > Config.CACHE_MAX_AGE:
        logger.info("Cache metadata expired")
        return None
    
    next_dates = raw_cache["data"]
    today = datetime.now(ZoneInfo("America/Toronto")).date()
    
    for v in next_dates.values():
        if v and v.date() < today:
            logger.info("Cache contains past dates, forcing refresh")
            return None
            
    logger.info("Using cached collection data")
    return next_dates

def get_next_collections(force_refresh=False):
    if not force_refresh:
        cached_data = load_cache()
        if cached_data is not None:
            return cached_data
    
    logger.info("Fetching fresh collection data from website")
    content = fetch_web_page()
    web_dates = parse_web_page(content)
    
    if not web_dates:
        # If fetch failed, return whatever we have in cache even if stale
        raw_cache = load_cache_raw()
        return raw_cache["data"] if raw_cache else {}

    # Merge with raw cache to preserve "today's" dates
    # If the website has already rolled over to the next week but it's still "today",
    # we want to keep "today" until the day is over.
    raw_cache = load_cache_raw()
    final_dates = {}
    today = datetime.now(ZoneInfo("America/Toronto")).date()
    
    # If raw_cache is from a different sector, don't use it for merging
    cached_dates = raw_cache["data"] if raw_cache else {}
    
    for key in COLLECTION_MAPPING.values():
        web_date = web_dates.get(key)
        cached_date = cached_dates.get(key)
        
        if cached_date and cached_date.date() == today:
            # Preserve today's date if we had it in cache
            final_dates[key] = cached_date
            logger.info(f"Preserving today's collection for {key}: {cached_date.date()}")
        else:
            final_dates[key] = web_date
            
    save_cache(final_dates)
    return final_dates
