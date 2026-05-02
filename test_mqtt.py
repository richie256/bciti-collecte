import pytest
import json
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
            # _on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict[str, Any], reason_code: mqtt.ReasonCode, properties: Any)
            client._on_connect(mock_client, None, {}, 0, None)
            mock_client.publish.assert_called_once_with(client.availability_topic, payload="online", retain=True)
            mock_publish_discovery.assert_called_once()

def test_on_connect_failure():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        client = MQTTClient()
        with patch.object(client, 'publish_discovery') as mock_publish_discovery:
            client._on_connect(mock_client, None, {}, 1, None)
            mock_client.publish.assert_not_called()
            mock_publish_discovery.assert_not_called()

def test_on_disconnect():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        client = MQTTClient()
        client._on_disconnect(None, None, {}, 1, None)

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
        payload = json.loads(first_call[0][1])
        assert f"{Config.HASS_DISCOVERY_PREFIX}/sensor/brossard_{Config.BROSSARD_SECTOR}_garbage/config" in topic
        assert "json_attributes_topic" in payload
        assert payload["json_attributes_topic"].endswith("/attributes")

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
            "garbage": {"next_date": datetime(2026, 4, 10), "collection_days": "Friday"},
            "recycling": {"next_date": None, "collection_days": "Unknown"}
        }
        client.publish_states(next_dates)
        
        # garbage: state + availability + attributes = 3 calls; recycling: availability only = 1 call
        assert mock_client.publish.call_count == 4

        # Garbage state should be published as date string
        garbage_state_call = [c for c in mock_client.publish.call_args_list if "garbage/state" in c[0][0]][0]
        assert garbage_state_call[0][1] == "2026-04-10"

        # Garbage availability should be "online"
        garbage_avail_call = [c for c in mock_client.publish.call_args_list if "garbage/availability" in c[0][0]][0]
        assert garbage_avail_call[0][1] == "online"

        # Garbage attributes should have collection_days
        garbage_attr_call = [c for c in mock_client.publish.call_args_list if "garbage/attributes" in c[0][0]][0]
        attr_payload = json.loads(garbage_attr_call[0][1])
        assert attr_payload["collection_days"] == "Friday"

        # Recycling has no date: only availability "offline" should be published, no state
        recycling_avail_call = [c for c in mock_client.publish.call_args_list if "recycling/availability" in c[0][0]][0]
        assert recycling_avail_call[0][1] == "offline"
        assert not any("recycling/state" in c[0][0] for c in mock_client.publish.call_args_list)

def test_publish_states_exception():
    from datetime import datetime
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.publish.side_effect = Exception("Publish error")
        client = MQTTClient()
        client.publish_states({"garbage": {"next_date": datetime(2026, 4, 10), "collection_days": "X"}}) # Should catch exception

def test_stop():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        client = MQTTClient()
        client.stop()
        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()

def test_on_message():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        client = MQTTClient()
        msg = MagicMock()
        msg.topic = client.ha_status_topic
        msg.payload = b"online"
        client._on_message(None, None, msg)
        assert client.ha_status == "online"

        msg.topic = client.ha_language_topic
        msg.payload = b"en"
        client._on_message(None, None, msg)
        assert client.ha_language == "en"

def test_ha_birth_message_triggers_callback():
    callback_mock = MagicMock()
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        client = MQTTClient(on_ha_online=callback_mock)
        
        # Simulate HA coming online
        msg = MagicMock()
        msg.topic = client.ha_status_topic
        msg.payload = b"online"
        
        # Initial state is None, so switching to online should trigger callback
        client._on_message(None, None, msg)
        assert client.ha_status == "online"
        callback_mock.assert_called_once()
        
        callback_mock.reset_mock()
        # Sending online again should NOT trigger callback
        client._on_message(None, None, msg)
        callback_mock.assert_not_called()
        
        # Transitioning away and then back to online should trigger it again
        msg.payload = b"offline"
        client._on_message(None, None, msg)
        
        msg.payload = b"online"
        client._on_message(None, None, msg)
        callback_mock.assert_called_once()

def test_wait_for_ha_config_success():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        client = MQTTClient()
        client.ha_status = "online"
        client.ha_language = "en"
        
        with patch('config.Config.set_language') as mock_set_lang:
            client.wait_for_ha_config(timeout=0.1)
            mock_set_lang.assert_called_with("en")

def test_wait_for_ha_config_timeout():
    with patch('paho.mqtt.client.Client') as mock_client_cls:
        client = MQTTClient()
        # Should just return after timeout
        client.wait_for_ha_config(timeout=0.1)
