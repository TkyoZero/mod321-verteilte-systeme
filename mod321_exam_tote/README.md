# Sensor API

A service that reads the air sensor (DHT11: temperature, humidity) and the light sensor of the Joy-Pi case and provides the values as a JSON API.
Every incoming request sends an MQTT message to the broker `10.5.61.199` on the topic `raspi/12/http/request`.

## Folder structure

```
sensor-api/
  main.py               # HTTP server + MQTT
  index.html
  sensor/
    air_sensor.py
    light_sensor.py
docker-compose.yaml
lg.zip                  # lgpio library, compiled inside the Docker image
lgpio.Dockerfile
mosquitto.conf          # config for the mosquitto container
README.md
```

## Requirements

- RaspberryPi with the Joy-Pi case
- I2C is enabled (`sudo raspi-config` → Interface Options → I2C)
- Docker and Docker Compose are installed
- The Pi is on the same network as the broker `10.5.61.199`

## Start the service

1. Unzip the files and go into the folder:
   ```bash
   unzip mod321_exam_tote.zip -d mod321_exam_tote
   cd mod321_exam_tote
   ```
2. Start the Docker services:
   ```bash
   docker compose up --build -d
   ```
3. Show the logs (optional):
   ```bash
   docker compose logs -f
   ```

## Stop the service

```bash
docker compose down
```

## Test

```bash
curl http://<host>:5000/api/sensors
```

Example response:

```json
{
  "status": "ok",
  "data": [
    {"label": "Temperature", "value": 23.0, "unit": "°C"},
    {"label": "Humidity", "value": 45.0, "unit": "%"},
    {"label": "Illuminance", "value": 120.8, "unit": "lux"}
  ]
}
```

Other endpoints: `/` (overview), `/api/air`, `/api/light`.

Check the MQTT messages. The `mosquitto` container already contains `mosquitto_sub`, so nothing has to be installed:

```bash
docker compose exec mosquitto mosquitto_sub -h 10.5.61.199 -t "raspi/12/http/request" -v
```

Then send a request in a second terminal (see above). Each request shows up as one line.
