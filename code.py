# Based off the following
# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: Unlicense
import time                                                             # Time for timer and alarms
import ssl                                                              # SSL for secure communication
import alarm                                                            # Alarm used for power savings
import board                                                            # Board interface to hardware
import digitalio                                                        # Digital IO interface for LED feedback
import wifi                                                             # WiFi for network communication
import socketpool                                                       # Sockets for WiFi and HTTP communication
import adafruit_requests                                                # HTTP
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError    # HTTP IO and Errors
from adafruit_lc709203f import LC709203F, PackSize                      # Battery Module
from adafruit_bme280 import basic as adafruit_bme280                    # BME280 Temperature/Humidity/Pressure Sensors

# Import secrets for WiFi and Influx
try:
    from config import config
except ImportError:
    print("WiFi and Influx information are kept in config.py, please add them there!")
    raise

# Set debug
debug = config["debug"]

# Set InfluxDB location
influxdb_path = config["influx_write_path"] + "?db=" + config["influx_database"]
influxdb_url = config["influx_scheme"] + "://" + config["influx_host"] + ":" + config["influx_port"] + influxdb_path
location = config["sensor_location"]

# min_sleep_duration is necessary to avoid ESP32 ambient temperature impact
# the minimum that can be used safely and accurately is 300 seconds
min_sleep_duration = 300
sleep_duration = config["sleep_duration"]

# Setup the red LED
led = digitalio.DigitalInOut(board.LED)
led.switch_to_output()

# Update to match the mAh of your battery for more accurate readings.
# Can be MAH100, MAH200, MAH400, MAH500, MAH1000, MAH2000, MAH3000.
# Choose the closest match. Include "PackSize." before it, as shown.
battery_pack_size = PackSize.MAH2000

# Set up the BME280 and LC709203 sensors
bme280 = adafruit_bme280.Adafruit_BME280_I2C(board.I2C())
battery_monitor = LC709203F(board.I2C())
battery_monitor.pack_size = battery_pack_size

# Collect the sensor data values and format the data
temperature = "{:.2f}".format(bme280.temperature)
temperature_f = "{:.2f}".format((bme280.temperature * (9 / 5) + 32))  # Convert C to F
humidity = "{:.2f}".format(bme280.relative_humidity)
pressure = "{:.2f}".format(bme280.pressure)
battery_voltage = "{:.2f}".format(battery_monitor.cell_voltage)
battery_percent = "{:.1f}".format(battery_monitor.cell_percent)

def go_to_sleep(sleep_period):
    # Turn off I2C power by setting it to input
    i2c_power = digitalio.DigitalInOut(board.I2C_POWER)
    i2c_power.switch_to_input()

    # Create an alarm that will trigger sleep_period number of seconds from now.
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_period)

    # Exit and deep sleep until the alarm wakes us.
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)

# Wi-Fi connections can have issues! This ensures the code will continue to run.
try:
    # Connect to Wi-Fi
    wifi.radio.connect(config["ssid"], config["password"])
    if debug:
        print("Connected to {}!".format(config["ssid"]))
        print("IP:", wifi.radio.ipv4_address)

    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())

# Wi-Fi connectivity fails with error messages, not specific errors, so this except is broad.
except Exception as e:  # pylint: disable=broad-except
    if debug:
        print(e)
    go_to_sleep(min_sleep_duration)

# Define sensors
measurements = {
    "weather": {
        "humidity": humidity,
        "pressure": pressure,
        "temperature_c": temperature,
        "temperature_f": temperature_f
    },
    "battery": {
        "voltage": battery_voltage,
        "charge": battery_percent
    }
}

# print all measurements
if debug:
    print(measurements)

# store our multiline string for influx batching
data = ""

# Update each measurement
for measurement, mapping in measurements.items():
    for field, value in mapping.items():
        payload = measurement + "," + "location=" + location + " " + field + "=" + value + "\n"
        data += payload

# print outbound request
if debug:
    print(data)

try:
    requests.post(influxdb_url, data=data)
except Exception as e:  # pylint: disable=broad-except
    if debug:
        print(e)
    go_to_sleep(min_sleep_duration)

go_to_sleep(sleep_duration)
