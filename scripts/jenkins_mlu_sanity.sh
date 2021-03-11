#!/bin/bash
# /c4site/SOBO/Public/zhengh3/scripts/jenkins_mlu_sanity.sh

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

function check_sanity_log()
{
    if [ -e "$SANITY_LOG" ]
    then
        test_status=$(sed -n -r 's/.*MLU Sanity\:Test Status ====> ([A-Za-Z]+).*/\1/p' $SANITY_LOG)
        if [ "$test_status" == "PASSED" ]
        then
            sanity_rc=0
            echo "Sanity passed. Clean $(basename $MLU_SANITY_FILE)."
            rm -f $MLU_SANITY_FILE
        else
            sanity_rc=1
        fi
    else
        die "Sanity log not found"
    fi
}

function mlu_sanity()
{
    [ -z "$MLU_SANITY_FILE" ] && die "Please specify MLU_SANITY_FILE"
    [ -f "$MLU_SANITY_FILE" ] || die "$MLU_SANITY_FILE not found"
    if [[ $MLU_SANITY_FILE =~ .*\.pl ]]
    then
        cp -r $(dirname $MLU_SANITY_FILE) ${WORKSPACE}
        cd ${WORKSPACE}/$(basename $(dirname $MLU_SANITY_FILE))
        cmd="perl $(basename $MLU_SANITY_FILE) -vnxe -block -file -machine $ARRAY_NAME -auto"
        echo "$cmd"
        eval "$cmd"
        SANITY_LOG=$(ls -r vnxe_sanity_log_* | head -1)
        [ -n "$SANITY_LOG" ] && cp $SANITY_LOG $(dirname $MLU_SANITY_FILE) && ls -l $(dirname $MLU_SANITY_FILE)/$SANITY_LOG
    elif [[ $MLU_SANITY_FILE =~ .*\.tar\.gz ]]
    then
        tar zxf $MLU_SANITY_FILE -C ${WORKSPACE}
        sanity_pl=$(find ${WORKSPACE} -name MluSanity.pl)
        cd $(dirname $sanity_pl)
        cmd="perl $(basename $sanity_pl) -vnxe -block -file -machine $ARRAY_NAME -auto"
        echo "$cmd"
        eval "$cmd"
        SANITY_LOG=$(ls -r vnxe_sanity_log_* | head -1)
        [ -n "$SANITY_LOG" ] && cp $SANITY_LOG $(dirname $MLU_SANITY_FILE) && ls -l $(dirname $MLU_SANITY_FILE)/$SANITY_LOG
    fi
}

check_array_available
mlu_sanity
check_sanity_log
exit ${sanity_rc:-255}
