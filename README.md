# AdaFruit Feather ESP-S2 BME280 Weather Station

The purpose of this project was to have a low-cost temperature sensor
solution for home use.  While investigating temperature sensors it seemed that
most sensors start at around $35 and are limited to N number of sensors.  Many
of them included subscriptions which I don't like.

The solution that I came up with based on my recent learning of time series
databases and moving metrics across the wire has been really stable so far.
I've tried to make it as simple as possible with as few moving parts.

At 10 minute interval the 2500mAh provides ~2 months of battery.

## Project Diagram
![sensor project diagram](_images/sensors-project-diagram.png)

## Project Dashboard
![grafana 7 day dashboard](_images/dashboard-7-days.png)

Sensor:
* [AdaFruit Feather ESP-S2 BME280](https://www.adafruit.com/product/5303)

Battery: 
* [Lithium-Ion Polymer Battery - 3.7v 2500mAh](https://www.adafruit.com/product/328)

Relay:
* [Fanless Mini PC Intel Atom Z8350 Processor, 8GB LDDR3, 128GB EMMC](https://www.amazon.com/gp/product/B0BCFBJ212)

Battery Recharging:
* [5V 2.5A Switching Power Supply with 20AWG MicroUSB](https://www.adafruit.com/product/1995)
* [PowerBoost 1000 Charger - Rechargeable 5V Lipo USB Boost @ 1A - 1000C](https://www.adafruit.com/product/2465)