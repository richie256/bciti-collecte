import pytest
from unittest.mock import MagicMock, patch
from mqtt import MQTTClient
from config import Config

def test_mqtt_client_init():
    with patch('paho.mqtt.client.Client') as mock_client:
        with patch('config.Config.MQTT_USERNAME', 'user'), patch('config.Config.MQTT_PASSWORD', 'pass'), patch('config.Config.MQTT_USE_TLS', True):
            client = MQTTClient()
            assert client.availability_topic == f"{Config.HASS_DISCOVERY_PREFIX}/sensor/brossard_{Config.BROSSARD_SECTOR}/availability"
            mock_client.return_value.username_pw_set.assert_called_once_with('user', 'pass')
            mock_client.return_value.tls_set.assert_called_once()
            mock_client.return_value.will_set.assert_called_once()

def test_on_connect_success():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        client = MQTTClient()
        with patch.object(client, 'publish_discovery') as mock_publish_discovery:
            client._on_connect(mock_client, None, {}, 0)
            mock_client.publish.assert_called_once_with(client.availability_topic, payload="online", retain=True)
            mock_publish_discovery.assert_called_once()

def test_on_connect_failure():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        client = MQTTClient()
        with patch.object(client, 'publish_discovery') as mock_publish_discovery:
            client._on_connect(mock_client, None, {}, 1)
            mock_client.publish.assert_not_called()
            mock_publish_discovery.assert_not_called()

def test_on_disconnect():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        client = MQTTClient()
        client._on_disconnect(None, None, 1)

def test_connect():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        client = MQTTClient()
        client.connect()
        mock_client.connect.assert_called_once()
        mock_client.loop_start.assert_called_once()

def test_connect_exception():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.connect.side_effect = Exception("Connect error")
        client = MQTTClient()
        client.connect() # Should catch exception

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

def test_publish_discovery_exception():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.publish.side_effect = Exception("Publish error")
        client = MQTTClient()
        client.publish_discovery() # Should catch exception

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

def test_publish_states_exception():
    from datetime import datetime
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.publish.side_effect = Exception("Publish error")
        client = MQTTClient()
        client.publish_states({"garbage": datetime(2026, 4, 10)}) # Should catch exception

def test_stop():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        client = MQTTClient()
        client.stop()
        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()
