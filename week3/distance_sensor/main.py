from http.server import BaseHTTPRequestHandler, HTTPServer
import signal
from time import sleep
from distance_sensor import DistanceSensor
import json

sensor = DistanceSensor()

host = "0.0.0.0"
port = 8080

sleep(1)


class SensorTimeout(Exception):
    pass


def raise_sensor_timeout(signum, frame):
    raise SensorTimeout("Ultrasonic sensor read timed out")


signal.signal(signal.SIGALRM, raise_sensor_timeout)


class Server(BaseHTTPRequestHandler):
    def sendJSON(self, object: object, code: int = 200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Vary", "Origin")
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(object).encode())

    def do_GET(self):
        if self.path == "/":
            try:
                signal.setitimer(signal.ITIMER_REAL, 0.2)
                distance = sensor.read_distance()
            except (TimeoutError, RuntimeError, SensorTimeout) as error:
                self.sendJSON({"status": "error", "message": str(error)}, 503)
                return
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)

            self.sendJSON({"status": "ok", "distance_cm": distance})


def main():
    web_server = HTTPServer((host, port), Server)
    print(f"Server started and listen to {host}:{port}")

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

print("Server stopped")
