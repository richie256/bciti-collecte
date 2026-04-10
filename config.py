import os

class Config:
    MQTT_HOST: str = os.getenv("MQTT_HOST", "undef")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME: str | None = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD: str | None = os.getenv("MQTT_PASSWORD")
    BROSSARD_SECTOR: str = os.getenv("BROSSARD_SECTOR", "m").lower()
    UPDATE_INTERVAL: int = int(os.getenv("UPDATE_INTERVAL", 1800))
    LANGUAGE: str = os.getenv("LANGUAGE", "fr").lower()
    
    if LANGUAGE == "fr":
        WEB_URL: str = f"https://brossard.ca/calendrier-collectes/secteur-{BROSSARD_SECTOR}/"
    else:
        WEB_URL: str = f"https://brossard.ca/en/collection-calendar/sector-{BROSSARD_SECTOR}/"
    
    CACHE_FILE: str = os.getenv("CACHE_FILE", "collections_cache.json")
    CACHE_MAX_AGE: int = int(os.getenv("CACHE_MAX_AGE", 43200))  # 12 hours in seconds
    RUN_ONCE: bool = os.getenv("RUN_ONCE", "false").lower() == "true"
    MQTT_USE_TLS: bool = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
    HASS_DISCOVERY_ENABLED: bool = os.getenv("HASS_DISCOVERY_ENABLED", "true").lower() == "true"
    HASS_DISCOVERY_PREFIX: str = os.getenv("HASS_DISCOVERY_PREFIX", "homeassistant")
