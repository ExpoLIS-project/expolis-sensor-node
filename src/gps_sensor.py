import adafruit_gps
import board
import busio

from threading import Thread
from time import sleep


gps = None
stop_update_gps_thread = False


# noinspection SpellCheckingInspection
def init_gps ():
    global gps

    i2c = busio.I2C (board.SCL, board.SDA)
    # Create a GPS module instance.
    gps = adafruit_gps.GPS_GtopI2C (i2c, debug=False)
    gps.send_command (b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
    gps.send_command (b'PMTK220,1000')
    gps.update ()
    for _ in range (3):
        sleep (0.5)
        gps.update ()
    Thread (target=thread_update_gps_run).start ()


# noinspection PyUnresolvedReferences
def thread_update_gps_run ():
    while not stop_update_gps_thread:
        gps.update ()
        sleep (0.5)


# noinspection PyUnresolvedReferences
def get_values ():
    """
    Return a tuple with the GPS readings.
    The first two arguments contain the latitude and longitude, and the third argument contains the GPS error.
    If the GPS sensor doesn't have a reading, we return the tuple (-1, -1, -1).  Sometimes, the sensor cannot compute
    the GPS error, and this case, we return -1 as the third argument of the tuple.
    :return: a tuple with the GPS readings.
    """
    if gps.has_fix:
        latitude_ = gps.latitude
        longitude_ = gps.longitude
        gps_error_ = gps.horizontal_dilution
        # if gps_error_ is None:
        #     gps_error_ = -1
    else:
        latitude_ = -1
        longitude_ = -1
        gps_error_ = -1
    return latitude_, longitude_, gps_error_
