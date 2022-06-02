"""
This module contains the commands that the expolis sensor node can receive by mqtt.

All commands are represented by a single string.  The first word in the string is a keyword stating which command to
run.  Additional words in the string are arguments to the command.

Each function in this module takes a string as argument that corresponds to remainder of the string received has the
mqtt payload.
"""

from subprocess import call
from time import sleep
from threading import Thread
import paho.mqtt.client as mqtt

import configuration as c


def command_ping (_mqtt_client: mqtt.Client, *_args):
    c.WATCHDOG_PATH.touch ()


def command_set_time (mqtt_client: mqtt.Client, t_year, t_month, t_day, t_hour, t_minute, t_seconds):
    def thread_set_time ():
        msg_time_date = 'sudo date -s "{}-{}-{} {}:{}:{}"'.format (t_year, t_month, t_day, t_hour, t_minute, t_seconds)
        print ("time/date set: " + msg_time_date)
        call (msg_time_date, shell=True)
        sleep (1)
        # noinspection SpellCheckingInspection
        call ("sudo hwclock -w", shell=True)
        mqtt_client.publish (c.TOPIC_LOG, "time and date set.", qos=2)

    mqtt_client.publish (c.TOPIC_LOG, "received set time date", qos=2)
    thread_time = Thread (target=thread_set_time)
    thread_time.start ()


def command_power_off (mqtt_client: mqtt.Client):
    mqtt_client.publish (c.TOPIC_LOG, 'received power off', qos=2)
    sleep (0.5)
    call ("sudo sync", shell=True)
    call ("sudo nohup shutdown -h now", shell=True)


def command_reboot (mqtt_client: mqtt.Client):
    mqtt_client.publish (c.TOPIC_LOG, 'received reboot', qos=2)
    sleep (0.5)
    call ("sudo sync", shell=True)
    call ("sudo nohup shutdown -r now", shell=True)


def command_set_wifi (mqtt_client: mqtt.Client, ssid: str, psk: str, key_management: str):
    mqtt_client.publish (c.TOPIC_LOG, 'received set wifi', qos=2)
    with open ('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as fd:
        fd.write ('''
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=PT

network={{
   ssid="Expolis"
   psk="xpto1234"
   priority=3
}}

network={{
   ssid="VodafoneMobileWiFi-8699C6"
   psk="eC6UF89802"
   priority=2
}}
network={{
   ssid="{ssid}"
   psk="{psk}"
   key_mgmt={key_mgmt}
   priority=1
}}
'''.format (
            ssid=ssid,
            psk=psk,
            key_mgmt=key_management,
        ))
    mqtt_client.publish (c.TOPIC_LOG, 'wifi set, rebooting.', qos=2)
    call ("sudo sync", shell=True)
    call ("sudo nohup shutdown -r now", shell=True)
