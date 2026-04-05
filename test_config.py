import os
from unittest.mock import patch
from config import Config

def test_config_defaults():
    # Since Config is already imported and initialized, 
    # testing it directly might reflect environmental defaults.
    # We can test that it has the expected attributes and types.
    assert isinstance(Config.MQTT_PORT, int)
    assert isinstance(Config.BROSSARD_SECTOR, str)
    assert isinstance(Config.UPDATE_INTERVAL, int)
    assert isinstance(Config.HASS_DISCOVERY_ENABLED, bool)

def test_config_web_url():
    # Ensure web URL reflects the sector
    expected_url = f"https://brossard.ca/en/collection-calendar/sector-{Config.BROSSARD_SECTOR}/"
    assert Config.WEB_URL == expected_url
