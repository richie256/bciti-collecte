import paho.mqtt.client as mqtt
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        if Config.MQTT_USER and Config.MQTT_PASSWORD:
            self.client.username_pw_set(Config.MQTT_USER, Config.MQTT_PASSWORD)
        
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.publish_discovery()
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.info(f"Disconnected from MQTT broker with code {rc}")

    def connect(self):
        try:
            self.client.connect(Config.MQTT_HOST, Config.MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Error connecting to MQTT: {e}")

    def publish_discovery(self):
        # (key, display_name, icon)
        categories = [
            ("garbage", "Garbage", "mdi:delete"),
            ("recycling", "Recycling", "mdi:recycle"),
            ("food_residues", "Food Residues", "mdi:food-apple"),
            ("wooden_bulky_items", "Wooden Bulky Items", "mdi:sofa"),
            ("branches", "Branches and Tree Trimmings", "mdi:tree"),
            ("green_waste", "Green Waste", "mdi:leaf"),
            ("fir_trees", "Fir Trees", "mdi:pine-tree"),
            ("surplus_recovery", "Surplus Recovery", "mdi:archive-arrow-down")
        ]
        
        device = {
            "identifiers": [f"brossard_collections_{Config.BROSSARD_SECTOR}"],
            "name": f"Brossard Collections (Sector {Config.BROSSARD_SECTOR.upper()})",
            "manufacturer": "City of Brossard",
            "model": "Scraper"
        }

        for en_key, display_name, icon in categories:
            discovery_topic = f"homeassistant/sensor/brossard_{Config.BROSSARD_SECTOR}_{en_key}/config"
            payload = {
                "name": f"{display_name}",
                "state_topic": f"homeassistant/sensor/brossard_{Config.BROSSARD_SECTOR}_{en_key}/state",
                "unique_id": f"brossard_{Config.BROSSARD_SECTOR}_{en_key}",
                "device_class": "timestamp",
                "icon": icon,
                "device": device
            }
            self.client.publish(discovery_topic, json.dumps(payload), retain=True)
            logger.info(f"Published discovery for {en_key}")

    def publish_states(self, next_dates):
        for en_key, event_date in next_dates.items():
            state_topic = f"homeassistant/sensor/brossard_{Config.BROSSARD_SECTOR}_{en_key}/state"
            if event_date:
                # Format to ISO 8601 string
                state_value = event_date.isoformat()
            else:
                state_value = "unknown"
                
            self.client.publish(state_topic, state_value, retain=True)
            logger.info(f"Published state for {en_key}: {state_value}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
