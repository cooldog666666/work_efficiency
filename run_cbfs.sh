#!/bin/bash
if [[ $1 == "" ]]
     then
     echo "usage: run_cbfs.sh <times> <suite name> <case id>"
     echo "example: run_cbfs.sh 10 CbfsSim_ildIO.exe 2390"
     exit
     fi
     
     for i in `seq 1 $1`
     do
         /net/sles15-chenq9-dev-00/c4_working/chenq9/filedomain/bin/simrun $2 $3 &> r.log;
         grep TestFinished r.log
     done

