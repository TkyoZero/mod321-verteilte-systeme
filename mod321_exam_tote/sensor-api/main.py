from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import sleep
from sensor.air_sensor import AirSensor
from sensor.light_sensor import LightSensor
import mimetypes
import textwrap
import threading
import json
import os

import paho.mqtt.client as mqtt

air_sensor = AirSensor()
light_sensor = LightSensor()

# GPIO and I2C are shared hardware: only one thread may read at a time
sensor_lock = threading.Lock()

host = "0.0.0.0"
port = 8080

# Folder where this file lives
base_directory = os.path.dirname(os.path.abspath(__file__))

# MQTT settings
mqtt_broker_host = "10.5.61.199"
raspi_number = "12"
request_topic = f"raspi/{raspi_number}/http/request"

# MQTT client
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT broker with reason code {reason_code}")

def on_message(client, userdata, msg: object):
    print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect_async(mqtt_broker_host, 1883, 60)
mqtt_client.loop_start()

sleep(1)


class Server(BaseHTTPRequestHandler):
    response_started = False

    def end_headers(self):
        self.response_started = True
        super().end_headers()

    def sendCommonHeaders(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Vary", "Origin")

    def sendJSON(self, object: object, code: int = 200):
        self.send_response(code)
        self.sendCommonHeaders()
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(object).encode())

    def publishRequest(self):
        # Send one MQTT message for every incoming request
        message = json.dumps(
            {
                "method": self.command,
                "path": self.path,
                "client": self.client_address[0],
            }
        )
        # retain=False: the broker does not store this message
        mqtt_client.publish(request_topic, message, qos=1, retain=False)

    def serveStatic(self):
        # Look for index.html next to main.py first, then in the working directory
        possible_paths = [
            os.path.join(base_directory, "index.html"),
            os.path.join(os.getcwd(), "index.html"),
        ]
        local_file_path = next(
            (path for path in possible_paths if os.path.isfile(path)), None
        )
        print(local_file_path)

        if local_file_path is None:
            self.sendJSON({"status": "error", "message": "index.html not found"}, code=404)
            return

        self.send_response(200)
        self.sendCommonHeaders()

        mime_type, _ = mimetypes.guess_type(local_file_path)
        if mime_type:
            self.send_header("Content-type", mime_type)
        else:
            self.send_header("Content-type", "application/octet-stream")

        self.end_headers()

        with open(local_file_path, "rb") as file:
            self.wfile.write(file.read())

    def do_OPTIONS(self):
        try:
            self.publishRequest()
        except Exception as e:
            print(f"Error publishing MQTT message: {e}")

        self.send_response(204)
        self.sendCommonHeaders()
        self.end_headers()

    def do_GET(self):
        route = self.path.split("?")[0]

        try:
            self.publishRequest()

            if route == "/":
                self.serveStatic()

            elif route == "/api/sensors":
                with sensor_lock:
                    air = air_sensor.readAir()
                    light = light_sensor.readLight()
                self.sendJSON(
                    {
                        "status": "ok",
                        "data": [
                            {
                                "label": "Temperature",
                                "value": air.temperature,
                                "unit": "°C",
                            },
                            {"label": "Humidity", "value": air.humidity, "unit": "%"},
                            {
                                "label": "Illuminance",
                                "value": light,
                                "unit": "lux",
                            },
                        ],
                    }
                )

            elif route == "/api/air":
                with sensor_lock:
                    air = air_sensor.readAir()
                self.sendJSON(
                    {
                        "status": "ok",
                        "data": [
                            {
                                "label": "Temperature",
                                "value": air.temperature,
                                "unit": "°C",
                            },
                            {"label": "Humidity", "value": air.humidity, "unit": "%"},
                        ],
                    }
                )

            elif route == "/api/light":
                with sensor_lock:
                    light = light_sensor.readLight()
                self.sendJSON(
                    {
                        "status": "ok",
                        "data": {
                            "label": "Illuminance",
                            "value": light,
                            "unit": "lux",
                        },
                    }
                )

            else:
                self.sendJSON({"status": "error", "message": "Not found"}, code=404)

        except Exception as e:
            print(f"Error handling {self.path}: {e}")
            if not self.response_started:
                self.sendJSON({"status": "error", "message": str(e)}, code=500)

    def handleOtherMethod(self):
        try:
            self.publishRequest()
        except Exception as e:
            print(f"Error publishing MQTT message: {e}")
        self.sendJSON({"status": "error", "message": "Method not allowed"}, code=405)

    do_POST = handleOtherMethod
    do_PUT = handleOtherMethod
    do_PATCH = handleOtherMethod
    do_DELETE = handleOtherMethod


def main():
    web_server = ThreadingHTTPServer((host, port), Server)
    print(f"Server started and listen to {host}:{port}")

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    print("Server stopped")


if __name__ == "__main__":
    main()
