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
    printf '[ERROR] %s\n' "$@" >&2 
    exit 255 
}

function catch_error() {
    die "An unhandled error occurred at $BASH_SOURCE:$BASH_LINENO"
}
# trap catch_error ERR

function debug_run()
{
    timeout=$1
    shift
    echo "[RUN] $@"
    "$@" & pid=$!
    tmpfile=/tmp/debug_run.${pid}.${RANDOM}-${RANDOM}
    echo ${pid} > ${tmpfile}
    ( sleep ${timeout} ; if [[ -e $tmpfile ]]; then kill -kill $pid; echo "[WARN] PID($pid) Timeout."; fi ; ) & 
    killerpid=$!
    wait $pid
    ec=$?
    disown $killerpid
    kill $killerpid >/dev/null 2>&1
    rm $tmpfile
    [[ $ec == 0 ]] || echo "[WARN] $@ exit with $ec"
    return ${ec:-0}
}

function get_property() {
    var=$1
    echo "[VAR] $var: ${!var}"
}

function git_authorization()
{
    # use same service account for both github and artifactory credentials
    github_hostname=$1
    github_user=$2
    github_password=$3
    artifactory_user=$2
    artifactory_password=$3

    # Cache credentials for a period long enough  (5 days) to perform the import, build and all tests
    git config credential.helper 'cache --timeout 432000' || die "Failed to set credential helper"

    # Set github credentials
    # TODO: test if Jenkins job already stores github credentials
    git credential approve < <(echo -e "protocol=https\nhost=${github_hostname}\nusername=${github_user}\npassword=${github_password}\n") || die "Failed to set credentials for $github_url"    

    # Get the Git LFS url, parse it and set credentials for it
    # TODO: could there be more than one LFS repo?
    declare git_lfs_url=$(git config --file .lfsconfig --get lfs.url)
    [[ $git_lfs_url ]] || die "Failed to obtain Git LFS configuration"
    
    [[ $git_lfs_url =~ ([^:]*)://([^/]*)/(.*) ]] || die "Failed to parse URL $git_lfs_url"

    git credential approve < <(echo -e "protocol=${BASH_REMATCH[1]}\nhost=${BASH_REMATCH[2]}\nusername=${artifactory_user}\npassword=${artifactory_password}\n") || die "Failed to set credentials for $url"
}

function populate_code()
{
    debug_run 600 git pull
    try_time=0
    total_try=2
    while ! debug_run 3000 git lfs pull
    do
        let try_time++
        if [ "$try_time" -ge "$total_try" ]
        then
            die "Could not populate code."
        fi
        echo "[INFO] Retry git lfs pull $((total_try - try_time)) more time(s)."
    done
}

function find_case_id()
{
    exe=$1
    case_body=$2
    exe_list=$(sudo LD_LIBRARY_PATH=$ldpath:$LD_LIBRARY_PATH ${exe} -list | grep " ${case_body}: ")
    # (1058) [timeout: 600 sec.] CbfsioApiDataTest_ForceUnmountTest:TLU_ILC_VBM_8k: ForceUnmountTest
    echo ${exe_list} | sed -n 's/\s*(\([0-9]\+\)).*/\1/p'
}

function collect_data()
{
    _case=$1
    mkdir "${_case}"
    sudo mv cbfs.log run.log CbfsSim*.dmp "${_case}"
}

function check_nightly_case()
{
    exe=$1
    case_id=$2
    # (1376) [timeout: 240 sec.] WriteReplayTestNoMFD:DLU_noVBM_PFDCEnable_16k:    Test marked NIGHTLY - SKIP
    if sudo LD_LIBRARY_PATH=$ldpath:$LD_LIBRARY_PATH ${exe} -list | egrep "\($case_id\)\s*\[timeout:" | grep -q "Test marked NIGHTLY"
    then
        echo "-nightly"
    fi
}

function repeat()
{
    _iteration=${1:-10}
    _case=${2}
    # CbfsSim_ilcIO.CbfsioApiDataTest_ForceUnmountTest:TLU_ILC_VBM_8k
    [[ -n ${_case} ]] || die "No case specified to run."
    case_exe=${_case%.*}
    case_body=${_case#*.}
    case_name=${case_body%:*}
    case_cls=${case_body#*:}
    
    for var in case_exe case_body case_name case_cls
    do
        get_property $var
    done
    
    # following are what simrun does
    proot=$(git rev-parse --show-toplevel)
    safesim=$proot/safe/Targets/armada64_checked/simulation/exec
    safeuser=$proot/safe/Targets/armada64_checked/user/exec
    sade=$proot/sade/obj/KHDATAPATH_DEBUG_64/dart/Dart/server/src/kernel/min_kernel/sade_csx
    bm=$proot/sade/obj/KHDATAPATH_DEBUG_64/dart/Dart/server/src/kernel/buffer_mgr/bm_csx
    linux=$proot/sade/obj/KHDATAPATH_DEBUG_64/dart/Dart/server/src/sade/sade_core_linux/core/
    sm=$proot/sade/obj/KHDATAPATH_DEBUG_64/rpm_install/EMC/Platform/lib64/
    stat=$proot/safe/obj/KHDATAPATH_DEBUG_64/rpm_install/opt/observability-producer/lib64/
    uutf=$proot/safe/obj/KHDATAPATH_DEBUG_64/rpm_install/opt/c4-uutf-common/lib64/
    ApiHelper=$proot/sade/obj/KHDATAPATH_DEBUG_64/rpm_install/opt/safe/lib64/admin/
    ldpath=$safesim:$safeuser:$sade:$bm:$linux:$sm:$stat:$uutf:$ApiHelper
    LD_LIBRARY_PATH=$ldpath:$LD_LIBRARY_PATH
    ln -sf $proot/safe/catmerge/layered/MLU/test/MUT/ufs64/ufs64sim/ufs64sim.sade.cfg  $proot/
    
    exe=${safesim}/${case_exe}.exe
    case_id=$(find_case_id ${exe} ${case_body})
    nightly_case=$(check_nightly_case ${exe} ${case_id})
    runlog='run.log'
    
    cd ${proot}
    _n=0
    while [ "$_n" -lt "$_iteration" ]
    do
        let _n++
        sudo rm -f cbfs.log $runlog > /dev/null 2>&1
        cmd="${exe} -run_tests ${case_id} -core -nodebugger ${nightly_case}"
        echo "[RUN:$_n] ${cmd}"
        sudo LD_LIBRARY_PATH=$ldpath:$LD_LIBRARY_PATH ${exe} -run_tests ${case_id} -core -nodebugger ${nightly_case} | tee $runlog
        if grep -q 'Failed: 0 Passed: 1' $runlog
        then
            continue
        else
            echo "[RESULT] \"${cmd}\" failed at ($_n) (total: ${_iteration})"
            collect_data ${_case}
            return 1
        fi
    done
    if [ "$_n" -eq "$_iteration" ]
    then
        echo "[INFO][ALL_PASS] ${_case} $_n iteration"
    fi
    return 0
}

##############################################################
# Main
##############################################################
echo "[INFO] Getting parameters for MergePush Jenkins (github plugin) build"
[[ -n ${GIT_URL} ]] || die "GIT_URL env variable not set by Jenkins job"
[[ -n ${GIT_BRANCH} ]] || die "GIT_BRANCH env variable not set by Jenkins job"
[[ -n ${BUILD_BRANCH} ]] || die "BUILD_BRANCH env variable not set by Jenkins job"
github_url=$(git config --get remote.origin.url)
github_url=${github_url#git@}
github_url=${github_url#http*://}
github_url=${github_url%:*}
declare ci_github_hostname=${github_url%%/*}
declare ci_git_target_branch=${GIT_BRANCH/#origin\//}
declare ci_build_branch=${BUILD_BRANCH:-${ci_git_target_branch}}

for prop in GIT_URL GIT_BRANCH ci_github_hostname BUILD_BRANCH ci_build_branch ci_git_target_branch
do
    get_property $prop
done

git checkout $ci_build_branch || die "Fail to checkout branch: $ci_build_branch"
head_commit_id=$(git rev-parse HEAD)
echo "[INFO] HEAD: ${head_commit_id} @BRANCH: ${ci_build_branch}"
git log --graph --pretty=format:'%h -%d%s (%cr) <%an>' --abbrev-commit -10
git_authorization $ci_github_hostname ${USERNAME} ${!USERNAME}
populate_code

build_all --noincremental safe || die "Fail to build_all safe"

echo "[INFO] Build_all safe complete."

if [ -f safe/safe_util/adebuild.mod/cbfssim_onlyNightly.sh ]
then
    cmd='bash safe/safe_util/adebuild.mod/cbfssim_onlyNightly.sh'
    echo "[INFO] $cmd"
    eval $cmd
    exit $?
else
    echo "[ERROR] Not found safe/safe_util/adebuild.mod/cbfssim_onlyNightly.sh"
    exit 255
fi

