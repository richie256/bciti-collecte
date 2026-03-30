import paho.mqtt.client as mqtt
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

TRANSLATIONS = {
    "fr": {
        "garbage": "Déchets",
        "recycling": "Recyclage",
        "food_residues": "Résidus alimentaires",
        "wooden_bulky_items": "Encombrants boisés",
        "branches": "Branches et retailles de haie",
        "green_waste": "Résidus verts",
        "fir_trees": "Sapins de Noël",
        "surplus_recovery": "Récupération des surplus",
        "device_name": "Collectes de Brossard",
        "manufacturer": "Ville de Brossard",
        "sector": "Secteur"
    },
    "en": {
        "garbage": "Garbage",
        "recycling": "Recycling",
        "food_residues": "Food Residues",
        "wooden_bulky_items": "Wooden Bulky Items",
        "branches": "Branches and Tree Trimmings",
        "green_waste": "Green Waste",
        "fir_trees": "Fir Trees",
        "surplus_recovery": "Surplus Recovery",
        "device_name": "Brossard Collections",
        "manufacturer": "City of Brossard",
        "sector": "Sector"
    }
}

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        if Config.MQTT_USERNAME and Config.MQTT_PASSWORD:
            self.client.username_pw_set(Config.MQTT_USERNAME, Config.MQTT_PASSWORD)
        
        if Config.MQTT_USE_TLS:
            self.client.tls_set()
        
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
        lang = Config.LANGUAGE if Config.LANGUAGE in TRANSLATIONS else "fr"
        t = TRANSLATIONS[lang]

        # (key, icon)
        categories = [
            ("garbage", "mdi:delete"),
            ("recycling", "mdi:recycle"),
            ("food_residues", "mdi:food-apple"),
            ("wooden_bulky_items", "mdi:sofa"),
            ("branches", "mdi:tree"),
            ("green_waste", "mdi:leaf"),
            ("fir_trees", "mdi:pine-tree"),
            ("surplus_recovery", "mdi:archive-arrow-down")
        ]
        
        device = {
            "identifiers": [f"brossard_collections_{Config.BROSSARD_SECTOR}"],
            "name": f"{t['device_name']} ({t['sector']} {Config.BROSSARD_SECTOR.upper()})",
            "manufacturer": t["manufacturer"],
            "model": "Scraper"
        }

        for en_key, icon in categories:
            display_name = t.get(en_key, en_key.replace("_", " ").title())
            discovery_topic = f"homeassistant/sensor/brossard_{Config.BROSSARD_SECTOR}_{en_key}/config"
            payload = {
                "name": f"{display_name}",
                "state_topic": f"homeassistant/sensor/brossard_{Config.BROSSARD_SECTOR}_{en_key}/state",
                "unique_id": f"brossard_{Config.BROSSARD_SECTOR}_{en_key}",
                "device_class": "date",
                "icon": icon,
                "device": device
            }
            try:
                self.client.publish(discovery_topic, json.dumps(payload), retain=True)
                logger.info(f"Published discovery for {en_key}")
            except Exception as e:
                logger.error(f"Failed to publish discovery for {en_key}: {e}")

    def publish_states(self, next_dates):
        for en_key, event_date in next_dates.items():
            state_topic = f"homeassistant/sensor/brossard_{Config.BROSSARD_SECTOR}_{en_key}/state"
            if event_date:
                # Format to ISO 8601 date string (YYYY-MM-DD)
                state_value = event_date.date().isoformat()
            else:
                state_value = "unknown"
                
            try:
                self.client.publish(state_topic, state_value, retain=True)
                logger.info(f"Published state for {en_key}: {state_value}")
            except Exception as e:
                logger.error(f"Failed to publish state for {en_key}: {e}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
