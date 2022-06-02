#!/bin/bash

PROCESS="/home/pi/expolis-sensor-node/sensor_node.py"

if pgrep -f "$PROCESS" > /dev/null
then
    if test `find "/media/pi/447AE8637AE8536A/watchdog" -mmin +5`
    then
        echo $(date)": rebooting machine" >> /var/log/expolis/crontab
        touch "/media/pi/447AE8637AE8536A/watchdog"
        sync
        nohup shutdown -r now
    fi

    if test `find "/media/pi/447AE8637AE8536A/watchdog" -mmin +1`
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
