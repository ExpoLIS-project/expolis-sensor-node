# configuration module should be the first one to be imported
import pathlib

import configuration as c
# modules that manage sensors
import gps_sensor
import other_sensors
import pms_sensor
import pms_sensor_kalman
import camera_sensor
import honeywell_sensor

# other modules
import log
import commands
import mqtt_interface

import collections
import datetime
import netifaces
import paho.mqtt.client as mqtt
import threading
import time
import urllib.error
import urllib.request

iteration = 1
iteration_sample = 1

external_ip = ip = 'unknown'

stop_main_thread = False

events_description = collections.deque ()

verbose = 3

sensor_data_id = collections.deque (maxlen=3600)
sensor_data_message = collections.deque (maxlen=3600)

path_do_not_sent_file = pathlib.Path ('/home/pi/SensorNode/do-not-sent-file')


def main ():
    global iteration
    if verbose > 0:
        print ('Initialising GPS sensor...')
    gps_sensor.init_gps ()
    pms_sensor.init_sensor ()
    camera_sensor.init_camera()
    honeywell_sensor.init_sensor()
    log.init_log ()
    mqtt_interface.init_mqtt_interface (on_message)
    if verbose > 0:
        print ('Entering main loop...')
    while not stop_main_thread:
        if verbose > 2:
            print ('Main loop {}'.format (iteration))
        time_before = time.time ()
        step ()
        time_after = time.time ()
        time_left = 1 - (time_after - time_before)
        if verbose > 4:
            print ('Time left in iteration {}.'.format (time_left))
        if time_left > 0:
            time.sleep (time_left)
        iteration += 1
    finish ()


def step ():
    global iteration, iteration_sample

    if iteration % 60 == 0:
        print ('sensor_node.step()')
    if iteration % 30 == 0:
        threading.Thread (target=thread_get_ip_run).start ()
    if iteration % 10 == 0:
        # TODO: compute log_msg
        msg = 'PING {} {} {}{}__id_{}'.format (
            ip, external_ip,
            '_csv' if log.log_data else '',
            '_img' if camera_sensor.capture_frames else '',
            iteration_sample)
        mqtt_interface.client_public.publish (c.TOPIC_MANAGEMENT, msg, qos=2)
        mqtt_interface.client_private.publish (c.TOPIC_MANAGEMENT, msg, qos=2)

    if iteration % c.PUBLISH_RATE_PERIOD != 0:
        return
    
    timestamp = datetime.datetime.timestamp (datetime.datetime.now ())
    gps_values = gps_sensor.get_values ()
    other_values = other_sensors.get_values ()
    pms_values = pms_sensor.get_values (sampling_period=c.PUBLISH_RATE_PERIOD)
    pm_honeywell_values = honeywell_sensor.get_values(debug=True)
    #print(pm_honeywell_values)
    if verbose > 2:
        # print ('{} {} {}'.format (gps_values, other_values, pms_values))
        pass
    # region publish sensor data
    latitude, longitude, gps_error = gps_values
    gas_co_value_1, gas_co_value_2, gas_no2_value_1, gas_no2_value_2, temperature_value, pressure_value, humidity_value, power_supply_value, acceleration_value_1, acceleration_value_2, acceleration_value_3 = other_values
    fields_new = [
        c.SENSOR_NODE_ID,
        iteration_sample,
        datetime.datetime.fromtimestamp (timestamp),
        latitude, longitude,
        gas_co_value_1, gas_co_value_2, gas_no2_value_1, gas_no2_value_2,
    ] + list (pms_values) + [
        temperature_value, pressure_value, humidity_value,
        gps_error,
        power_supply_value,
        pms_sensor_kalman.kp_base, pms_sensor_kalman.kd_base,
        acceleration_value_1, acceleration_value_2, acceleration_value_3,
    ] + list(pm_honeywell_values) + [
        c.PUBLISH_RATE_PERIOD
    ]
    fields = fields_new
    msg = ' '.join ([str (e) for e in fields])
    mqtt_interface.client_public.publish (c.TOPIC_SENSOR_DATA, msg, qos=2)
    mqtt_interface.client_private.publish (c.TOPIC_SENSOR_DATA, msg, qos=2)
    # endregion
    sensor_data_id.append (iteration_sample)
    sensor_data_message.append (msg)
    log.step_log_csv (
        iteration=iteration_sample,
        step_timestamp=timestamp,
        gps_data=gps_values,
        pms_data=pms_values,
        pm_honeywell_data=pm_honeywell_values,
        other_sensor_data=other_values,
        event=events_description.pop () if len (events_description) > 0 else 'none',
        image_file=camera_sensor.image_file,
        ip=external_ip,
        sampling_period=c.PUBLISH_RATE_PERIOD)
    iteration_sample += 1


def thread_get_ip_run ():
    global ip
    global external_ip

    if verbose > 2 and 'wlan0' in netifaces.interfaces ():
        r = netifaces.ifaddresses ('wlan0')
        print (r)
    # noinspection SpellCheckingInspection
    if 'uap0' in netifaces.interfaces () and netifaces.AF_INET in netifaces.ifaddresses ('uap0'):
        ip = netifaces.ifaddresses ('uap0')[netifaces.AF_INET][0]['addr']
    else:
        ip = 'unavailable'

    external_ip = 'unavailable'
    try:
        # external_ip = urllib.request.urlopen ('https://ident.me').read ().decode ('utf8')
        external_ip = urllib.request.urlopen ('https://v4.ident.me').read ().decode ('utf8')
    except urllib.error.URLError:
        pass
    except Exception as e:
        print ('????')
        print (e)
        print (type (e))
    if verbose > 0:
        print ("IP: " + ip + " Public IP: " + external_ip)


