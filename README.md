# expolis-sensor-node
Software that runs on the raspberry that controls the sensors

# Dependencies

The second version of the sensor node has the following dependencies

| sensor                   | library | pip package                 |
|--------------------------|---------|-----------------------------|
| PM1 PM2.5 PM10           |         |                             |
| ADC                      | ADS1115 |                             |
| Barometric pressure      | LPS25   |                             |
| Accelerometer            | MSA301  |                             |
| Temperature and Humidity | SHTC3   |                             |
| GPS                      | PA1010D | `adafruit-circuitpython-gps`|
| Real Time Clock          | DS1307  |                             |

    sudo pip3 install adafruit-circuitpython-ads1x15
    sudo pip3 install adafruit-circuitpython-lps2x
    sudo pip3 install adafruit-circuitpython-msa301
    sudo pip3 install adafruit-circuitpython-shtc3
    sudo pip3 install adafruit-circuitpython-ds1307
    sudo pip3 install adafruit-circuitpython-gps


# Communication

The software sends sensor data as a MQTT string. All values are separated by a space. The data sent is:

0. sensor id
1. iteration number
2. time stamp in the format YYYY-MM-DDTHH:MM:SS.sssss
3. time stamp in the format YYYY-MM-DDTHH:MM:SS.sssss
4. latitude
5. longitude
6. CO value 1 of 2
7. CO value 2 of 2
8. NO2 value 1 of 2
9. NO2 value 2 of 2
10. PM1 raw value
11. PM2.5 raw value
12. PM10 raw value
13. PM1 filtered value
14. PM2.5 filtered value
15. PM10 filtered value
16. temperature
17. pressure
18. humidity
19. GPS error
20. power supply value
21. kalman filter parameter kp
22. kalman filter parameter kd

# Installation

1. Get a SD card and install the raspberry pi operating system.  See the documentation at <https://www.raspberrypi.org/documentation/installation/installing-images/README.md> on how to do this.
2. Configure the access the raspberry pi host.
   1. Without monitor and keyboard, check the documentation at <https://www.raspberrypi.org/documentation/remote-access/ssh/README.md>.  You need to plug the network cable to the raspberrypi.
3. Log in to the raspberry pi.
4. Change the password of the pi user.
   1. run the command `sudo raspi-config`
   2. select option `1 System Options`
   3. select option `S3 Password`
5. Set the host name.
   1. run the command `sudo raspi-config`
   2. select option `1 System Options`
   3. select option `S4 Hostname`
6. Configure the raspberry to connect to the expolis Wi-Fi network
   1. run the command `sudo raspi-config`
   2. select option `1 System Options`
   3. select option `S1 Wireless LAN`
   4. select the country
   5. enter the SSID and the password of the expolis Wi-Fi network
7. Set the localisation options.
   1. run the command `sudo raspi-config`
   2. select option `5 Localisation Options`
   3. set the locale.
   4. set the timezone.
4. Enable the I2C bus.
   1. run the command `sudo raspi-config`
   2. select option `3 Interface Options`
   3. select option `P5 I2C`
5. Install I2C software
   1. run the command `sudo apt-get install -y python-smbus`
   2. run the command `sudo apt-get install -y i2c-tools`
   3. test and check the devices with the command `sudo i2cdetect - 1`
   4. check the tutorial at <https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c>
10. Configure RTC.
   1. Edit the file `/boot/config.txt`.
   2. Add the line `dtoverlay=i2c-rtc,ds1307` to the end of the file.
   3. Reboot
   4. run the command `sudo apt-get install -y i2c-tools`
