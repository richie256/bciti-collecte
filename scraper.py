import requests
import json
import time
import os
from bs4 import BeautifulSoup
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
import logging
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import Config

logger = logging.getLogger(__name__)

# Titles as they appear on the Brossard website
WEB_TITLES: Dict[str, Dict[str, str]] = {
    "fr": {
        "garbage": "Ordures",
        "recycling": "Récupération",
        "food_residues": "Résidus alimentaires",
        "wooden_bulky_items": "Encombrants en bois",
        "branches": "Branches et résidus de coupe d’arbres",
        "green_waste": "Résidus verts",
        "fir_trees": "Sapins",
        "surplus_recovery": "Surplus de récupération"
    },
    "en": {
        "garbage": "Garbage",
        "recycling": "Recycling",
        "food_residues": "Food residues",
        "wooden_bulky_items": "Wooden bulky items",
        "branches": "Branches and tree trimmings",
        "green_waste": "Green waste",
        "fir_trees": "Fir trees",
        "surplus_recovery": "Surplus recovery"
    }
}

def get_internal_key(title: str) -> Optional[str]:
    """Identify the internal key from a website title."""
    # Try the current language first
    current_lang = Config.LANGUAGE
    # Priority: Current Config, then any other language available in WEB_TITLES
    langs = [current_lang] + [l for l in WEB_TITLES.keys() if l != current_lang]
    
    for lang in langs:
        mapping = WEB_TITLES.get(lang, {})
        for key, web_title in mapping.items():
            if web_title.lower() in title.lower():
                return key
    return None