def thread_resend_run (*intervals):
    if verbose > 0:
        print ('Thread resend')
    for an_interval in intervals:
        limits = an_interval.split ('-')
        if int (limits[0]) > iteration:
            if verbose > 1:
                print ('Old interval {}'.format (an_interval))
        else:
            index_from = int (limits [0])
            index_to = int (limits [1])
            for an_index in range (index_from, index_to + 1):
                try:
                    msg = sensor_data_message[sensor_data_id.index (an_index)]
                    if verbose > 1:
                        print ('Resending: {}'.format (msg))
                    mqtt_interface.client_public.publish (c.TOPIC_SENSOR_DATA, msg, qos=2)
                    mqtt_interface.client_private.publish (c.TOPIC_SENSOR_DATA, msg, qos=2)
                except ValueError:
                    pass


def command_resend (_mqtt_client: mqtt.Client, *intervals):
    threading.Thread (
        target=thread_resend_run,
        args=intervals
    ).start ()


def command_register_event (mqtt_client: mqtt.Client, an_event_description):
    events_description.append (an_event_description)
    if verbose > 0:
        print ("Received event: " + an_event_description)
    mqtt_client.publish (c.TOPIC_LOG, 'received event register', qos=2)


def command_kill (mqtt_client: mqtt.Client):
    global stop_main_thread
    print("received kill command")
    mqtt_client.publish (c.TOPIC_LOG, 'received process kill', qos=2)
    stop_main_thread = True


def command_change_sample_period (mqtt_client: mqtt.Client, new_sample_period):
    c.PUBLISH_RATE_PERIOD = int (new_sample_period)
    c.config['BASE']['publish_rate_period'] = new_sample_period
    c.save_config ()
    print ('Updated publish rate period to {}'.format (new_sample_period))
    mqtt_client.publish (c.TOPIC_LOG, 'Updated publish rate period to {}'.format (new_sample_period), qos=2)


def start_log_command(mqtt_client: mqtt.Client, new_sample_period):
    command_change_sample_period(mqtt_client, new_sample_period)
    log.command_start_logging(mqtt_client)


def set_sampling_period(mqtt_client: mqtt.Client, new_sample_period):
    command_change_sample_period(mqtt_client, new_sample_period)


def on_message (mqtt_client, _user_data, message):
    command_line = message.payload.decode ("utf-8").split ()
    cmd = command_line[0]
    args = command_line[1:]
    if cmd in MQTT_COMMANDS:
        function = MQTT_COMMANDS[cmd]
        if function is None:
            print ('Command {} not implemented!'.format (cmd))
        else:
            if verbose > 0:
                print ('*************** Running [{}]...'.format (' '.join (command_line)))
            try:
                function (mqtt_client, *args)
            except TypeError as e:
                print ('--------------- error {}'.format (e))
    else:
        print ('Unknown command: {}.'.format (cmd))


def finish ():
    pms_sensor.laser_off ()
    pms_sensor.fan_off ()
    gps_sensor.stop_update_gps_thread = True
    print ('Stopped sensor node.')
    mqtt_interface.client_private.loop_stop ()
    mqtt_interface.client_public.loop_stop ()
    log.finish_log ()


if __name__ == '__main__':
    # noinspection SpellCheckingInspection
    MQTT_COMMANDS = {
        'PING': commands.command_ping,
        'SET_TIMEDATE': commands.command_set_time,
        'RESEND': command_resend,
        'TEST_FILTER': pms_sensor_kalman.command_test_filter,
        'SAVE_FILTER': pms_sensor_kalman.command_save_filter,
        'REGISTER_EVENT': command_register_event,
        'DELETE_FRAMES': None,
        'DELETE_LOGS': log.command_delete_logs,
        'POWER_OFF': commands.command_power_off,
        'REBOOT': commands.command_reboot,
        'SET_WIFI': commands.command_set_wifi,
        'KILL': command_kill,
        'START_CAPTURE_FRAMES': command_change_sample_period, # ...
        'STOP_CAPTURE_FRAMES': None,
        'GET_ONE_FRAME': camera_sensor.command_get_one_frame,
        'GET_NEXT_FRAME': None,
        'GET_PREVIOUS_FRAME': None,
        'GET_NEXT_LOG': log.command_get_next_log,
        'GET_PREVIOUS_LOG': log.command_get_previous_log,
        'GET_ALL_FRAMES': None,
        'GET_ALL_LOGS': log.command_get_all_logs,
        'PUBLISH_PRIVATE': None,
        'PUBLISH_PUBLIC': None,
        'STOP_SENSORS': pms_sensor.command_start_sensors,
        'START_SENSORS': pms_sensor.command_stop_sensors,
        'STOP_LOGGING': log.command_stop_logging,
        'START_LOGGING': start_log_command,
        'SET_SAMPLING_PERIOD': set_sampling_period,
    }

    try:
        main ()
    except (InterruptedError, KeyboardInterrupt):
        print ('Catch control-C')
        finish ()
    except Exception as e:
        with open ('/var/log/expolis/sensor-node', 'a+') as fd:
            fd.write (datetime.datetime.now ().isoformat ())
            fd.write ('\n')
            fd.write (str (e))
            fd.write ('\n')
        print("exception")
        finish ()
