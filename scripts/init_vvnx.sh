#!/bin/bash

for i in AUTOX_USER AUTOX_TESTBED AUTOX_TESTSET UTMS_PROJECT UTMS_TESTSET_CYCLE_ID UTMS_TEAM_NAME TIME_OUT IMAGE_PATH
do
  if [ -z "${!i}" ]
  then
    echo "[ERROR] $i not set"
    exit 1
  fi
  echo "$i: ${!i}"
done

./sw-dev-tools/ci-test/linux/run_automatos_tests \
  --username $AUTOX_USER\
  --testbed "$AUTOX_TESTBED"\
  --testset "$AUTOX_TESTSET"\
  --utms "$UTMS_PROJECT;$UTMS_TESTSET_CYCLE_ID;$UTMS_TEAM_NAME"\
  --time_out "$TIME_OUT"
