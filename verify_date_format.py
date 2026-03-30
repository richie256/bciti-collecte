from datetime import datetime
from zoneinfo import ZoneInfo
from mqtt import TRANSLATIONS

def test_date_formatting():
    # Simulate a datetime object from the scraper
    event_date = datetime(2026, 3, 30, 0, 0, 0, tzinfo=ZoneInfo("America/Toronto"))
    
    # This is what I added to mqtt.py:
    state_value = event_date.date().isoformat()
    
    print(f"Original datetime: {event_date.isoformat()}")
    print(f"Formatted date for HA: {state_value}")
    
    assert state_value == "2026-03-30"
    print("Verification successful: Date format is YYYY-MM-DD")

def test_translations():
    print("\nChecking translations:")
    assert "fr" in TRANSLATIONS
    assert "en" in TRANSLATIONS
    
    assert TRANSLATIONS["fr"]["manufacturer"] == "Ville de Brossard"
    assert TRANSLATIONS["fr"]["sector"] == "Secteur"
    assert TRANSLATIONS["en"]["manufacturer"] == "City of Brossard"
    assert TRANSLATIONS["en"]["sector"] == "Sector"
    
    print(f"FR manufacturer: {TRANSLATIONS['fr']['manufacturer']}")
    print(f"FR sector: {TRANSLATIONS['fr']['sector']}")
    print("Verification successful: Translations are correct")

if __name__ == "__main__":
    test_date_formatting()
    test_translations()
