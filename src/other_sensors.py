"""
This module handles sensors whose API to get values is simple.

The sensor data handled in this module is: carbon monoxide, nitric dioxide, power supply voltage, temperature,
pressure and humidity.
"""
import adafruit_ads1x15.ads1115
import adafruit_ads1x15.analog_in
import adafruit_shtc3
import adafruit_lps2x
import adafruit_msa301
import board
import busio


def get_values ():
    # initialisation
    i2c = busio.I2C (board.SCL, board.SDA)
    ads = adafruit_ads1x15.ads1115.ADS1115 (i2c)
    gas_co_reading_1 = adafruit_ads1x15.analog_in.AnalogIn (ads, adafruit_ads1x15.ads1115.P0)
    gas_co_reading_2 = adafruit_ads1x15.analog_in.AnalogIn (ads, adafruit_ads1x15.ads1115.P1)
    gas_no2_reading_1 = adafruit_ads1x15.analog_in.AnalogIn (ads, adafruit_ads1x15.ads1115.P2)
    gas_no2_reading_2 = adafruit_ads1x15.analog_in.AnalogIn (ads, adafruit_ads1x15.ads1115.P3)
    power_supply_reading = adafruit_ads1x15.analog_in.AnalogIn (ads, adafruit_ads1x15.ads1115.P3)
    humidity_temperature_reading = adafruit_shtc3.SHTC3 (i2c)
    pressure_reading = adafruit_lps2x.LPS25 (i2c)
    acceleration_reading = adafruit_msa301.MSA301 (i2c)
    # get values
    gas_co_value_1 = gas_co_reading_1.voltage
    gas_co_value_2 = gas_co_reading_2.voltage
    gas_no2_value_1 = gas_no2_reading_1.voltage
    gas_no2_value_2 = gas_no2_reading_2.voltage
    power_supply_value = power_supply_reading.voltage * 2.0
    temperature_value, relative_humidity_value = humidity_temperature_reading.measurements
    pressure_value = pressure_reading.pressure
    acceleration_value_1, acceleration_value_2, acceleration_value_3 = acceleration_reading.acceleration
    # return values
    return gas_co_value_1, gas_co_value_2, gas_no2_value_1, gas_no2_value_2, temperature_value, pressure_value, relative_humidity_value, power_supply_value, acceleration_value_1, acceleration_value_2, acceleration_value_3
