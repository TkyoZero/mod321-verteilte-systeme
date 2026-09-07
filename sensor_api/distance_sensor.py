import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.cleanup()


class DistanceSensor:
    def __init__(self, trigger_pin=36, echo_pin=32):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin

        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

        GPIO.output(self.trigger_pin, False)
        time.sleep(0.1)

    def read_distance(self):
        GPIO.output(self.trigger_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, False)

        timeout = time.monotonic() + 0.1

        while GPIO.input(self.echo_pin) == 0:
            if time.monotonic() >= timeout:
                raise TimeoutError("Ultrasonic sensor did not receive an echo")

        start_time = time.time()
        timeout = time.monotonic() + 0.1

        while GPIO.input(self.echo_pin) == 1:
            if time.monotonic() >= timeout:
                raise TimeoutError("Ultrasonic sensor echo signal timed out")
            stop_time = time.time()

        elapsed = stop_time - start_time
        distance_cm = (elapsed * 34300) / 2

        return round(distance_cm, 2)
