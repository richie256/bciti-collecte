# Brossard Collection Scraper

[![Build & Tests](https://github.com/richie256/bciti-collecte/actions/workflows/docker-build-push.yml/badge.svg)](https://github.com/richie256/bciti-collecte/actions/workflows/docker-build-push.yml)
![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/richie256/bciti-collecte)](https://github.com/richie256/bciti-collecte/releases)
[![GitHub License](https://img.shields.io/github/license/richie256/bciti-collecte)](https://github.com/richie256/bciti-collecte/blob/main/LICENSE)

A Python-based utility that scrapes waste collection schedules from the City of Brossard's website and publishes them to an MQTT broker. It is specifically designed for seamless integration with **Home Assistant** using MQTT Discovery.

## Features

- **Automated Scraping**: Fetches next collection dates for garbage, recycling, organic waste, and more.
- **Home Assistant Integration**: Automatically creates sensors in Home Assistant via MQTT Discovery with appropriate icons and `date` device classes.
- **Multi-language Support**: Supports both French and English for sensor names.
- **Sector Based**: Configurable for any city sector (m, l, r, etc.).
- **Caching**: Local caching mechanism to reduce redundant web requests.
- **Dockerized**: Ready for deployment as a lightweight Docker container.

## Supported Collections

- Garbage (Déchets)
- Recycling (Recyclage)
- Food Residues (Résidus alimentaires)
- Wooden Bulky Items (Encombrants boisés)
- Branches (Branches et retailles de haie)
- Green Waste (Résidus verts)
- Fir Trees (Sapins de Noël)
- Surplus Recovery (Récupération des surplus)

## Configuration

The application is configured using environment variables. You can create a `.env` file based on `.env.example`.

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_HOST` | Hostname or IP of your MQTT broker | `undef` |
| `MQTT_PORT` | Port of your MQTT broker | `1883` |
| `MQTT_USERNAME` | Username for MQTT authentication | `None` |
| `MQTT_PASSWORD` | Password for MQTT authentication | `None` |
| `MQTT_USE_TLS` | Whether to use TLS for MQTT connection | `false` |
| `BROSSARD_SECTOR` | Your city sector (e.g., `m`, `l`, `r`) | `m` |
| `UPDATE_INTERVAL` | Interval between scrapes in seconds | `1800` (30 mins) |
| `CACHE_MAX_AGE` | Max age of local cache in seconds | `43200` (12 hours) |
| `LANGUAGE` | Sensor name language (`fr` or `en`) | `fr` |
| `RUN_ONCE` | Set to `true` to exit after one successful run | `false` |

## Installation & Usage

### Using Docker (Recommended)

```bash
docker run -d \
  --name brossard-collecte \
  -e MQTT_HOST="192.168.1.10" \
  -e BROSSARD_SECTOR="m" \
  -v $(pwd)/collections_cache.json:/app/collections_cache.json \
  rdubois/bciti-collecte:latest
```

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rdubois/bciti-collecte.git
   cd bciti-collecte
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables** and run:
   ```bash
   export MQTT_HOST="your-mqtt-broker"
   export BROSSARD_SECTOR="m"
   python main.py
   ```

## Development

### Running Tests
The project uses `pytest` for testing.
```bash
pytest
```

### Project Structure
- `main.py`: Entry point and task scheduler.
- `scraper.py`: Logic for parsing the city's website and extraction.
- `mqtt.py`: MQTT client handling discovery and state updates.
- `config.py`: Configuration management.

## License
MIT
