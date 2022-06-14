#!/usr/bin/env python3
import configparser
import os.path
import shutil


def read_value (prompt: str, default, convert=None, check=None):
    full_prompt = '{} [{}]? '.format (prompt, default) if default is not None else (prompt + '? ')
    result = input (full_prompt)
    if default is not None:
        result = default
    if result == '' and default is None:
        print ('Must enter a value!')
        return read_value (prompt, default, convert, check)
    if result != '' and convert is not None:
        try:
            result = convert (result)
        except ValueError:
            print ('Conversion error!')
            return read_value (prompt, default, convert, check)
    if check is not None and not check (result):
        print ('Check error!!!')
        return read_value (prompt, default, convert, check)
    return default if result == '' else result


def check_path (x):
    if x == '':
        print ('Please enter a path!')
        return False
    elif not os.path.exists (x):
        print ('USB path does not exists!')
        return False
    elif not os.path.isdir (x):
        print ('Path must be a directory!')
        return False
    else:
        return True


source_folder = os.path.dirname (os.path.abspath (__file__))

sensor_node_id = read_value ('Sensor node ID', 1, int)
mqtt_broker = read_value ('MQTT broker', 'mqtt.expolis.pt')
kp = read_value ('Constant Kp used by Kalman filter', 20, float)
kd = read_value ('Constant Kd used by Kalman filter', 50, float)
storage = read_value ('Path where USB pen is mounted', None, None, check_path)

CONFIG_PATH = '/home/pi/SensorNode/Sensor_Node.ini'
if not os.path.exists (os.path.dirname (CONFIG_PATH)):
    os.mkdir (os.path.dirname (CONFIG_PATH))

config = configparser.ConfigParser ()
config ['BASE'] = {}
config ['BASE']['sensor_node_id'] = str (sensor_node_id)
config ['BASE']['mqtt_broker'] = mqtt_broker
config ['BASE']['storage'] = storage
config ['BASE']['publish_rate_period'] = str (1)
config ['BASE']['log_csv_boot'] = 'True'
config ['BASE']['kp'] = str (kp)
config ['BASE']['kd'] = str (kd)

with open (CONFIG_PATH, 'w') as fd:
    config.write (fd)

DESTINATION = '/home/pi/expolis-sensor-node'
if not os.path.exists (DESTINATION):
    os.mkdir (DESTINATION)
files = [
    'camera_sensor.py',
    'commands.py',
    'configuration.py',
    'gps_sensor.py',
    'honeywell_sensor.py',
    'log.py',
    'mqtt_interface.py',
    'other_sensors.py',
    'pms_sensor_kalman.py',
    'pms_sensor.py',
    'sensor_node.py',
]
print ('Copying source files to {}...'.format (DESTINATION))
for a_file in files:
    shutil.copy (
        os.path.join (source_folder, os.path.join ('src', a_file)),
        DESTINATION,
    )

with open (os.path.join (source_folder, 'cron/stay-alive.sh')) as fd:
    content = fd.readlines ()
content [3] = content [3].replace ('PATH_TO_WATCHDOG', storage)
with open ('/etc/cron.d/expolis-stay-alive.sh', 'w') as fd:
    fd.writelines (content)
print ('Do not forget to edit crontab to add a reference to the ExpoLIS stay-alive.sh script.')
