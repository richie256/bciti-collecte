import pytest
from unittest.mock import MagicMock, patch
import main
from config import Config

def test_job():
    with patch('main.get_next_collections') as mock_get_next:
        with patch('main.mqtt_client') as mock_mqtt:
            mock_get_next.return_value = {"garbage": "2026-04-10"}
            main.job()
            mock_mqtt.publish_states.assert_called_once_with({"garbage": "2026-04-10"})

def test_job_no_dates():
    with patch('main.get_next_collections') as mock_get_next:
        with patch('main.mqtt_client') as mock_mqtt:
            mock_get_next.return_value = {}
            main.job()
            mock_mqtt.publish_states.assert_not_called()

def test_signal_handler():
    with patch('main.mqtt_client') as mock_mqtt:
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            main.signal_handler(15, None)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 0
        mock_mqtt.stop.assert_called_once()

def test_main_run_once():
    with patch('main.signal.signal') as mock_signal:
        with patch('main.mqtt_client') as mock_mqtt:
            with patch('main.job') as mock_job:
                with patch('main.Config.RUN_ONCE', True):
                    with pytest.raises(SystemExit) as pytest_wrapped_e:
                        main.main()
                    assert pytest_wrapped_e.type == SystemExit
                    assert pytest_wrapped_e.value.code == 0
                    mock_mqtt.connect.assert_called_once()
                    mock_job.assert_called_once()
                    mock_mqtt.stop.assert_called_once()

def test_main_loop():
    with patch('main.signal.signal'), \
         patch('main.mqtt_client'), \
         patch('main.job'), \
         patch('main.Config.RUN_ONCE', False), \
         patch('main.schedule.run_pending'), \
         patch('main.time.sleep', side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            main.main()
