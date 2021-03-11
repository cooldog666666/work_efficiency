#!/bin/bash
. ~/.bashrc

# Colors
BLACK='\e[0;30m'
DARKGRAY='\e[1;30m'
BLUE='\e[0;34m'
LIGHTBLUE='\e[1;34m'
GREEN='\e[0;32m'
LIGHTGREEN='\e[1;32m'
CYAN='\e[0;36m'
LIGHTCYAN='\e[1;36m'
RED='\e[0;31m'
LIGHTRED='\e[1;31m'
PURPLE='\e[0;35m'
LIGHTPURPLE='\e[1;35m'
BROWN='\e[0;33m'
YELLOW='\e[1;33m'
LIGHTGRAY='\e[0;37m'
WHITE='\e[1;37m'
UNSETCOLOR='\e[m'
CERROR="$RED[ERROR]$UNSETCOLOR"
CINFO="$BROWN[INFO]$UNSETCOLOR"
CWARN="$LIGHTRED[WARN]$UNSETCOLOR"
CRUN="$BROWN[RUN]$UNSETCOLOR"

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

source $HOME/.profile

user='zhengh3'
passwd=$(echo $CORPPASSWD|base64 -d)

cmd="accurev login -n $user '$passwd'"
logger "$cmd"
start_with_progress $cmd

echo $SWPSTDOUT
echo $SWPSTDERR

cmd="python3 /c4site/SOBO/Public/zhengh3/scripts/git_login.py;"
logger "$cmd"
start_with_progress $cmd

echo $SWPSTDOUT
echo $SWPSTDERR



