import pytest
from unittest.mock import MagicMock, patch
from mqtt import MQTTClient
from config import Config

def test_mqtt_client_init():
    with patch('paho.mqtt.client.Client') as mock_client:
        client = MQTTClient()
        assert client.availability_topic == f"{Config.HASS_DISCOVERY_PREFIX}/sensor/brossard_{Config.BROSSARD_SECTOR}/availability"
        mock_client.return_value.will_set.assert_called_once()

def test_publish_discovery():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        client = MQTTClient()
        client.publish_discovery()
        
        # We expect 8 categories
        assert mock_client.publish.call_count == 8
        
        # Check first call discovery topic
        first_call = mock_client.publish.call_args_list[0]
        topic = first_call[0][0]
        assert f"{Config.HASS_DISCOVERY_PREFIX}/sensor/brossard_{Config.BROSSARD_SECTOR}_garbage/config" in topic

def test_publish_states():
    from datetime import datetime
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        client = MQTTClient()
        
        next_dates = {
            "garbage": datetime(2026, 4, 10),
            "recycling": None
        }
        client.publish_states(next_dates)
        
        # Garbage should be published as date string
        garbage_call = [c for c in mock_client.publish.call_args_list if "garbage/state" in c[0][0]][0]
        assert garbage_call[0][1] == "2026-04-10"
        
        # Recycling should be published as "unknown"
        recycling_call = [c for c in mock_client.publish.call_args_list if "recycling/state" in c[0][0]][0]
        assert recycling_call[0][1] == "unknown"
