import configparser
import os.path
import pathlib

BASE_PATH = '/home/pi/SensorNode/'

CONFIG_PATH = BASE_PATH + 'Sensor_Node.ini'

config = configparser.ConfigParser ()
config.read (CONFIG_PATH)

BROKER_ADDRESS = config['BASE']['mqtt_broker']
STORAGE_FOLDER = config['BASE']['storage']
SENSOR_NODE_ID = config.getint ('BASE', 'sensor_node_id')
PUBLISH_RATE_PERIOD = int (config['BASE']['publish_rate_period'])

LOGS_FOLDER = os.path.join (STORAGE_FOLDER, 'logs/')
IMAGES_FOLDER = os.path.join (STORAGE_FOLDER, 'images/')

WATCHDOG_PATH = pathlib.Path (os.path.join (STORAGE_FOLDER, 'watchdog'))

IMAGE_FILE_TEMPLATE = '{}Frame_{{iteration}}_{}_{{datetime}}.jpg'.format (IMAGES_FOLDER, SENSOR_NODE_ID)

TOPIC_LOG = 'expolis_project/sensor_nodes/logs/sn_{}'.format (SENSOR_NODE_ID)
# noinspection SpellCheckingInspection
TOPIC_CSV_FILES = 'expolis_project/sensor_nodes/csvfiles/sn_{}'.format (SENSOR_NODE_ID)
# noinspection SpellCheckingInspection
TOPIC_MANAGEMENT = 'expolis_project/sensor_nodes/managment/sn_{}'.format (SENSOR_NODE_ID)
TOPIC_SENSOR_DATA = 'expolis_project/sensor_nodes/sn_{}'.format (SENSOR_NODE_ID)
TOPIC_IMAGE_DATA = 'expolis_project/sensor_nodes/images/sn_{}'.format (SENSOR_NODE_ID)


def save_config ():
    with open (CONFIG_PATH, 'w') as fd:
        config.write (fd)
