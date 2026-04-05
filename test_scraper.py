import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from zoneinfo import ZoneInfo
from scraper import parse_web_page, fetch_web_page

SAMPLE_HTML = """
<div class="collect-card">
    <h4><span class="span-title">Garbage</span></h4>
    <div class="card-collect-item">
        <span class="span-title">Next collection:</span>
        <span class="info">10/04/2026</span>
    </div>
</div>
<div class="collect-card">
    <h4><span class="span-title">Recycling</span></h4>
    <div class="card-collect-item">
        <span class="span-title">Next collection:</span>
        <span class="info">11/04/2026</span>
    </div>
</div>
"""

def test_parse_web_page():
    results = parse_web_page(SAMPLE_HTML)
    assert results["garbage"] == datetime(2026, 4, 10, tzinfo=ZoneInfo("America/Toronto"))
    assert results["recycling"] == datetime(2026, 4, 11, tzinfo=ZoneInfo("America/Toronto"))
    assert results["food_residues"] is None

def test_parse_web_page_empty():
    results = parse_web_page("")
    assert results == {}
    
    results = parse_web_page(None)
    assert results == {}

def test_parse_web_page_no_cards():
    results = parse_web_page("<html><body>No cards here</body></html>")
    for key in results:
        assert results[key] is None

@patch('requests.Session.get')
def test_fetch_web_page_success(mock_get):
    mock_response = MagicMock()
    mock_response.text = "<html></html>"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    result = fetch_web_page()
    assert result == "<html></html>"

@patch('requests.Session.get')
def test_fetch_web_page_failure(mock_get):
    mock_get.side_effect = Exception("Network error")
    result = fetch_web_page()
    assert result is None
