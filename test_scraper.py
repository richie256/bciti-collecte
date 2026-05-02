import pytest
import os
import time
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from scraper import parse_web_page, fetch_web_page, save_cache, load_cache_raw, load_cache, get_next_collections
from config import Config

SAMPLE_HTML = """
<div class="collect-card">
    <h4><span class="span-title">Garbage Collection</span></h4>
    <div class="days card-collect-item">
        <span class="span-title">Collection days:</span>
    </div>
    <div>
        <span class="mx-2">Friday</span>
    </div>
    <div class="card-collect-item">
        <span class="span-title">Next collection:</span>
        <span class="info">10/04/2026</span>
    </div>
</div>
<div class="collect-card">
    <h4><span class="span-title">Recycling</span></h4>
    <div class="days card-collect-item">
        <span class="span-title">Collection days:</span>
    </div>
    <div>
        <span class="mx-2">Thursday</span>
    </div>
    <div class="card-collect-item">
        <span class="span-title">Next collection:</span>
        <span class="info">11/04/2026</span>
    </div>
</div>
<div class="collect-card">
    <h4><span class="span-title">Invalid Date</span></h4>
    <div class="card-collect-item">
        <span class="span-title">Next collection:</span>
        <span class="info">invalid-date</span>
    </div>
</div>
"""

def test_parse_web_page():
    # Test partial match with "Garbage Collection" matching "Garbage"
    # Also include a card that won't match any key
    html = SAMPLE_HTML + """
<div class="collect-card">
    <h4><span class="span-title">Unknown Collection</span></h4>
    <div class="card-collect-item">
        <span class="span-title">Next collection:</span>
        <span class="info">12/04/2026</span>
    </div>
</div>
"""
    results = parse_web_page(html)
    assert results["garbage"]["next_date"] == datetime(2026, 4, 10, tzinfo=ZoneInfo("America/Toronto"))
    assert results["garbage"]["collection_days"] == "Friday"
    assert results["recycling"]["next_date"] == datetime(2026, 4, 11, tzinfo=ZoneInfo("America/Toronto"))
    assert results["recycling"]["collection_days"] == "Thursday"
    assert results["food_residues"]["next_date"] is None

def test_parse_web_page_exception():
    with patch('scraper.BeautifulSoup', side_effect=Exception("BS error")):
        results = parse_web_page("<html></html>")
        assert results == {}

def test_parse_web_page_missing_tags():
    html = """
<div class="collect-card">
    <!-- Missing h4 -->
</div>
<div class="collect-card">
    <h4><!-- Missing span --></h4>
</div>
<div class="collect-card">
    <h4><span class="span-title">Garbage</span></h4>
    <div class="card-collect-item">
        <span class="span-title">Next collection:</span>
        <span class="info">invalid-date</span>
    </div>
</div>
"""
    results = parse_web_page(html)
    assert results["garbage"]["next_date"] is None

def test_parse_web_page_partial_match():
    html = """
<div class="collect-card">
    <h4><span class="span-title">Garbage Collection</span></h4>
    <div class="card-collect-item">
        <span class="span-title">Next collection:</span>
        <span class="info">10/04/2026</span>
    </div>
</div>
"""
    results = parse_web_page(html)
    assert results["garbage"]["next_date"] == datetime(2026, 4, 10, tzinfo=ZoneInfo("America/Toronto"))

def test_parse_web_page_none_content():
    assert parse_web_page(None) == {}
    assert parse_web_page("") == {}

def test_parse_web_page_no_cards():
    results = parse_web_page("<html><body>No cards here</body></html>")
    for key in results:
        assert results[key]["next_date"] is None

@patch('scraper.requests.Session')
def test_fetch_web_page_success(mock_session_cls):
    mock_session = mock_session_cls.return_value
    mock_response = MagicMock()
    mock_response.text = "<html></html>"
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response
    
    result = fetch_web_page()
    assert result == "<html></html>"

@patch('scraper.requests.Session')
def test_fetch_web_page_failure(mock_session_cls):
    mock_session = mock_session_cls.return_value
    mock_session.get.side_effect = Exception("Network error")
    result = fetch_web_page()
    assert result is None

def test_cache_operations(tmp_path):
    cache_file = tmp_path / "cache.json"
    with patch('config.Config.CACHE_FILE', str(cache_file)):
        # Test save_cache
        test_dates = {
            "garbage": {"next_date": datetime(2030, 4, 10, tzinfo=ZoneInfo("America/Toronto")), "collection_days": "Friday"},
            "recycling": {"next_date": None, "collection_days": "Unknown"}
        }
        save_cache(test_dates)
        assert os.path.exists(cache_file)
        
        # Test load_cache_raw
        raw = load_cache_raw()
        assert raw["data"]["garbage"]["next_date"] == datetime(2030, 4, 10, tzinfo=ZoneInfo("America/Toronto"))
        assert raw["data"]["garbage"]["collection_days"] == "Friday"
        assert raw["data"]["recycling"]["next_date"] is None
        
        # Test load_cache (not expired)
        loaded = load_cache()
        assert loaded == test_dates
        
        # Test load_cache (expired)
        with patch('time.time', return_value=time.time() + 86400):
            assert load_cache() is None

        # Test sector mismatch
        with patch('config.Config.BROSSARD_SECTOR', 'other'):
            assert load_cache_raw() is None

def test_load_cache_past_dates(tmp_path):
    cache_file = tmp_path / "cache.json"
    with patch('config.Config.CACHE_FILE', str(cache_file)):
        past_date = datetime(2000, 1, 1, tzinfo=ZoneInfo("America/Toronto"))
        save_cache({"garbage": {"next_date": past_date, "collection_days": "X"}})
        assert load_cache() is None

