import struct
import paho.mqtt.client as mqtt
import spidev
import threading
from time import sleep

import configuration
import pms_sensor_kalman


# noinspection PyTypeChecker
spi = None  # type: spidev.SpiDev

pm_1 = -1
pm_2_5 = -1
pmC = -1

opc_start_thread_done = False
opc_sample_thread_done = False

iteration = 0


def init_sensor ():
    """
    Initialise the OPC-N3 sensor that return the PM measurements.
    """
    pms_sensor_kalman.init_kalman_filters ()
    threading.Thread (target=thread_opc_start_run).start ()


def thread_opc_start_run ():
    global opc_start_thread_done
    global spi
    opc_start_thread_done = False

    # preparing SPI communications for OPC-N3
    spi = spidev.SpiDev ()
    spi.open (0, 0)
    spi.mode = 1
    spi.max_speed_hz = 500000
    # spi.cshigh = False
    # sleep(0.1)
    # spi.cshigh = True
    # sleep(0.1)
    # spi.cshigh = False
    sleep (1)

    print ('OPC done')

    # turn on OPC-N3 fan and laser
    fan_on ()
    sleep (1)
    print ('OPC fan on')

    laser_on ()
    sleep (1)
    print ('OPC laser on')

    opc_start_thread_done = True

    # # now we can sample the OPC_N3 sensors
    # threading.Thread (target=thread_sample_opc_run).start ()


# start OPC-N3 fan
def fan_on (debug=False):
    talk_device (0x03, 'fan on', debug)


# start OPC-N3 laser
def laser_on (debug=False):
    talk_device (0x07, 'laser on', debug)


# stop OPC-N3 fan
def fan_off (debug=False):
    talk_device (0x02, 'fan off', debug)


# stop OPC-N3 laser
def laser_off (debug=False):
    talk_device (0x06, 'laser off', debug)


def talk_device (message, action='act device', debug=False):
    count_x = 0
    ctr = 0
    while True:
        count_x = count_x + 1
        if count_x > 3:
            if debug:
                print ('{}: failed!'.format(action))
            return
        a = spi.xfer ([0x03])[0]
        if debug:
            print ('{}: CMD1 {} {}'.format (action, hex (a), a))
        count = 0
        while a is not int ('0xf3', 16) and count != 20:
            sleep (0.02)
            ctr = 1
            a = spi.xfer ([0x03])[0]
            if debug:
                print ('{}: CMD2 {} {}'.format (action, hex (a), a))
            count = count + 1
        if a is int ('0xf3', 16):
            break
        if debug:
            print ('{}: resetting spi'.format (action))
        sleep (3)
    if ctr == 0:
        sleep (0.02)
        _dummy = spi.xfer ([0x03])[0]
    sleep (0.00002)
    a = spi.xfer ([message])[0]
    if debug:
        print ('{}: done, {} {}'.format (action, hex (a), a))
    sleep (3)


def thread_sample_opc_run (debug=False):
    global pm_1
    global pm_2_5
    global pmC
    global opc_sample_thread_done

    opc_sample_thread_done = False
    ctr = 0
    count_x = 0
    while True:
        count_x = count_x + 1
        if count_x > 3:
            if debug:
                print ('fail to sample OPC')
            break
        a = spi.xfer ([0x32])[0]
        if debug:
            print ("CMD1: ", hex (a), a)
        count = 0
        while a is not int ('0xf3', 16) and count != 20:  # [0xf3]: #49
            ctr = 1
            sleep (0.02)
            a = spi.xfer ([0x32])[0]
            if debug:
                print ("CMD2: ", hex (a), a)
            count = count + 1
        if a is int ('0xf3', 16):
            break
        if debug:
            print ("resetting spi")
        sleep (3)
    if ctr == 0:
        sleep (0.02)
        _a = spi.xfer ([0x32])[0]
    output = []
    for _i in range (14):
        sleep (0.00002)
        a = spi.xfer ([0x32])[0]
        output.append (a)
    pm_1 = struct.unpack ('f', bytes (output[0:4]))[0]
    pm_2_5 = struct.unpack ('f', bytes (output[4:8]))[0]
    pmC = struct.unpack ('f', bytes (output[8:12]))[0]
    check = combine_bytes (output[12], output[13])

    # check = combine_bytes (output[13], output[12])
    # pm_1a = struct.unpack ('f', bytes (output[0:3]))[0]
    
    print ('OPC 14 bytes:', end='')
    for idx, ab in enumerate (output):
        if idx % 4 == 0:
            print (' ', end='')
        print ('{:02X}'.format (ab), end='')
    print (' {:10.7} {:10.7f} {:10.7f}'.format (pm_1, pm_2_5, pmC))
    
    if True or debug:
        print ("CRC ", check, "Dif ", check - calc_crc (output, 12))
    if check - calc_crc (output, 12) != 0:
        print ('---> Error in CRC {} {} {}'.format (pm_1, pm_2_5, pmC))
        pm_1 = -1
        pm_2_5 = -1
        pmC = -1
    if debug:
        print ("PMA ", pm_1, "PMB ", pm_2_5, "PMC ", pmC)
    opc_sample_thread_done = True


