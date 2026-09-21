from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import sleep
from air_sensor import AirSensor
from light_sensor import LightSensor
from distance_sensor import DistanceSensor
import mimetypes
import textwrap
import threading
import json
import os

air_sensor = AirSensor()
light_sensor = LightSensor()
distance_sensor = DistanceSensor()

# GPIO and I2C are shared hardware: only one thread may read at a time
sensor_lock = threading.Lock()

host = "0.0.0.0"
port = 8080

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

    def serveStatic(self):
        local_file_path = os.path.join(".", self.path[1:], "index.html")
        print(local_file_path)

        if not (os.path.exists(local_file_path) and os.path.isfile(local_file_path)):
            self.send_error(404, "File not found")
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
        self.send_response(204)
        self.sendCommonHeaders()
        self.end_headers()

    def do_GET(self):
        route = self.path.split("?")[0]

        try:
            if route == "/":
                self.serveStatic()

            elif route == "/metrics":
                metric_lines = []

                with sensor_lock:
                    try:
                        light = light_sensor.readLight()
                        metric_lines.append(textwrap.dedent(f"""\
                            # HELP sensor_light measured light itensity in lux
                            # TYPE sensor_light gauge
                            sensor_light {light}
                        """))
                    except Exception as error:
                        print(f"Light sensor failed: {error}")

                    try:
                        air = air_sensor.readAir()
                        metric_lines.append(textwrap.dedent(f"""\
                            # HELP sensor_air_temperature measured temperature in celcius
                            # TYPE sensor_air_temperature gauge
                            sensor_air_temperature {air.temperature}
                            # HELP sensor_air_humidity measured humidity in percent
                            # TYPE sensor_air_humidity gauge
                            sensor_air_humidity {air.humidity}
                        """))
                    except Exception as error:
                        print(f"Air sensor failed: {error}")

                    try:
                        distance = distance_sensor.read_distance()
                        metric_lines.append(textwrap.dedent(f"""\
                            # HELP sensor_distance measured distance in centimeters
                            # TYPE sensor_distance gauge
                            sensor_distance {distance}
                        """))
                    except Exception as error:
                        print(f"Distance sensor failed: {error}")

                body = "".join(metric_lines).encode()

                self.send_response(200)
                self.sendCommonHeaders()
                self.send_header("Content-type", "text/plain; version=0.0.4")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()

                self.wfile.write(body)

            elif route == "/air":
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

            elif route == "/light":
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

            elif route == "/distance":
                with sensor_lock:
                    distance = distance_sensor.read_distance()
                self.sendJSON({"status": "ok", "distance": distance})

            else:
                self.send_error(404, "Not found")

        except Exception as e:
            print(f"Error handling {self.path}: {e}")
            if not self.response_started:
                self.sendJSON({"status": "error", "message": str(e)}, code=500)


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
