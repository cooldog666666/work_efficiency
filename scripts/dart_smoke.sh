#!/bin/bash -e

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
    ws pop --name $TARGET_WS_NAME
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

if [ ! -z "$TARGET_STREAM_NAME" ] && [ -z "$TARGET_WS_NAME" ]
then
    echo -e "==========\nStarting patching ...\n=========="
    if [ -e $PATCH_DIR ]
    then
        cd $PATCH_DIR
        until mkdir .patch_lock; do
            echo "attempt acquire lock for patch"
            sleep 3
        done
        PATCH_FILES=(`ls`)
        for patch in ${PATCH_FILES[@]}
        do
            echo "handle patch file: $patch"
            mv $patch $wspace_dir
        done
        rmdir .patch_lock
        cd $wspace_dir
        for patch in ${PATCH_FILES[@]}
        do
            echo "Update code for patch $patch"
            if patch --dry-run -p0 -t < $patch
            then
                patch -p0 < $patch
                echo "Patched $patch successfully"
            else
                echo "Failed with attempt to apply the patch $patch."
                exit 1
            fi
        done
    else
        echo "No patch dir exist. Skip patching."
    fi
fi  

echo -e "==========\nBegin dartmake ...\n=========="

cd sade/src/dart/Dart/server/x86_64.bin
/c4site/SOBO/Public/zhengh3/tools/dartmake_m all

echo -e "==========\nCollect NAS.exe and smoke_unit_test ...\n=========="

ls -l NAS.exe
gzip NAS.exe
ls -l NAS.exe.gz
mv NAS.exe.gz NAS.exe
ls -l NAS.exe

cd $WORKSPACE/sade/src/dart/Dart/server/src/dvt/
tar zcf smoke_unit_test.tgz smoke_unit_test
ls -l smoke_unit_test.tgz
