from time import sleep
import RPi.GPIO as GPIO
import threading
import dht11

GPIO.setmode(GPIO.BOARD)

class AirSensor():
    def update(self):
        while True:
            readout = self.instance.read()
            valid = readout.is_valid()
            if valid:  # read until valid values
                print(f'Temperature: {readout.temperature}°C Humidity: {readout.humidity}%')
                self.result = readout
                sleep(2)  # DHT11 can only be read every ~2 seconds
            else:
                sleep(2)

    def __init__(self):
        self.instance = dht11.DHT11(pin = 7)
        self.result = self.instance.read()
        print(self.result.__dict__)

        threading.Thread(target=self.update, daemon=True).start()

    def readAir(self):
        return self.result
