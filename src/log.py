"""Provides functions to log sensor data in the backup pen in each sensor node.

Data gathered by the sensors is always published to the MQTT server.  Sensor
data is also stored in a FIFO queue which provides a temporary storage in
case communication fails for a short time.

This module provides a last case scenario against communication failures, as
sensor data is stored in the backup pen that equips each sensor node.  At
every time step, function step_log_csv is called and if logging is enabled a
new entry is added to the current log file.

Log files have a limit on the number of entries, which is stored in the
configuration file.  Function start_log_csv creates a new log file.

This module also provides functions that implement the commands that the
sensor node can receive on the management mqtt topic.

In order to obtain the logs, without requiring physical access to the sensor
node, a protocol using the mqtt was devised.  Whenever a client wants the logs,
it sends the command ``GET_ALL_LOGS``. The function that processes this command
creates a thread (in order to not lock the mqtt thread).  Each log file is sent
as a mqtt message. The handling thread waits before sending the next log file.
The client may also request resending the current log file.

Main Function
-------------

step_log_csv
    The main function of this module receives the iteration number, current
    timestamp, sensor data, current event, and current grabbed image name. If
    logging is enabled, writes the above data in the current log file. If the
    line limit has been reached, starts a new log file.

Command Functions
-----------------

The following functions are called whenever the sensor node receives a command
through the management MQTT topic. As has been defined, the first argument of
these functions is the ``paho.mqtt.client.Client`` that sent the command.

command_start_logging
    Enables logging which causes a new log file to be created. This means that
    the previous file will not reach the line limit.

command_stop_logging
    Disables logging.  If logging was enabled, the current log file is closed.
    If the sensor node is turned off, when it is powered on, logging will not
    be enabled.

command_get_all_logs
    Sends all files that are stored in the log folder in the backup pen. This
    is handled by function thread_upload_logs_run which is run in its own
    thread.

command_get_next_log
    Causes the function thread_upload_logs_run to send the next log file.

command_get_previous_log
    Causes the function thread_upload_logs_run to send the current log file.

command_delete_logs
    Deletes all csv files in the log folder in the backup pen.

Other Functions
---------------

init_log
    Function called to *initialise* the variables in this module.

start_log_csv
    Starts a new log file. Closes the current file (if logging is enabled).

close_log_csv
    Closes the current log file.

restart_log_csv
    Opens the log file where data was being written the last time the sensor
    node software was running.  This function is called at initialisation
    time.

thread_upload_logs_run
    This function handles the uploading of the log files.
"""

import datetime
import os
import subprocess

import paho.mqtt.client as mqtt
import threading
from typing import Optional, Tuple
from typing.io import IO

import configuration
import pms_sensor_kalman

log_data = False  # type: bool
"""Whether logging is enabled or not."""
current_log_file = None  # type: Optional[IO]
"""The current log file handler descriptor."""
number_lines_log_file = 0  # type: int
"""The number of lines int the current log file."""
last_csv_open = None  # type: Optional[str]
"""The file name of the current log file."""
mutex = threading.Semaphore ()
# Mutex used when writing sensor data and manipulating corresponding log variables

uploading_logs = False
"""Whether we are currently uploading the log files or not."""
queue_upload = threading.Semaphore ()
"""*Queue* where clients wait when requesting all log files.

We only permit one client at time. Handling multiple clients is not a priority,
since sensor data should mainly be accessed through the ExpoLIS server."""
client_wants_next_log = False
"""Whether we should upload the next log file or resend the current log file."""
is_waiting_answer = False
"""Are we waiting for an answer after sending a log file."""
abort_upload = False
"""Should we abort the upload.

Used when we need to terminate the program."""
client_answered = threading.Condition ()


def init_log () -> None:
    """Initialises the variables in the log module.

    Logging is written in the previous log file depending on configuration
    parameters.
    """
    if configuration.config.getboolean ('BASE', 'log_csv_boot'):
        print ('Restarting log from file {}.'.format (configuration.config.get ('BASE', 'current_csv')))
        restart_log_csv (configuration.config.get ('BASE', 'current_csv'))
    else:
        # TODO: Check with Pedro Santana whether we should start logging or not.
        start_log_csv ()


def finish_log () -> None:
    global is_waiting_answer, abort_upload

    client_answered.acquire ()
    abort_upload = True
    if uploading_logs and is_waiting_answer:
        is_waiting_answer = False
        client_answered.notify ()
    client_answered.release ()


