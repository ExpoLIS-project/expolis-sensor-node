from typing import Optional

import paho.mqtt.client as mqtt

import configuration


client_private = None  # type: Optional[mqtt.Client]
client_public = None  # type: Optional[mqtt.Client]

debug = False


def init_mqtt_interface (on_message):
    global client_private, client_public
    client_private = mqtt.Client (client_id=None, clean_session=True)
    client_private.on_publish = on_publish
    client_private.on_message = on_message
    client_private.on_connect = on_connect
    client_private.connect_async ('localhost')
    client_private.loop_start ()

    client_public = mqtt.Client (client_id=None, clean_session=True)
    client_public.on_publish = on_publish
    client_public.on_message = on_message
    client_public.on_connect = on_connect
    client_public.connect_async (configuration.BROKER_ADDRESS)
    client_public.loop_start ()


# callback invoked with MQTT message is sent
def on_publish (_client, _userdata, mid):
    if debug:
        print ("data published " + str (mid) + "\n")


def on_connect (mqtt_client: mqtt.Client, _user_data, _flags, rc):
    print ('Connected with result code {}'.format (rc))
    print ('Subscribing to topic {}'.format (configuration.TOPIC_MANAGEMENT))
    mqtt_client.subscribe (configuration.TOPIC_MANAGEMENT, qos=2)
