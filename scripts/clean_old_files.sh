#!/bin/bash

# Default settings
target_dev=/dev/sdb1
expiration_time=15    # days
size_threshold=209715200

# Colors
Black='\e[0;30m'
DarkGray='\e[1;30m'
Blue='\e[0;34m'
LightBlue='\e[1;34m'
Green='\e[0;32m'
LightGreen='\e[1;32m'
Cyan='\e[0;36m'
LightCyan='\e[1;36m'
Red='\e[0;31m'
LightRed='\e[1;31m'
Purple='\e[0;35m'
LightPurple='\e[1;35m'
Brown='\e[0;33m'
Yellow='\e[1;33m'
LightGray='\e[0;37m'
White='\e[1;37m'
UNSETCOLOR='\e[m'
CERROR="$Red[ERROR]$UNSETCOLOR"
CINFO="$Brown[INFO]$UNSETCOLOR"
CWARN="$LightRed[WARN]$UNSETCOLOR"
CRUN="$Brown[RUN]$UNSETCOLOR"

function die() {
    printf "$Red[ERROR]$UNSETCOLOR %s\n" "$@" >&2
    exit 255
}

declare SWPSTDOUT
declare SWPSTDERR
function start_with_progress()
{
    local bgpid
    echo -en "$CRUN '$@' "
    local stdout_file=/tmp/$$_start_with_progress_stdout
    local stderr_file=/tmp/$$_start_with_progress_stderr
    eval "$@" 1>${stdout_file} 2>${stderr_file} & bgpid=$!
    while ps | grep -v grep | grep -q "$bgpid"
    do
        echo -n '.'
        sleep 3
    done
    wait $bgpid
    local exit_code=$?
    echo " ($exit_code)"
    SWPSTDOUT=$(<${stdout_file})
    SWPSTDERR=$(<${stderr_file})
    return $exit_code
}

declare -a mountpoints_list
function get_mountpoints()
{
# ci-sles12-slave-478:~ # mount |grep '/dev/sdb1 '
# /dev/sdb1 on /user_data_disk type xfs (rw,relatime,attr2,inode64,noquota)
# /dev/sdb1 on /home type xfs (rw,relatime,attr2,inode64,noquota)
# /dev/sdb1 on /c4_working type xfs (rw,relatime,attr2,inode64,noquota)
# /dev/sdb1 on /var/cache/ccache type xfs (rw,relatime,attr2,inode64,noquota)
# /dev/sdb1 on /user_data_disk/docker/devicemapper type xfs (rw,relatime,attr2,inode64,noquota)

    echo -e "$CINFO Check mountpoints on $target_dev ..."
    mountpoints_list=($(mount |grep "$target_dev" | awk '{print $3}'))
}

function main()
{
    get_mountpoints
    for mp in ${mountpoints_list[@]}
    do
        start_with_progress du -s $mp
        echo $SWPSTDOUT
        mp_size=$(echo $SWPSTDOUT|sed -rn '/[0-9]+/ s/([0-9]+) .*/\1/p')
        if [ "$mp_size" -gt "$size_threshold" ]
        then
            echo -e "$CINFO Cleaning on $mp (expiration_time: $expiration_time days) ..."
            find $mp -atime +${expiration_time} -a -mtime +${expiration_time} -print0 | xargs -0 rm
            echo "[DONE]"
        fi
    done
}

if [ -b "$1" ]
then
    target_dev=$1
fi

main

