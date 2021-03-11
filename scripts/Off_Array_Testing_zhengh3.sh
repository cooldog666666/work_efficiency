#!/bin/bash
set -x
EXITIFERROR='+e'
set ${EXITIFERROR}

function finish() {
    echo "[INFO] Reset all root file permissions to current user: $USER"
    local _user=$(id $USER -u)
    local _group=$(id $USER -g)
    cd $WORKSPACE && sudo chown -R ${_user}:${_group} * .*
    echo "[INFO] Reset all root file permissions to current user: $USER [DONE]"
}
# trap finish EXIT SIGHUP SIGINT SIGTERM

function die() {
    printf '[ERROR] %s\n' "$@" >&2 
    exit 255 
}

function catch_error() {
    die "An unhandled error occurred at $BASH_SOURCE:$BASH_LINENO"
}

function partialmake() {
    if [ -z "$1" ]; then
        echo "[usage] $0 {safe | sade | sim | ufs64sim} [<sub_dir>]"
        return 1
    fi
    target=$1
    sub=$2
    proot=${DEV_WORKSPACE}
    export CFG_FLAVOR=DEBUG
    if [ "$target" == "sim" ]; then
        target="safe"
        sub="layered/MLU/krnl/cbfs_driver"
    fi
    if [ "$target" == "ufs64sim" ]; then
        target="safe"
        sub="layered/MLU/test/MUT/ufs64"
    fi
    if [ -z "$sub" ]; then
        if [ "$target" == "safe" ]; then
            sub="layered/MLU"
        fi
        if [ "$target" == "sade" ]; then
            sub="Dart"
        fi
    fi
    declare required
    if [ -e "$proot/build/tags/KHDATAPATH" ]; then
        required=`grep SLES $proot/build/tags/KHDATAPATH | awk '{print $2}'`
    fi
    echo "Required Build ENV: $required"
    declare present
    if [ -e "/etc/c4buildversion" ]; then
        present=`cat /etc/c4buildversion | awk '{print $1}'`
    fi
    echo "Present Build ENV: $present"
    if [ -n "$required" ] && [ -n "$present" ] && [ "$required" != "$present" ]; then 
        echo "Switch to Build ENV: $required"
        (go12sp1 --dist $required -- $proot --- -c "cd $proot/$target && ./build.sh -t GNOSIS -f DEBUG --subdir $sub --build-only --no-package") 2>&1 | tee $proot/partialmake.log
    else
        (cd $proot/$target && ./build.sh -t GNOSIS -f DEBUG --subdir $sub --build-only --no-package) 2>&1 | tee $proot/partialmake.log
    fi
    return $?
}

function run_partialmake() {
    cd ${DEV_WORKSPACE}
    if [[ ${RUN_PARTIALMAKE} == true ]]
    then
        echo "[INFO] Run partial make"
        partialmake safe
        return $?
    else
        echo "[INFO] Skip dartmake"
        return 0
    fi
}

function clean_results() {
    set +e
    echo "[INFO] Cleaning existing Results ..."
    sudo rm -rf ${DEV_WORKSPACE}/safe/Targets/armada64_checked/simulation/exec/Results*
    set ${EXITIFERROR}
}

function change_owner() {
    set +e
    echo "[INFO] Change owner"
    sudo chown c4dev:users ${DEV_WORKSPACE}/safe/Targets/armada64_checked/simulation/exec -R
    set ${EXITIFERROR}
}

function run_mutRegress() {
    cd ${DEV_WORKSPACE}/safe/safe_util/adebuild.mod/
    pwd
    
    if ( "${DEFAULT_TEST_LIST}" == "true"); then
    #  Really a bug,  this code used to always process Test_List.JSON, while it should have use ${MutRegress_Config_File}
    # Actual bug, mutRegress.pl requires 2 config files, the first to specify a group, the second containing the list of tests.
    # Need tox fix, mutRegress.pl to be able to process config files containing list of tests.
        echo executing sudo ./mutRegress.pl -memory_nocheck -view ${DEV_WORKSPACE}/safe -configDir ${MutRegress_Config_Directory} -nocleanup -list Test_List.JSON -verbosity ktrace -timeout ${TIMEOUT} -iteration ${ITERATION} -worker ${Worker_Threads} -extraCli "${EXTRACLI}"
        sudo ./mutRegress.pl -memory_nocheck -view ${DEV_WORKSPACE}/safe -configDir ${MutRegress_Config_Directory} -nocleanup -list Test_List.JSON -verbosity ktrace -timeout ${TIMEOUT} -iteration ${ITERATION} -worker ${Worker_Threads} -extraCli "${EXTRACLI}"
    else
        echo executing sudo ./mutRegress.pl -memory_nocheck -view ${DEV_WORKSPACE}/safe -configDir ${MutRegress_Config_Directory} -nocleanup -list ${MutRegress_Config_file} -verbosity ktrace -timeout ${TIMEOUT} -iteration ${ITERATION} -worker ${Worker_Threads} -extraCli "${EXTRACLI}"
        sudo ./mutRegress.pl -memory_nocheck -view ${DEV_WORKSPACE}/safe -configDir ${MutRegress_Config_Directory} -nocleanup -list ${MutRegress_Config_file} -verbosity ktrace -timeout ${TIMEOUT} -iteration ${ITERATION} -worker ${Worker_Threads} -extraCli "${EXTRACLI}"
    fi
    
    return $?
}

function report_parse() {
    ls -ld ${DEV_WORKSPACE}/safe/Targets/armada64_checked/simulation/exec/Results*
    
    if [ -f "${DEV_WORKSPACE}/safe/safe_util/adebuild.mod/mutRegressReportParser.pl" ]
    then
      ${DEV_WORKSPACE}/safe/safe_util/adebuild.mod/mutRegressReportParser.pl -l ${DEV_WORKSPACE}/safe/Targets/armada64_checked/simulation/exec -s ${DEV_WORKSPACE}/suite.log -x ${DEV_WORKSPACE}/suite.xml -j ${DEV_WORKSPACE}/suite.json
      (cd ${DEV_WORKSPACE} && sudo ${DEV_WORKSPACE}/safe/safe_util/adebuild.mod/cbfssim_errs.sh)
    else
      ~bucklm2/bin/mutRegressReportParser.pl -l ${DEV_WORKSPACE}/safe/Targets/armada64_checked/simulation/exec -s ${DEV_WORKSPACE}/suite.log -x ${DEV_WORKSPACE}/suite.xml -j ${DEV_WORKSPACE}/suite.json
      (cd ${DEV_WORKSPACE} && sudo ~bucklm2/bin/cbfssim_errs.sh)
    fi
    
    find ${DEV_WORKSPACE}/safe/Targets/armada64_checked/simulation/exec -name summary.txt -type f| xargs cat | tee ${DEV_WORKSPACE}/summary.log
} 

function main() {
    cd ${DEV_WORKSPACE}
    
    run_partialmake || die "Partialmake failed"
    clean_results
    run_mutRegress
    ret=$?
    change_owner
    report_parse
    exit $ret
}

main
