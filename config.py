import os

class Config:
    MQTT_HOST: str = os.getenv("MQTT_HOST", "undef")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME: str | None = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD: str | None = os.getenv("MQTT_PASSWORD")
    BROSSARD_SECTOR: str = os.getenv("BROSSARD_SECTOR", "m").lower()
    UPDATE_INTERVAL: int = int(os.getenv("UPDATE_INTERVAL", 1800))
    LANGUAGE: str = os.getenv("LANGUAGE", "fr").lower()
    WEB_URL: str = "" # Initialized in set_language
    
    CACHE_FILE: str = os.getenv("CACHE_FILE", "/data/collections_cache.json")
    CACHE_MAX_AGE: int = int(os.getenv("CACHE_MAX_AGE", 43200))  # 12 hours in seconds
    RUN_ONCE: bool = os.getenv("RUN_ONCE", "false").lower() == "true"
    MQTT_USE_TLS: bool = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
    HASS_DISCOVERY_ENABLED: bool = os.getenv("HASS_DISCOVERY_ENABLED", "true").lower() == "true"
    HASS_DISCOVERY_PREFIX: str = os.getenv("HASS_DISCOVERY_PREFIX", "homeassistant")

    @classmethod
    def set_language(cls, lang: str) -> None:
        cls.LANGUAGE = lang.lower()
        if cls.LANGUAGE == "fr":
            cls.WEB_URL = f"https://brossard.ca/calendrier-collectes/secteur-{cls.BROSSARD_SECTOR}/"
        else:
            cls.WEB_URL = f"https://brossard.ca/en/collection-calendar/sector-{cls.BROSSARD_SECTOR}/"

# Initialize defaults
Config.set_language(Config.LANGUAGE)