def fetch_web_page() -> Optional[str]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=True
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        
        response = session.get(Config.WEB_URL, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch web data: {e}")
        return None

def parse_web_page(html_content: Optional[str]) -> Dict[str, Dict[str, Any]]:
    if not html_content:
        return {}

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get all possible keys from WEB_TITLES
        all_keys = set()
        for lang_map in WEB_TITLES.values():
            all_keys.update(lang_map.keys())

        next_collections: Dict[str, Dict[str, Any]] = {
            key: {"next_date": None, "collection_days": "Unknown"} 
            for key in all_keys
        }
        
        cards = soup.find_all("div", class_="collect-card")
        if not cards:
            logger.warning("No collection cards found in HTML.")
            return next_collections

        for card in cards:
            title_tag = card.find("h4")
            if not title_tag:
                continue
            
            title_span = title_tag.find("span", class_="span-title")
            if not title_span:
                continue
            
            title = title_span.get_text(strip=True)
            en_key = get_internal_key(title)
            
            if en_key:
                # Find the items inside the card
                items = card.find_all("div", class_="card-collect-item")
                for item in items:
                    label_span = item.find("span", class_="span-title")
                    if not label_span:
                        continue
                    
                    label_text = label_span.get_text()
                    
                    if "Collection days" in label_text or "Jours de passage" in label_text:
                        # Collection days are usually in a sibling div or nested span
                        # Based on curl: it's in a sibling div containing a span with class "mx-2"
                        # Structure: 
                        # <div class="days card-collect-item">
                        #   <div><span>Collection days:</span></div>
                        #   <div><span>Value</span></div>
                        # </div>
                        
                        # If the label_span is inside a div, we want the next sibling of THAT div
                        parent_div = label_span.find_parent("div")
                        if parent_div and parent_div.parent == item:
                            val_div = parent_div.find_next_sibling("div")
                        else:
                            val_div = item.find_next_sibling("div")

                        if val_div:
                            days_text = val_div.get_text(strip=True)
                            if days_text:
                                next_collections[en_key]["collection_days"] = days_text

                    elif "Next collection" in label_text or "Prochaine collecte" in label_text:
                        date_span = item.find("span", class_="info")
                        if not date_span:
                            # Sometimes it's in a sibling div
                            val_div = item.find_next_sibling("div")
                            if val_div:
                                date_span = val_div.find("span", class_="info")
                        
                        if date_span:
                            date_str = date_span.get_text(strip=True)
                            try:
                                # Date format is DD/MM/YYYY
                                next_date = datetime.strptime(date_str, "%d/%m/%Y").replace(tzinfo=ZoneInfo("America/Toronto"))
                                current_next = next_collections[en_key]["next_date"]
                                if current_next is None or next_date < current_next:
                                    next_collections[en_key]["next_date"] = next_date
                            except ValueError as ve:
                                logger.error(f"Failed to parse date string '{date_str}' for '{title}': {ve}")

        return next_collections
    except Exception as e:
        logger.error(f"Failed to parse web data: {e}")
        return {}

def save_cache(next_dates: Dict[str, Dict[str, Any]]) -> None:
    # Convert datetimes to strings for JSON
    serializable_data = {}
    for k, v in next_dates.items():
        serializable_data[k] = {
            "next_date": v["next_date"].isoformat() if v["next_date"] else None,
            "collection_days": v["collection_days"]
        }
    
    cache_data = {
        "timestamp": time.time(),
        "sector": Config.BROSSARD_SECTOR,
        "data": serializable_data
    }
    try:
        with open(Config.CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
        logger.info(f"Cache saved to {Config.CACHE_FILE}")
    except Exception as e:
        logger.error(f"Failed to save cache: {e}")

def load_cache_raw() -> Optional[Dict[str, Any]]:
    if not os.path.exists(Config.CACHE_FILE):
        return None
    
    try:
        with open(Config.CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        # Check if cache is for the same sector
        if cache_data.get("sector") != Config.BROSSARD_SECTOR:
            return None
            
        # Convert strings back to datetimes
        parsed_data: Dict[str, Dict[str, Any]] = {}
        for k, v in cache_data.get("data", {}).items():
            if isinstance(v, dict):
                # New format
                parsed_data[k] = {
                    "next_date": datetime.fromisoformat(v["next_date"]) if v.get("next_date") else None,
                    "collection_days": v.get("collection_days", "Unknown")
                }
            else:
                # Compatibility with old format (v was just a string)
                parsed_data[k] = {
                    "next_date": datetime.fromisoformat(v) if v else None,
                    "collection_days": "Unknown"
                }
        
        return {
            "timestamp": cache_data.get("timestamp", 0),
            "data": parsed_data
        }
    except Exception as e:
        logger.error(f"Failed to load raw cache: {e}")
        return None

def load_cache() -> Optional[Dict[str, Dict[str, Any]]]:
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
        if v["next_date"] and v["next_date"].date() < today:
            logger.info("Cache contains past dates, forcing refresh")
            return None
            
    logger.info("Using cached collection data")
    return next_dates

def get_next_collections(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    from datetime import timedelta
    
    if not force_refresh:
        cached_data = load_cache()
        if cached_data is not None:
            return cached_data
    
    logger.info("Fetching fresh collection data from website")
    content = fetch_web_page()
    web_data = parse_web_page(content)
    
    if not web_data:
        # If fetch failed, return whatever we have in cache even if stale
        raw_cache = load_cache_raw()
        return raw_cache["data"] if raw_cache else {}

    # Merge with raw cache to preserve "today's" or "tomorrow's" dates
    raw_cache = load_cache_raw()
    final_data: Dict[str, Dict[str, Any]] = {}
    
    now = datetime.now(ZoneInfo("America/Toronto"))
    today = now.date()
    tomorrow = (now + timedelta(days=1)).date()
    
    cached_dates = raw_cache["data"] if raw_cache else {}
    
    for key in web_data.keys():
        web_item = web_data.get(key, {"next_date": None, "collection_days": "Unknown"})
        cached_item = cached_dates.get(key, {"next_date": None, "collection_days": "Unknown"})
        
        cached_date = cached_item.get("next_date")
        
        # Preservation logic: if we have an imminent collection in cache that the website 
        # already skipped, preserve it.
        if cached_date and (cached_date.date() == today or cached_date.date() == tomorrow):
            # If web says a DIFFERENT future date, preserve the one from cache
            web_date = web_item.get("next_date")
            if web_date and web_date.date() > cached_date.date():
                final_data[key] = cached_item
                logger.info(f"Preserving imminent collection for {key}: {cached_date.date()}")
                continue
        
        final_data[key] = web_item
            
    save_cache(final_data)
    return final_data
