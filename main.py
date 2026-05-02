import time
import logging
import signal
import sys
import os
import threading
from typing import Any
import schedule
from config import Config
from scraper import get_next_collections
from mqtt import MQTTClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Heartbeat file path for health check
HEARTBEAT_FILE = "/tmp/heartbeat"

# Lock for thread safety
job_lock = threading.Lock()

# Initialize MQTT Client
mqtt_client = MQTTClient(on_ha_online=lambda: job())

def touch_heartbeat() -> None:
    try:
        with open(HEARTBEAT_FILE, 'w') as f:
            f.write(str(time.time()))
    except Exception as e:
        logger.error(f"Failed to touch heartbeat file: {e}")

def job() -> None:
    with job_lock:
        logger.info("Starting collection schedule update job")
        next_dates = get_next_collections()
        logger.info(f"Data returned from scraper: {next_dates}")
        if next_dates:
            mqtt_client.publish_states(next_dates)
            logger.info("Successfully updated collection dates")
        else:
            logger.warning("No collection dates found or error occurred")
        
        next_interval_minutes = Config.UPDATE_INTERVAL / 60
        logger.info(f"Next update in approximately {next_interval_minutes:.0f} minutes.")
        # Also touch heartbeat when job completes
        touch_heartbeat()

def signal_handler(sig: int, frame: Any) -> None:
    logger.info("Shutting down...")
    if os.path.exists(HEARTBEAT_FILE):
        try:
            os.remove(HEARTBEAT_FILE)
        except Exception:
            pass
    mqtt_client.stop()
    sys.exit(0)

def main() -> None:
    # Register signal handlers for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if not Config.MQTT_HOST:
        logger.error("MQTT_HOST environment variable is not set.")
        sys.exit(1)

    logger.info(f"Starting Brossard Web Scraper for Sector {Config.BROSSARD_SECTOR.upper()}")

    # Initial heartbeat
    touch_heartbeat()

    # Connect to MQTT
    try:
        mqtt_client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker at {Config.MQTT_HOST}:{Config.MQTT_PORT}: {e}")
        sys.exit(1)

    # Wait for Home Assistant configuration (status/language)
    mqtt_client.wait_for_ha_config()

    # Initial run
    job()

    if Config.RUN_ONCE:
        logger.info("RUN_ONCE is enabled, exiting after initial job")
        mqtt_client.stop()
        sys.exit(0)

    # Schedule subsequent runs
    schedule.every(Config.UPDATE_INTERVAL).seconds.do(job)

    while True:
        schedule.run_pending()
        touch_heartbeat()
        time.sleep(1)

if __name__ == "__main__":
    main()
