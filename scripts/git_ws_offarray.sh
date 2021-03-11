#!/bin/bash

function finish() {
    echo "[INFO] Reset all root file permissions to current user: $USER"
    local _user=$(id $USER -u)
    local _group=$(id $USER -g)
    cd $WORKSPACE && sudo chown -R ${_user}:${_group} * .*
    echo "[INFO] Reset all root file permissions to current user: $USER [DONE]"
}
trap finish EXIT SIGHUP SIGINT SIGTERM

function die() {
    printf 'ERROR: %s\n' "$@" >&2
    exit 255
}

function catch_error() {
    die "An unhandled error occurred at $BASH_SOURCE:$BASH_LINENO"
}

function get_property() {
    var=$1
    echo "[VAR] $var: ${!var}"
}

cd ${WORKSPACE} || die "${WORKSPACE} not found."

echo -e "####################\n# OffArray Testing #\n####################"
if [[ ! $BUILD_CMD =~ .*safe.* && ! $BUILD_CMD =~ .*image.* ]] 
then
    echo "[WARN] No safe build. No offarray testing."
    exit 0
fi

MutRegress_Config_Directory='layered/MLU/krnl/Dart/server/src/cbfs/test'
MutRegress_Config_file='Test_List.JSON'
TIMEOUT=120
Worker_Threads=4
Iteration=1
EXTRACLI='-nodebugger -core'

cd safe/safe_util/adebuild.mod/
echo sudo PERL5LIB="${WORKSPACE}/safe/safe_util/adebuild.mod" ./mutRegress.pl -view ${WORKSPACE}/safe -configDir ${MutRegress_Config_Directory} -nocleanup -List ${MutRegress_Config_file} -timeout ${TIMEOUT} -worker ${Worker_Threads} -iteration ${Iteration} -extraCli "${EXTRACLI}"

sudo PERL5LIB="${WORKSPACE}/safe/safe_util/adebuild.mod" ./mutRegress.pl -view ${WORKSPACE}/safe -configDir ${MutRegress_Config_Directory} -nocleanup -List ${MutRegress_Config_file} -timeout ${TIMEOUT} -worker ${Worker_Threads} -iteration ${Iteration} -extraCli "${EXTRACLI}"

${WORKSPACE}/safe/safe_util/adebuild.mod/mutRegressReportParser.pl -l ${WORKSPACE}/safe/Targets/armada64_checked/simulation/exec -s ${WORKSPACE}/suite.log

echo "cd ${WORKSPACE} && sudo ${WORKSPACE}/safe/safe_util/adebuild.mod/cbfssim_errs.sh"
cd ${WORKSPACE} && sudo ${WORKSPACE}/safe/safe_util/adebuild.mod/cbfssim_errs.sh

echo "find ${WORKSPACE}/safe/Targets/armada64_checked/simulation/exec -name summary.txt -type f| xargs cat | tee ${WORKSPACE}/summary.log"
find ${WORKSPACE}/safe/Targets/armada64_checked/simulation/exec -name summary.txt -type f| xargs cat | tee ${WORKSPACE}/summary.log
# e.g. safe/Targets/armada64_checked/simulation/exec/Results_2017_0221_181925/pass1/job15_[CbfsSim_pfdc_io]/summary.txt
# e.g. safe/Targets/armada64_checked/simulation/exec/Results_2017_0221_181925/pass1/job50_[CbfsSim_stressTest_ILC_TLU]/summary.txt

echo "safe/safe_util/adebuild.mod/findInFile.pl -file ${WORKSPACE}/suite.log -match FAILED -fail -showMatches"
safe/safe_util/adebuild.mod/findInFile.pl -file ${WORKSPACE}/suite.log -match FAILED -fail -showMatches

ec=$?
if [ "$ec" -ne 0 ]
then
    export COLLECT_MATERIALS=1
fi

exit $ec

