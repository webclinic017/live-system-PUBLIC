#!/bin/bash

_pid=$(<pid)
_cmd=$(<cmd)
_update_cron_py="update_cron.py"

# check if pid still running, restart if still running
if ps -p $_pid > /dev/null && [[ $(ps -p $_pid -o command | grep python) = $_cmd ]];
then
    echo "$_pid still running"
    kill -15 $_pid
    if [[ $_cmd =~ $_update_cron_py ]];
    then
        $_cmd && /usr/bin/bash -c "~/live-system/bin/crons/update-cron.sh"
    else 
        $_cmd
    fi
else
    echo "$_pid not running"
fi

