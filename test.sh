#!/bin/bash
name=${1:-result.txt}
echo "${name}"
date >> $name
df -lh >> $name
echo $PATH >> $name
tail -n 10 /var/log/messages >> $name
