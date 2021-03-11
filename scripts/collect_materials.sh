#!/bin/bash

set -e
_user=$(id $USER -u)
_group=$(id $USER -g)

remain_results_num=3
save_num=3
save_folder="${WORKSPACE}/../Offarray_Results"
MutRegress_exe_Directory='safe/Targets/armada64_checked/simulation/exec'

function die() {
    printf 'ERROR: %s\n' "$@" >&2
    exit 255
}

##############################################################
# Main
##############################################################
echo -e "#####################\n# Collect Materials #\n#####################"
if [ "${COLLECT_MATERIALS:-0}" -ne 1 ]
then
    echo "[INFO] No failure."
    exit 0
fi

if [ ! -e "${save_folder}" ]
then
    sudo mkdir ${save_folder}
    sudo chown ${_user}:${_group} ${save_folder}
fi 

today_results="${save_folder}/Results_$(date +%F_%H-%M-%S)"
mkdir ${today_results}

# Remove overdues
echo "[INFO] Remove overdues"
for item in $(ls -rt ${save_folder} | head -n -${remain_results_num})
do
    echo "[INFO] Remove ${save_folder}/${item}"
    rm -rf ${save_folder}/${item}
done

# collect materials
echo "[INFO] Collect materials"
count=0
cd ${WORKSPACE}
set +e
safe/safe_util/adebuild.mod/findInFile.pl -file ${WORKSPACE}/suite.log -match FAILED -fail -showMatches > offarray_fail_cases.list
set -e

while read line
do
    if [ "$count" == "$save_num" ]
    then
        echo "[INFO] Only save $save_num failure materials for space concern"
        break
    fi
    # pass1_job50_[CbfsSim_stressTest_PFDC_TLU] 1 0 1 843.248 FAILED pass1_job50_[CbfsSim_stressTest_PFDC_TLU].exe j50p1
    passN=${line%%_*}
    jobN=${line#*_}
    jobN=${jobN%%_*}
    # safe/Targets/armada64_checked/simulation/exec/Results_2017_0221_181925/pass1/job15_[CbfsSim_pfdc_io]/
    target_path=$(ls -d ${MutRegress_exe_Directory}/Results_*/${passN}/${jobN}_*)
    summary_file=$(ls $target_path/summary.txt)
    # skep AbortOnTimeout
    if grep 'Mut_thread_test_runner::AbortOnTimeout' ${summary_file}
    then
        echo "[INFO] Job ${jobN} AbortOnTimeout. Skip"
        continue
    fi
    target_path_basename=$(basename ${target_path})
    echo "[INFO] Collect ${target_path_basename}"
    mv ${target_path} ${today_results}
    let count++
done < offarray_fail_cases.list
echo '[INFO] Finish.'

exit 255

