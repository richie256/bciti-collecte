import paho.mqtt.client as mqtt
import json
import logging
import time
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

TRANSLATIONS: Dict[str, Dict[str, str]] = {
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
    def __init__(self) -> None:
        self.client = mqtt.Client()
        self.availability_topic: str = f"{Config.HASS_DISCOVERY_PREFIX}/sensor/brossard_{Config.BROSSARD_SECTOR}/availability"
        self.ha_status_topic: str = f"{Config.HASS_DISCOVERY_PREFIX}/status"
        self.ha_language_topic: str = f"{Config.HASS_DISCOVERY_PREFIX}/system/language"
        
        self.ha_status: Optional[str] = None
        self.ha_language: Optional[str] = None

        if Config.MQTT_USERNAME and Config.MQTT_PASSWORD:
            self.client.username_pw_set(Config.MQTT_USERNAME, Config.MQTT_PASSWORD)
        
        if Config.MQTT_USE_TLS:
            self.client.tls_set()
        
        # Set Last Will and Testament
        self.client.will_set(self.availability_topic, payload="offline", retain=True)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict[str, int], rc: int) -> None:
        if rc == 0:
            logger.info("Connected to MQTT broker")
            # Subscribe to HA status and language
            self.client.subscribe([(self.ha_status_topic, 0), (self.ha_language_topic, 0)])
            # Publish availability
            self.client.publish(self.availability_topic, payload="online", retain=True)
            if Config.HASS_DISCOVERY_ENABLED:
                self.publish_discovery()
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            payload = msg.payload.decode()
            if msg.topic == self.ha_status_topic:
                self.ha_status = payload.lower()
                logger.debug(f"Received HA status: {self.ha_status}")
            elif msg.topic == self.ha_language_topic:
                self.ha_language = payload.lower()
                logger.debug(f"Received HA language: {self.ha_language}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def wait_for_ha_config(self, timeout: float = 5.0) -> None:
        """Wait for HA status and language messages."""
        logger.info("Waiting for Home Assistant configuration via MQTT...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.ha_status == "online":
                if self.ha_language:
                    logger.info(f"Home Assistant is online. Found language via MQTT: '{self.ha_language}'")
                    if self.ha_language != Config.LANGUAGE:
                        logger.info(f"Overriding local language '{Config.LANGUAGE}' with Home Assistant language '{self.ha_language}'")
                        Config.set_language(self.ha_language)
                        # Re-publish discovery in case language changed
                        if Config.HASS_DISCOVERY_ENABLED:
                            self.publish_discovery()
                    else:
                        logger.info(f"Home Assistant language matches local configuration ('{Config.LANGUAGE}'). No override needed.")
                    break
                # If we have status but no language yet, keep waiting a bit
            time.sleep(0.1)
        
        if self.ha_status != "online":
            logger.info(f"Home Assistant status is '{self.ha_status}' (not 'online'). Using local language: '{Config.LANGUAGE}'")
        elif not self.ha_language:
            logger.info(f"Home Assistant language not received within {timeout}s. Using local language: '{Config.LANGUAGE}'")
        
        logger.info(f"Final language configuration: '{Config.LANGUAGE}' (URL: {Config.WEB_URL})")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        logger.info(f"Disconnected from MQTT broker with code {rc}")

    def connect(self) -> None:
        try:
            self.client.connect(Config.MQTT_HOST, Config.MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Error connecting to MQTT: {e}")

    def publish_discovery(self) -> None:
        lang = Config.LANGUAGE if Config.LANGUAGE in TRANSLATIONS else "fr"
        t = TRANSLATIONS[lang]

        # (key, icon)
        categories: List[Tuple[str, str]] = [
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
            discovery_topic = f"{Config.HASS_DISCOVERY_PREFIX}/sensor/brossard_{Config.BROSSARD_SECTOR}_{en_key}/config"
            base_topic = f"{Config.HASS_DISCOVERY_PREFIX}/sensor/brossard_{Config.BROSSARD_SECTOR}_{en_key}"
            payload = {
                "name": f"{display_name}",
                "state_topic": f"{base_topic}/state",
                "json_attributes_topic": f"{base_topic}/attributes",
                "unique_id": f"brossard_{Config.BROSSARD_SECTOR}_{en_key}",
                "device_class": "date",
                "icon": icon,
                "availability_topic": self.availability_topic,
                "device": device
            }
            try:
                self.client.publish(discovery_topic, json.dumps(payload), retain=True)
                logger.info(f"Published discovery for {en_key}")
            except Exception as e:
                logger.error(f"Failed to publish discovery for {en_key}: {e}")

    def publish_states(self, next_dates: Dict[str, Dict[str, Any]]) -> None:
        for en_key, data in next_dates.items():
            base_topic = f"{Config.HASS_DISCOVERY_PREFIX}/sensor/brossard_{Config.BROSSARD_SECTOR}_{en_key}"
            state_topic = f"{base_topic}/state"
            attr_topic = f"{base_topic}/attributes"
            
            event_date = data.get("next_date")
            collection_days = data.get("collection_days", "Unknown")
            
            if event_date:
                # Format to ISO 8601 date string (YYYY-MM-DD)
                state_value = event_date.date().isoformat()
            else:
                state_value = "unknown"
                
            try:
                # Publish state
                self.client.publish(state_topic, state_value, retain=True)
                
                # Publish attributes
                attr_payload = {"collection_days": collection_days}
                self.client.publish(attr_topic, json.dumps(attr_payload), retain=True)
                
                logger.info(f"Published state for {en_key}: {state_value} (Days: {collection_days})")
            except Exception as e:
                logger.error(f"Failed to publish state or attributes for {en_key}: {e}")

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