def test_load_cache_no_file(tmp_path):
    cache_file = tmp_path / "nonexistent.json"
    with patch('config.Config.CACHE_FILE', str(cache_file)):
        assert load_cache_raw() is None
        assert load_cache() is None

def test_save_cache_exception():
    with patch('builtins.open', side_effect=Exception("Open error")):
        save_cache({}) # Should catch exception

def test_load_cache_raw_exception(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text("invalid json")
    with patch('config.Config.CACHE_FILE', str(cache_file)):
        assert load_cache_raw() is None

def test_get_next_collections_cached():
    with patch('scraper.load_cache') as mock_load:
        mock_load.return_value = {"garbage": {"next_date": "some-date", "collection_days": "X"}}
        assert get_next_collections() == {"garbage": {"next_date": "some-date", "collection_days": "X"}}

def test_get_next_collections_fresh():
    with patch('scraper.load_cache', return_value=None):
        with patch('scraper.fetch_web_page', return_value=SAMPLE_HTML):
            with patch('scraper.save_cache') as mock_save:
                with patch('scraper.load_cache_raw', return_value=None):
                    results = get_next_collections()
                    assert results["garbage"]["next_date"] == datetime(2026, 4, 10, tzinfo=ZoneInfo("America/Toronto"))
                    mock_save.assert_called_once()

def test_get_next_collections_tomorrow_preservation():
    # Today is April 8, tomorrow is April 9
    today = datetime(2026, 4, 8, 12, 0, 0, tzinfo=ZoneInfo("America/Toronto"))
    tomorrow = today + timedelta(days=1)
    
    cached_data = {
        "recycling": {"next_date": tomorrow, "collection_days": "Thursday"}
    }
    
    # Web returns a future date (skipping tomorrow)
    web_data = {
        "recycling": {"next_date": today + timedelta(days=15), "collection_days": "Thursday"}
    }
    
    with patch('scraper.load_cache', return_value=None):
        with patch('scraper.fetch_web_page', return_value="<html></html>"):
            with patch('scraper.parse_web_page', return_value=web_data):
                with patch('scraper.load_cache_raw') as mock_load_raw:
                    mock_load_raw.return_value = {
                        "data": cached_data,
                        "timestamp": time.time()
                    }
                    with patch('scraper.datetime') as mock_datetime:
                        mock_datetime.now.return_value = today
                        mock_datetime.strptime = datetime.strptime
                        mock_datetime.fromisoformat = datetime.fromisoformat
                        
                        results = get_next_collections()
                        # Should preserve tomorrow's date
                        assert results["recycling"]["next_date"].date() == tomorrow.date()

def test_get_next_collections_fetch_failed_with_cache():
    with patch('scraper.load_cache', return_value=None):
        with patch('scraper.fetch_web_page', return_value=None):
            with patch('scraper.load_cache_raw') as mock_load_raw:
                mock_load_raw.return_value = {
                    "data": {"garbage": "cached-date"},
                    "timestamp": time.time()
                }
                assert get_next_collections() == {"garbage": "cached-date"}

def test_parse_web_page_recycling_specific():
    html = """
<div class="collect-card info-outline p-3 my-3">
    <div class="col-12">
        <div class="content">
            <div class="d-flex justify-content-between align-items-center">
                <h4>
                <i data-lucide="" aria-hidden="true"></i>
                <span class="ms-2 span-title">Recycling</span>
                </h4>
            </div>
            <div class="days card-collect-item">
                <div>
                    <i data-lucide="calendar-days" width="20" height="20" color="#231E20" aria-hidden="true"></i>
                    <span class="ms-2 span-title">Collection days:</span>
                </div>
                <div>
                    <span class="mx-2">Thursday, once every two weeks</span>
                </div>
            </div>
            <div class="days card-collect-item">
                <div>
                <i data-lucide="calendar-days" width="20" height="20" color="#231E20" aria-hidden="true"></i>
                <span class="ms-2 span-title">Next collection:</span>
                </div>
                <div>
                <span class="info me-2">23/04/2026 </span>
                </div>
            </div>
        </div>
    </div>
</div>
"""
    results = parse_web_page(html)
    assert results["recycling"]["next_date"] == datetime(2026, 4, 23, tzinfo=ZoneInfo("America/Toronto"))
    assert results["recycling"]["collection_days"] == "Thursday, once every two weeks"

def test_parse_web_page_french():
    html = """
<div class="collect-card info-outline p-3 my-3">
    <div class="col-12">
        <div class="content">
            <div class="d-flex justify-content-between align-items-center">
                <h4>
                <i data-lucide="recycle" aria-hidden="true"></i>
                <span class="ms-2 span-title">Recyclage</span>
                </h4>
            </div>
            <div class="days card-collect-item">
                <div>
                    <i data-lucide="calendar-days" width="20" height="20" color="#231E20" aria-hidden="true"></i>
                    <span class="ms-2 span-title">Jours de passage :</span>
                </div>
                <div>
                    <span class="mx-2">Jeudi, une fois aux deux semaines</span>
                </div>
            </div>
            <div class="days card-collect-item">
                <div>
                <i data-lucide="calendar-days" width="20" height="20" color="#231E20" aria-hidden="true"></i>
                <span class="ms-2 span-title">Prochaine collecte :</span>
                </div>
                <div>
                <span class="info me-2">23/04/2026 </span>
                </div>
            </div>
        </div>
    </div>
</div>
"""
    results = parse_web_page(html)
    assert results["recycling"]["next_date"] == datetime(2026, 4, 23, tzinfo=ZoneInfo("America/Toronto"))
    assert results["recycling"]["collection_days"] == "Jeudi, une fois aux deux semaines"
