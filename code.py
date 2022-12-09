# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: Unlicense
"""
CircuitPython Adafruit IO Example for BME280 and LC709203 Sensors
"""
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
    from secrets import secrets
except ImportError:
    print("WiFi and Influx information are kept in secrets.py, please add them there!")
    raise

# Set InfluxDB location
influxdb_path = secrets["influx_write_path"] + "?db=" + secrets["influx_database"]
influxdb_url = secrets["influx_scheme"] + "://" + secrets["influx_host"] + ":" + secrets["influx_port"] + influxdb_path
location = secrets["sensor_location"]

# Feather will sleep for this duration between sensor readings
sleep_duration = 600

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

    # Create a an alarm that will trigger sleep_period number of seconds from now.
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_period)
    # Exit and deep sleep until the alarm wakes us.
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)

# Wi-Fi connections can have issues! This ensures the code will continue to run.
try:
    # Connect to Wi-Fi
    wifi.radio.connect(secrets["ssid"], secrets["password"])
    print("Connected to {}!".format(secrets["ssid"]))
    print("IP:", wifi.radio.ipv4_address)

    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())

# Wi-Fi connectivity fails with error messages, not specific errors, so this except is broad.
except Exception as e:  # pylint: disable=broad-except
    #print(e)
    go_to_sleep(60)

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

# Update each measurement
for measurement, mapping in measurements.items():
    for m, value in mapping.items():
      data = measurement + "," + "location=" + location + " " + m + "=" + value
      try:
          requests.post(influxdb_url, data=data)
      except Exception as e:  # pylint: disable=broad-except
          #print(e)
          go_to_sleep(60)

go_to_sleep(sleep_duration)

