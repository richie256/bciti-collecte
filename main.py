import time
import logging
import signal
import sys
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

# Initialize MQTT Client
mqtt_client = MQTTClient()

def job():
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

def signal_handler(sig, frame):
    logger.info("Shutting down...")
    mqtt_client.stop()
    sys.exit(0)

def main():
    # Register signal handlers for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info(f"Starting Brossard Web Scraper for Sector {Config.BROSSARD_SECTOR.upper()}")
    
    # Connect to MQTT
    mqtt_client.connect()

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
        time.sleep(1)

if __name__ == "__main__":
    main()
