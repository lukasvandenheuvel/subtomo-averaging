#!/bin/bash  
TOMONAME=Position_91_3
ROOT=/mnt/storage/data/users/lukas/20251127_MSA_liftout/Session2/Titan3_EPFL_LBEM_Lukas2_20251210/msa_human/20251127_lift_out/Position_91_3
REPOSITORY=/mnt/storage/data/users/lukas/subtomo-averaging
ANGPIX=1.98 # make sure it is a float, e.g. 2.00 (not 2)
MAGNIFICATION=64000
RECBINNING=4
BOXSIZE=64
TOMOSIZEX=4096
TOMOSIZEY=4096
TOMOSIZEZ=3000

echo "TOMONAME: $TOMONAME"
echo "ROOT: $ROOT"
echo "REPOSITORY: $REPOSITORY"
echo "ANGPIX: $ANGPIX"
echo "MAGNIFICATION: $MAGNIFICATION"
echo "RECBINNING: $RECBINNING"
echo "BOXSIZE: $BOXSIZE"
echo "TOMOSIZEX: $TOMOSIZEX"
echo "TOMOSIZEY: $TOMOSIZEY"
echo "TOMOSIZEZ: $TOMOSIZEZ"