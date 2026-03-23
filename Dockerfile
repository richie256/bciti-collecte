# Use a slim Python image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl procps

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables with defaults
ENV MQTT_BROKER=mqtt.titan.home.interstellarbagel.xyz
ENV MQTT_PORT=1883
ENV BROSSARD_SECTOR=m
ENV UPDATE_INTERVAL=3600

ENV TZ=America/Montreal
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

# Run as a non-root user for security
RUN useradd -m scraperuser
USER scraperuser

# Start the application
CMD ["python", "main.py"]