def step_log_csv (
        iteration: int,
        step_timestamp: float,
        gps_data: Tuple,
        pms_data: Tuple,
        pm_honeywell_data: Tuple,
        other_sensor_data: Tuple,
        event: str,
        image_file: str,
        ip: str,
        sampling_period: int,
) -> None:
    """Writes the current iteration, timestamp, event and grabbed image, and
    sensor data to the log file.

    Starts a new log file if the maximum number of lines has been reached.
    Log files are written to the backup pen in the sensor node.

    :param iteration: the current iteration counted from the start of the
        program.
    :param step_timestamp: the current time stamp.
    :param gps_data: the gps data.
    :param pms_data: the PM raw and filtered data.
    :param pm_honeywell_data: the PM data gathered by the Honeywell sensor.
    :param other_sensor_data: other sensor data (CO, NO2, temperature,
       pressure, humidity and power voltage.
    :param event: the current registered event.
    :param image_file: the current grabbed image.
    :param ip:
    :param sampling_period: time between sampling the sensors (in seconds).
    """
    global number_lines_log_file
    if log_data and number_lines_log_file > 3600 * 4:
        start_log_csv ()
    mutex.acquire ()
    if log_data:
        gas_co_value_1, gas_co_value_2, gas_no2_value_1, gas_no2_value_2, \
            temperature_value, pressure_value, humidity_value, \
            power_supply_value, \
            acceleration_value_1, acceleration_value_2, acceleration_value_3 = other_sensor_data
        time = datetime.datetime.fromtimestamp (step_timestamp).isoformat (timespec='seconds')
        fields = [
                     iteration, time,
                 ] + list (gps_data) + [
                     gas_co_value_1, gas_co_value_2, gas_no2_value_1, gas_no2_value_2
                 ] + list (pms_data) + [
                     temperature_value, pressure_value, humidity_value, power_supply_value,
                     pms_sensor_kalman.kp_base, pms_sensor_kalman.kd_base, event, image_file,
                     acceleration_value_1, acceleration_value_2, acceleration_value_3
                 ] + list (pm_honeywell_data)
        fields = [str (s).replace ('.', ',') for s in fields]
        fields = fields + [ip, str(sampling_period)]
        line = ' '.join (fields)
        current_log_file.write (line + '\n')
        current_log_file.flush ()
        number_lines_log_file += 1
    mutex.release ()


def thread_upload_logs_run (mqtt_client: mqtt.Client) -> None:
    """Thread responsible for uploading log files to the MQTT client.

    Each log file is sent in its own mqtt message.  In order to not overload
    the mqtt server, there is protocol to request the next log file.  There is
    also the possibility to request the current log file.

    After sending a file, the thread waits for a response from the client:

    * the command GET_PREVIOUS_LOG causes the thread to resend the current
      log file;
    * the command GET_NEXT_LOG makes the thread go to to next log file.

    :param mqtt_client: the mqtt client where the log files are published.
    """
    global uploading_logs, client_wants_next_log, is_waiting_answer

    queue_upload.acquire ()
    # flush the current log file
    mutex.acquire ()
    if log_data:
        current_log_file.flush ()
    mutex.release ()
    # upload files main loop
    client_answered.acquire ()
    uploading_logs = True
    number_files = len (os.listdir (configuration.LOGS_FOLDER))
    # TODO: Only send the files that match the log file pattern.
    for idx, csv_file in enumerate (os.listdir (configuration.LOGS_FOLDER)):
        print ('Processing file {} of {}...'.format (idx + 1, number_files))
        try:
            client_wants_next_log = False
            while not client_wants_next_log:
                print ('Uploading file {}'.format (csv_file))
                with open (configuration.LOGS_FOLDER + csv_file, 'r') as fd:
                    content = fd.read ()
                    mqtt_client.publish (configuration.TOPIC_CSV_FILES, content, qos=2)
                print ('Sent file {}'.format (csv_file))
                is_waiting_answer = True
                client_answered.wait ()
        except FileNotFoundError:
            print ('File {} has been deleted!'.format (csv_file))
        if abort_upload:
            break
    if not abort_upload:
        mqtt_client.publish (configuration.TOPIC_LOG, 'all logs sent', qos=2)
    uploading_logs = False
    client_answered.release ()
    queue_upload.release ()
    if abort_upload:
        print ('Aborted upload!')
    else:
        print ('All files uploaded')


def start_log_csv () -> None:
    """Starts a new log file.

    Closes the current log file.  Enables logging.  Saves the log filename in
    the configuration file.
    """
    global log_data, current_log_file, number_lines_log_file, last_csv_open

    print ("creating log file ...")
    mutex.acquire ()
    log_data = True
    close_log_csv ()

    initial_datetime = str (datetime.datetime.now ()) \
        .replace (' ', '__') \
        .split ('.')[0] \
        .replace (':', '_') \
        .replace ('-', '_')
    csv_filename = '{}Node_{}_Remote_Log___{}.csv'.format (
        configuration.LOGS_FOLDER, configuration.SENSOR_NODE_ID, initial_datetime)
    current_log_file = open (csv_filename, 'w+')
    description = 'Node_{}_Remote_Log___{}\n'.format (configuration.SENSOR_NODE_ID, initial_datetime)
    current_log_file.write (description)
    # noinspection SpellCheckingInspection
    header = 'sample date_time ' \
             'latitude longitude gps_error ' \
             'co_1 co_2 no2_1 no2_2 ' \
             'pm1_opc pm25_opc pm10_opc pm1_opc_filt pm2_opc_filt pm_10_opc_filt ' \
             'temperature pressure humidity ' \
             'power kp_base kd_base event image_file ' \
             'acceleration_1 acceleration_2 acceleration_3 ' \
             'pm1_honwell pm25_honwell pm4_honwell pm10_honwell ip sampling_period\n'
    current_log_file.write (header)
    last_csv_open = csv_filename
    number_lines_log_file = 0
    # update configuration
    configuration.config['BASE']['current_csv'] = csv_filename
    configuration.save_config ()
    mutex.release ()


