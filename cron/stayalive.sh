#!/bin/bash

PROCESS="/home/pi/expolis-sensor-node/sensor_node.py"
WATCHDOG="PATH_TO_WATCHDOG/watchdog"

if pgrep -f "$PROCESS" > /dev/null
then
    if test `find "$WATCHDOG" -mmin +5`
    then
        echo $(date)": rebooting machine" >> /var/log/expolis/crontab
        touch "$WATCHDOG"
        sync
        nohup shutdown -r now
    fi

    if test `find "$WATCHDOG" -mmin +1`
    then
        echo $(date)": killing process" >> /var/log/expolis/crontab
        pkill -9 -f "python3 $PROCESS"
        sleep 1
        echo $(date)": restarting process" >> /var/log/expolis/crontab
        python3 "$PROCESS" > /dev/null &
    fi
else
    echo $(date)": process stopped, restarting process" >> /var/log/expolis/crontab
    python3 "$PROCESS" > /dev/null &
fi
