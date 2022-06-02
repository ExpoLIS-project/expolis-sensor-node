import datetime
import picamera
import time
from io import BytesIO
import base64

import configuration as cfg

camera = None

capture_frames = False

image_file = 'none'

capture_frames_period = 5


def init_camera ():
    global camera

    camera = picamera.PiCamera ()
    camera.resolution = (1024, 768)
    camera.start_preview()
    time.sleep (2)


def command_get_one_frame (mqtt_client):
    my_stream = BytesIO ()
    camera.capture (my_stream, 'jpeg')
    my_stream.seek (0)
    value = base64.b64encode (my_stream.read ())
    mqtt_client.publish (cfg.TOPIC_IMAGE_DATA, value, qos=0)


def step_camera (iteration):
    global image_file

    if capture_frames and iteration % capture_frames_period == 0:
        image_file = cfg.IMAGE_FILE_TEMPLATE.format (
            iteration=iteration,
            datetime=str (datetime.datetime.now ())
                .replace (' ', '__')
                .split ('.')[0]
                .replace (':', '_')
                .replace ('-', '_'),
        )
        camera.capture (image_file)
        print ('Frame captured: {}'.format(image_file))
    else:
        pass