def restart_log_csv (csv_filename: str) -> None:
    """Reopens the log file from the last time the sensor node software was
    running.

    This function is only called when this module initialises.

    :param csv_filename: log filename.
    """
    global log_data, current_log_file, number_lines_log_file, last_csv_open

    if os.path.exists (csv_filename):
        last_csv_open = csv_filename
        print ("restarting log file " + csv_filename)
        number_lines_log_file = sum (1 for _ in open (csv_filename, 'r'))
        log_data = True
        current_log_file = open (csv_filename, 'a+')
    else:
        start_log_csv ()


def close_log_csv () -> None:
    """Closes the current log file."""
    global current_log_file
    if current_log_file is not None:
        current_log_file.close ()
        current_log_file = None


def command_delete_logs (mqtt_client: mqtt.Client) -> None:
    """Deletes all log files except the current open log file.

    :param mqtt_client: mqtt client where log messages are published.
    """
    global current_log_file
    mqtt_client.publish (configuration.TOPIC_LOG, 'received delete log files', qos=2)
    mutex.acquire ()
    if log_data:
        current_log_file.close ()
        subprocess.call ('mv {} {}restore'.format (last_csv_open, configuration.LOGS_FOLDER), shell=True)
    subprocess.call ('rm -f {}/*.csv'.format (configuration.LOGS_FOLDER), shell=True)
    if log_data:
        subprocess.call ('mv {}restore {}'.format (configuration.LOGS_FOLDER, last_csv_open), shell=True)
        current_log_file = open (last_csv_open, 'a+')
    mutex.release ()
    mqtt_client.publish (configuration.TOPIC_LOG, 'log files deleted', qos=2)


def command_get_next_log (_mqtt_client: mqtt.Client) -> None:
    """Instructs the thread that uploads log files to process the next log
    file.

    :param _mqtt_client: not used.
    """
    global client_wants_next_log, is_waiting_answer

    client_answered.acquire ()
    if uploading_logs:
        if is_waiting_answer:
            client_wants_next_log = True
            is_waiting_answer = False
            client_answered.notify ()
            print ('Finished command command_get_next_log')
        else:
            print ('I''m not waiting for an answer')
    else:
        print ('In command_get_next_log but not uploading logs!')
    client_answered.release ()


def command_get_previous_log (_mqtt_client: mqtt.Client) -> None:
    """Instructs the thread that uploads log files to resend the current log
    file.

    :param _mqtt_client: not used.
    """
    global client_wants_next_log, is_waiting_answer

    client_answered.acquire ()
    if uploading_logs:
        if is_waiting_answer:
            client_wants_next_log = False
            is_waiting_answer = False
            client_answered.notify ()
            print ('Finished command command_get_previous_log')
        else:
            print ('I''m not waiting for an answer')
    else:
        print ('In command_get_previous_log but not uploading logs!')
    client_answered.release ()


def command_get_all_logs (mqtt_client: mqtt.Client) -> None:
    """Starts the thread that uploads log files.

    :param mqtt_client: mqtt client where log messages are published.
    :return:
    """
    mqtt_client.publish (configuration.TOPIC_LOG, 'received get all logs', qos=2)
    if not abort_upload:
        threading.Thread (
            target=thread_upload_logs_run,
            args=(mqtt_client,),
        ).start ()


def command_stop_logging (mqtt_client: mqtt.Client) -> None:
    """Disables logging.

    Closes the current log file and updates the configuration parameter for
    logging.

    :param mqtt_client: mqtt client where log messages are published.
    """
    global log_data
    mqtt_client.publish (configuration.TOPIC_LOG, 'received stop logging', qos=2)
    print ("closing log file ...")
    mutex.acquire ()
    log_data = False
    close_log_csv ()
    configuration.config['BASE']['log_csv_boot'] = 'False'
    configuration.save_config ()
    mutex.release ()


def command_start_logging (mqtt_client: mqtt.Client) -> None:
    """Enables logging.

    Opens a new log file and updates the configuration parameter for logging.

    :param mqtt_client: mqtt client where log messages are published.
    """
    mqtt_client.publish (configuration.TOPIC_LOG, 'received start logging', qos=2)
    start_log_csv ()
    configuration.config['BASE']['log_csv_boot'] = 'True'
    configuration.save_config ()
