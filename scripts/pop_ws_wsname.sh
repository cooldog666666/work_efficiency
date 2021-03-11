#!/bin/bash

function usage()
{
    cat << EOF
Usage:
$0 [workspace name|stream name]
EOF
    exit ${1:-255}
}

wspace_dir=$(pwd)
echo "Begin task under $wspace_dir"

TARGET_WS_NAME=${WSPACE_NAME:-''}
TARGET_STREAM_NAME=${STREAM_NAME:-''}
if [ -z "$TARGET_WS_NAME" ] && [ -z "$TARGET_STREAM_NAME" ];
then
    echo "[ERROR] No workspace or stream specified. Exit." >& 2
    usage 4
fi

accurev logout >/dev/null 2>&1 
ACCUREV_USER="svc_usdciauto"
ACCUREV_PWD="y!4ataZaTrun+Th"
accurev login $ACCUREV_USER $ACCUREV_PWD



echo -e "==========\nBegin to setup workspace ...\n=========="
rm -rf *

if [ ! -z "$TARGET_WS_NAME" ]
then
    BASIS_STREAM=`accurev show -s $TARGET_WS_NAME streams -fx | sed -nr 's/\s*basis="(.+)".*/\1/p'`
    echo "Target workspace name: $TARGET_WS_NAME (basis: $BASIS_STREAM)"
    modSetup -op pop -wspace $TARGET_WS_NAME -dir . c4core safe sade image -noconfirm
    setupWspace -stream $TARGET_WS_NAME -dir .
    ret_status=$?
elif [ ! -z "$TARGET_STREAM_NAME" ]
then
    echo "Target stream name: $TARGET_STREAM_NAME"
    modSetup -op pop -stream $TARGET_STREAM_NAME -dir . c4core safe sade image -noconfirm
    setupWspace -stream $TARGET_STREAM_NAME -dir .
    ret_status=$?
else
    echo "Something is wrong..."
    exit 1
fi
#ret_status=0

if [ "$ret_status" -eq 0 ]
then
    echo "Populate complete."
else
    echo "Populate failed."
    exit 1
fi

