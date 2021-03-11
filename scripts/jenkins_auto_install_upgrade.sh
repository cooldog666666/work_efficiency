#!/bin/bash
# /c4site/SOBO/Public/zhengh3/scripts/jenkins_auto_install_upgrade.sh

function die()
{
    echo "[ERROR] $@"
    exit 255
}

function check_array_available()
{
    [ -z "$ARRAY_NAME" ] && die "ARRAY_NAME not specified."
    if ! swarm $ARRAY_NAME > /dev/null
    then
        die "$ARRAY_NAME is not available."
    fi
}

function manual_install_upgrade()
{
    [ -z "$IMAGE_PATH" ] && [ -z "$UPPKG_PATH" ] && die "Invailable IMAGE_PATH and UPPKG_PATH"
    cmd="/c4shares/auto/devutils/bin/auto_install_upgrade.sh -a ${ARRAY_NAME}"
    [ -n "$IMAGE_PATH" ] && cmd="$cmd -i $IMAGE_PATH"
    [ -n "$UPPKG_PATH" ] && cmd="$cmd -u $UPPKG_PATH"
    [ -n "$LICENSE" ] && [ -e "$LICENSE" ] && cmd="$cmd -X $LICENSE"
    echo "[CMD] $cmd"
    eval "$cmd"
}

function upstreamtrigger_install_upgrade()
{
    upstream_build_archive_path=${CI_BUILD_OUTPUT_BASE}/${UPSTREAM_BUILD_INFO}
    [ ! -d $upstream_build_archive_path ] && die "${upstream_build_archive_path} is not found or not a dir."

    IMAGE_PATH=$(find ${upstream_build_archive_path}/image -name "OS-*.tgz.bin" | head -n 1)
    echo "[INFO] Found IMAGE : $IMAGE_PATH"
    UPPKG_PATH=$(find ${upstream_build_archive_path}/image -name "Unity-*.tgz.bin.gpg" | head -n 1)
    echo "[INFO] Found UPPKG : $UPPKG_PATH"
    [ -z "$IMAGE_PATH" ] && [ -z "$UPPKG_PATH" ] && die "Invailable IMAGE_PATH and UPPKG_PATH"
    cmd="/c4shares/auto/devutils/bin/auto_install_upgrade.sh -a ${ARRAY_NAME}"
    [ -n "$IMAGE_PATH" -a "${INSTALL}" == true ] && cmd="$cmd -i $IMAGE_PATH"
    [ -n "$UPPKG_PATH" -a "${UPGRADE}" == true ] && cmd="$cmd -u $UPPKG_PATH"
    [ -n "$LICENSE" ] && [ -e "$LICENSE" ] && cmd="$cmd -X $LICENSE"
    echo "[CMD] $cmd"
    eval "$cmd"
}

function install_upgrade()
{
    if [ -z "${UPSTREAM_BUILD_INFO}" ]
    then
        manual_install_upgrade
    else
        upstreamtrigger_install_upgrade
    fi
}


for i in ARRAY_NAME IMAGE_PATH UPPKG_PATH INSTALL UPGRADE LICENSE MLU_SANITY UPSTREAM_BUILD_INFO CI_BUILD_OUTPUT_BASE
do
    echo "[PARAMETER] $i : '${!i}'"
done

#if [ "$BUILD_CAUSE" == UPSTREAMTRIGGER ]
#then
    #if [ -z "${UPSTREAM_BUILD_INFO}" ]
    #then
        #die "UPSTREAM_BUILD_INFO not set."
    #fi
    #check_array_available
    #upstreamtrigger_install_upgrade
#else
    #check_array_available
    #manual_install_upgrade
#fi
check_array_available
install_upgrade
