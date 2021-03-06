# ExpoLIS Sensor Node
Software that runs on the raspberry that controls the sensor hardware. This software reads sensor values and publishes values on the ExpoLIS MQTT broker.  Data order is important and should match the ExpoLIS server daemon script responsible for saving sensor data in the database.

If you use this software please cite the following publication:

> Pedro Santana, Alexandre Almeida, Pedro Mariano, Carolina Correia, Vânia Martins, Susana Marta Almeida. (2021). [Air quality mapping and visualisation: An affordable solution based on a vehicle-mounted sensor network](https://www.sciencedirect.com/science/article/pii/S0959652621024124). Journal of Cleaner Production, 315:128194.

For complementary information see the following publication:

> Pedro Mariano, Susana Marta Almeida, Alexandre Almeida, Carolina Correia, Vânia Martins, José Moura, Tomás Brandão e Pedro Santana. "An Information System for Air Quality Monitoring using Mobile Sensor Networks". In: Proceedings of the 19th International Conference on Informatics in Control, Automation and Robotics. INSTICC. SciTePress.

    @article{Santana2021a,
       author =       {Pedro Santana and Alexandre Almeida and Pedro Mariano and Carolina Correia and Vânia Martins and Susana Marta Almeida}
       title =        {Air quality mapping and visualisation: An affordable solution based on a vehicle-mounted sensor network},
       journal =      {Journal of Cleaner Production},
       volume =       315,
       pages =        128194,
       year =         2021,
       issn =         {0959-6526},
       doi =          {10.1016/j.jclepro.2021.128194},
       url =          {https://www.sciencedirect.com/science/article/pii/S0959652621024124}
    }
    
    @InProceedings{Mariano2022a,
       author =       {Pedro Mariano and Susana Marta Almeida and
                       Alexandre Almeida and Carolina Correia and
                       Vânia Martins and José Moura and
                       Tomás Brandão and Pedro Santana},
       title =        {An Information System for Air Quality Monitoring using Mobile Sensor Networks},
       booktitle =    {Proceedings of the 19th International Conference on Informatics in Control, Automation and Robotics (ICINCO 2022)},
       publisher =    {SciTePress},
       organization = {INSTICC}
    }

# Sensor Hardware

* Optical particle counter (Model OPC-N3 from Alphasense);
* CO sensor (CO-B4, Alphasense);
* NO2 sensor (NO2-A43F, Alphasense);
* Temperature and relative humidity sensor (SHTC3, Adafruit);
* Barometric pressure sensor (LPS25, Adafruit);
* Accelerometer (MSA 301, Adafruit);
* GPS sensor (PA1010D, Adafruit).


# Dependencies

The sensor node has the following dependencies

| sensor                   | library | pip package                     |
|--------------------------|---------|---------------------------------|
| ADC                      | ADS1115 | `adafruit-circuitpython-ads1x15`|
| Barometric pressure      | LPS25   | `adafruit-circuitpython-lps2x`  |
| Accelerometer            | MSA301  | `adafruit-circuitpython-msa301` |
| Temperature and Humidity | SHTC3   | `adafruit-circuitpython-shtc3`  |
| GPS                      | PA1010D | `adafruit-circuitpython-gps`    |
| Real Time Clock          | DS1307  | `adafruit-circuitpython-ds1307` |

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


# Configuration

Clone this repository into the raspberry pi or download a zip file with this repository.  Run the `setup.py` script:

    python3 <PATH_TO_REPOSITORY>/setup.py

This script will copy the python files to a folder in the home directory of the `pi` user, ask the id number of the sensor node, ask the path where the USB pen is mounted, create the `Sensor_Node.ini` configuration file, and install the `stay_alive.sh` cron script.

The sensor node identification should be unique, as it identifies sensor data published by a sensor node.  The USB pen is where CSV files with sensor data are saved.  These CSV files are a backup of sensor data in case they are not received by the ExpoLIS server.  If you change the USB pen, you have to edit the `Sensor_Node.ini` file.

## Sensor_Node.ini

The `Sensor_Node.ini` file contains information about a sensor node.  It is created by the `setup.py` script.  Its location is in folder `/home/pi/SensorNode/`.  An example of the contents of this file is:

    [BASE]
    sensor_node_id = 1
    mqtt_broker = mqtt.eclipse.org
    publish_rate_period = 1
    kp = 20.0
    kd = 50.0
    storage = /media/pi/usb-pen/
    log_csv_boot = True
    log_img_boot = False

Most fields are self explanatory.

* `publish_rate_period` is the rate in seconds at which data is published;
* `kp` and `kd` are used by the kalman filter when processing raw PM data;
* `storage` folder where the USB pen is mounted;
* `log_csv_boot` whether the sensor node should save sensor data in CSV files;
* `log_img_boot` currently not used.
