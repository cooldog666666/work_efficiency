#!/bin/bash

### INPUT
# IN_SAFE_TEST_RPM_PATH    # /CI-build/upc-nextunity-file-Stream-jobs/upc-nextunity-file-cs_Build-Suse-Debug/latest/safe/KHDATAPATH_DEBUG
# IN_TEST_SUITE    # CbfsSim_Fsck.exe
# IN_TEST_DURATION_HOURS    # 8
# IN_TEST_CASES_SKIPPED

### OUTPUT
# When fail, pack everything into testfail-*.tgz

err_count=0
thre_err_count=10
function trap_err()
{
  let err_count++
  echo "trap ERR ($err_count) times; exit at $thre_err_count"
  if [ "$err_count" -ge "$thre_err_count" ]
  then
    exit 1
  fi  
}
trap "trap_err" ERR

[ "${_debug}" != 0 ] && set -x

function Debug()
{
    [ "${_debug}" != 0 ] && $@
}

console_log="test.log"
dump_thread_log="allStacks.txt"
NO_CASE_ENDURE=${_NO_CASE_ENDURE:-10}


function disorder_array()
{
_tary=($1)
_length=${#_tary[@]}
_ele=''
_ary=()
while [ "$_length" -gt 1 ] 
do
#echo "length: $_length"
rdm=$((RANDOM % $_length))
_ele=${_tary[$rdm]}
_ary="${_ary[@]} ${_ele}"
_tary=(${_tary[@]/$_ele})
let _length--
#echo "ele: ${_ele}"                                                                                                                                  
#echo "ary: ${_ary[@]}"
#echo "tary: ${_tary[@]}"
done

_ary="${_ary[@]} ${_tary}"
echo ${_ary[@]}
}

function extract()
{
    Debug echo "Extract rpm ..."
    Debug echo "Now at $(pwd)"
    rpmfile=`ls $IN_SAFE_TEST_RPM_PATH/safe-test-*rpm`;  # /CI-build/upc-nextunity-file-Stream-jobs/upc-nextunity-file-cs_Build-Suse-Debug/latest/safe/KHDATAPATH_DEBUG/safe-test-upc_nextunity_file_cs.7910801.7910801-KHDATAPATH_DEBUG.0.x86_64.rpm
    rpm2cpio $rpmfile | cpio -id;
    Debug ls -l
}

function collect
{
    suite_path=$1
    c=$2

    echo "Collecting dmp and logs"
    suite=$(basename $suite_path)
    dmpfile=`ls *dmp`
    tarball=`echo testfail-$suite-$c.tgz | sed "s/:/-/g"`
    gdb -batch -ex "thread apply all bt" $suite_path $dmpfile >& $dump_thread_log
    pid=`grep 'waitpid.*libc' -B 1 $dump_thread_log | head -n 1 | awk '{print $2}'`
    grep 'waitpid.*libc' -B 1 -A 50 $dump_thread_log
    echo "file $suite_path" > gdbinit
    echo "core-file $dmpfile" >> gdbinit
    echo "thread $pid" >> gdbinit
    tar zcf $tarball *txt *log *dmp gdbinit etc/ opt/ --exclude $tarball
}

function runcase()
{
    Debug echo "runcase ..."
    libs=$1
    suite_path=$2
    c=$3
    suite=$(basename $suite_path)
    
    echo `date +%Y%m%d%H%M%S` "Running test case $suite $c"
    if [ -n "`echo $IN_TEST_CASES_SKIPPED | grep $c`" ]; then
        echo === Test case $suite $c skipped ===
        return
    fi
    sudo LD_LIBRARY_PATH=$libs $suite_path -run_tests $c -core -nodebugger >& $console_log || echo
    if [ -z "`ls *dmp 2>/dev/null`" ]
    then
        echo === Test case $suite $c success ===
        return
    fi
    echo === Test case $suite $c fail ===
    collect $suite_path $c
    exit 1
}

function runsuite()
{
    Debug echo "runsuite ..."
    endtime=$1
    NO_CASE_CAL=0
    Debug echo "now at $(pwd)"
    folders=`find -type d`
    Debug echo -e "***folders:\n$folders"
    libs=`echo $folders | sed "s/ /:/g"`
    Debug echo -e "***libs:\n$libs"
    suite_pathes=`find -name $IN_TEST_SUITE`
    Debug echo -e "***suite_pathes:\n$suite_pathes"
    suite_path_array=$(disorder_array "$suite_pathes")
    for suite_path in ${suite_path_array}
    do
        Debug echo "Run suite: $suite_path"
        cases=`sudo LD_LIBRARY_PATH=$libs $suite_path -list | grep "^([0-9]\+)" | awk '{print $5}' | sed "s/:$//"`
        Debug echo -e "cases:\n$cases"
        if [ -z "$cases" ]
        then
            echo "[ERROR] No cases found."
            sudo LD_LIBRARY_PATH=$libs $suite_path -list
            let NO_CASE_CAL++
            if [ "$NO_CASE_CAL" -ge "$NO_CASE_ENDURE" ]
            then
                exit 1
            fi 
            sleep 300;
        else
            for c in $cases
            do
                runcase $libs $suite_path $c
                now=`date +%s`
                if [ "$now" -gt "$endtime" ]
                then
                    echo Test suite $IN_TEST_SUITE success
                    exit 0
                fi
            done
        fi
    done
}

function run_cases_hours()
{
    Debug echo "run_cases_hours ..."
    now=`date +%s`
    endtime=$((now+(IN_TEST_DURATION_HOURS*3600)))
    while :;
    do
        runsuite $endtime
    done
}

function precheck()
{
    nowH=`date +%H -u`
    nowH=${nowH#0}
    endtimeH=$((nowH+IN_TEST_DURATION_HOURS))
    Debug echo "nowH: $nowH"
    Debug echo "endtimeH: $endtimeH (should less than ${WORKTIME_UTC})"
    if [ "$endtimeH" -ge "$WORKTIME_UTC" ] ;
    then
        echo "[ERROR] Should not start the test if test ends after 8 AM(UTC 24 PM)"
        exit 0
    fi
    
    
}

function main
{
    precheck
    extract
    run_cases_hours
}

main