# make an int from two bytes
def combine_bytes (lsb, msb):
    return (msb << 8) | lsb


# compute CRC code for OPC-N3
def calc_crc (data, number_of_bytes):
    crc = 0xFFFF
    for byteCtr in range (number_of_bytes):
        crc ^= data[byteCtr]
        for _bit in range (8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc


def get_values (debug=True, sampling_period=1):
    global iteration
    if opc_start_thread_done:
        threading.Thread (
            target=thread_sample_opc_run,
            args=(False, )
        ).start ()
        sleep (0.1)
        if opc_sample_thread_done and pm_1 != -1 and pm_1 != 0:
            pm1_filtered, pm2_5_filtered, pm10_filtered = pms_sensor_kalman.step_kalman_filters (pm_1, pm_2_5, pmC, sampling_period)
            result = (pm_1, pm_2_5, pmC, pm1_filtered, pm2_5_filtered, pm10_filtered)
        else:
            iteration += 1
            if iteration == 3:
                print ('Algo esquisito aconteceu ?!@#%&*?!!\nVou fazer restart ao OPC')
                threading.Thread (target=thread_opc_start_run).start ()
                iteration = 0
            result = (-1, -1, -1, -1, -1, -1)
    else:
        result = (-1, -1, -1, -1, -1, -1)

    return result
        

def get_values__ (debug=True):
    global iteration

    if opc_start_thread_done and opc_sample_thread_done and iteration > 60 and pm_1 == -1:
        if debug:
            print ('OPC with issues: restarting sensor     {} {} {}'.format (pm_1, pm_2_5, pmC))
        threading.Thread (target=thread_opc_start_run).start ()
        if debug:
            print ('retried')
        iteration = 1
        result = (-1, -1, -1, -1, -1, -1)
    elif opc_start_thread_done and opc_sample_thread_done:
        if debug:
            pass
            # print ('OPC has already finished sampling')
        pm1_filtered, pm2_5_filtered, pm10_filtered = pms_sensor_kalman.step_kalman_filters (pm_1, pm_2_5, pmC)
        result = (pm_1, pm_2_5, pmC, pm1_filtered, pm2_5_filtered, pm10_filtered)
        threading.Thread (
            target=thread_sample_opc_run,
            args=(False, )
        ).start ()
    else:
        if debug:
            print (
                "OPC hasn't finished (re)starting" if not opc_start_thread_done else
                "OPC hasn't finished sampling")
        result = (-1, -1, -1, -1, -1, -1)
    iteration = iteration + 1
    return result


def command_stop_sensors (mqtt_client: mqtt.Client):
    mqtt_client.publish (configuration.TOPIC_LOG, 'received stop sensors', qos=2)
    fan_off ()
    laser_off ()


def command_start_sensors (mqtt_client: mqtt.Client):
    mqtt_client.publish (configuration.TOPIC_LOG, 'received start sensors', qos=2)
    fan_on ()
    laser_on ()
