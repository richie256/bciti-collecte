import os

class Config:
    MQTT_HOST = os.getenv("MQTT_HOST", "undef")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
    BROSSARD_SECTOR = os.getenv("BROSSARD_SECTOR", "m").lower()
    UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", 1800))
    WEB_URL = f"https://brossard.ca/en/collection-calendar/sector-{BROSSARD_SECTOR}/"
    CACHE_FILE = os.getenv("CACHE_FILE", "collections_cache.json")
    CACHE_MAX_AGE = int(os.getenv("CACHE_MAX_AGE", 43200))  # 12 hours in seconds
    RUN_ONCE = os.getenv("RUN_ONCE", "false").lower() == "true"
    MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
