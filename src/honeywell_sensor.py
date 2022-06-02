import board
import busio
import serial
import time
import struct

uart = None


def comm (command, reply_length):
    rcv = None
    try:
        if command is not None:
            stop_measurement = bytes.fromhex (command)
            uart.write (stop_measurement)  # Write to the UART from a buffer
        rcv = uart.read (reply_length)
        return rcv
    except Exception as e:
        pass


def calc_cs (data):
    total = 0
    for j in range (12):
        total = total + data [j]
    cs = (65536 - total) % 256
    return cs


def init_sensor ():
    global uart

    uart = serial.Serial ("/dev/ttyAMA0", baudrate=9600, timeout=0.2)
    uart.read (100)

    # stop auto send
    print (comm ('68012077', 2))

    # starting particle measurement
    print (comm ('68010196', 2))


def get_values (debug=True):
    if uart is None:
        init_sensor ()
        return -1, -1, -1, -1

    output = comm ('68010493', 16)

    if output is None or len (output) < 16:
        init_sensor ()
        return -1, -1, -1, -1

    pm1 = output [3] * 256 + output [4]
    pm25 = output [5] * 256 + output [6]
    pm4 = output [7] * 256 + output [8]
    pm10 = output [9] * 256 + output [10]
    cs = output [14] * 256 + output [15]

    if cs != calc_cs (output):
        pm1 = pm25 = pm4 = pm10 = -1
        init_sensor ()

    if debug:
        print (' '.join ([hex (b) for b in output]) + "\n")
        print ('CS ' + str (cs) + "  " + str (calc_cs (output)))
        print (str (pm1) + " " + str (pm25) + " " + str (pm4) + " " + str (pm10))

    return pm1, pm25, pm4, pm10
