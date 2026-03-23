# Brossard Collection Scraper

A Python-based web scraper that fetches waste collection schedules for the city of Brossard and publishes the next collection dates to an MQTT broker, specifically designed for Home Assistant integration.

## Project Overview

- **Purpose**: Automates the retrieval of garbage, recycling, and organic waste collection dates from the city of Brossard's website.
- **Main Technologies**:
  - **Python 3.10+**: Core language.
  - **BeautifulSoup4**: HTML parsing and data extraction.
  - **Paho-MQTT**: Communication with MQTT brokers.
  - **Requests**: HTTP client for fetching web pages.
  - **Schedule**: Manages periodic scraping tasks.
  - **Docker**: For containerized deployment.
- **Architecture**:
  - `main.py`: Entry point that initializes the MQTT client, performs an initial scrape, and schedules subsequent updates.
  - `scraper.py`: Contains logic for fetching the city's collection calendar, parsing the HTML to find the next dates for various categories, and handling local caching to `collections_cache.json`.
  - `mqtt.py`: Manages the MQTT connection, publishes Home Assistant discovery payloads, and updates sensor states with ISO 8601 timestamps.
  - `config.py`: Centralized configuration management using environment variables.

## Building and Running

### Prerequisites
- Python 3.10 or higher.
- An MQTT broker (e.g., Mosquitto) accessible from the application.

### Local Development
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   # Set environment variables as needed (see Configuration)
   python main.py
   ```
3. Run tests:
   ```bash
   python test_scraper.py
   ```

### Docker
1. Build the image:
   ```bash
   docker build -t brossard-collecte .
   ```
2. Run the container:
   ```bash
   docker run --env-file .env brossard-collecte
   ```

## Configuration

The application is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_BROKER` | Address of the MQTT broker | `mqtt.titan.home.interstellarbagel.xyz` |
| `MQTT_PORT` | Port for the MQTT broker | `1883` |
| `MQTT_USER` | Username for MQTT authentication | `None` |
| `MQTT_PASSWORD` | Password for MQTT authentication | `None` |
| `BROSSARD_SECTOR` | City sector to scrape (e.g., 'm', 'l', etc.) | `m` |
| `UPDATE_INTERVAL` | Interval between scrapes in seconds | `1800` |
| `CACHE_FILE` | Path to the local cache file | `collections_cache.json` |
| `CACHE_MAX_AGE` | Maximum age of cache in seconds before refresh | `43200` (12 hours) |
| `RUN_ONCE` | If `true`, exit after the first successful run | `false` |

## Development Conventions

- **Logging**: Use the standard `logging` library. Default format is set in `main.py`.
- **Error Handling**: Gracefully handle network failures and parsing errors; the application should retry according to the schedule.
- **MQTT Discovery**: Follows Home Assistant's MQTT discovery format for `timestamp` device classes.
- **Scraping**: The scraper targets `https://brossard.ca/en/collection-calendar/sector-{BROSSARD_SECTOR}/`. If the website structure changes, updates to `scraper.py` will be required.
