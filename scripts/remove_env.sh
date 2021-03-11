#!/bin/bash

sudo rm -rf $@
if [[ $? -ne 0 ]]; then
    #KILL the docker PID and remove folder again
    echo "Kill the docker process and remove the legacy folder again"
ps -ef | grep docker | grep -v grep | awk '{print $2}' | xargs sudo kill -9
sleep 5s
    sudo rm -rf $@
fi

