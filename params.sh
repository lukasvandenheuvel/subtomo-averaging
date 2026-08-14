#!/bin/bash  

### PARAMETERS ###

TOMONAME=Position_60_3
ROOT=/mnt/storage/data/users/lukas/20251127_MSA_liftout/Session1/msa_human/20251127_lift_out/$TOMONAME
#ROOT=/mnt/storage/data/users/lukas/20251127_MSA_liftout/Session2/Titan3_EPFL_LBEM_Lukas2_20251210/msa_human/20251127_lift_out/$TOMONAME
REPOSITORY=/mnt/storage/data/users/lukas/subtomo-averaging
ANGPIX=1.98             # pixel size in Angs. Make sure it is a float, e.g. 2.00 (not 2)
MAGNIFICATION=64000     # nominal magnification
FRAMEEXPOSURE=3.4       # exposure per frame in e/A2
RECBINNING=4            # binning factor for reconstruction (choose something nice for picking particles)
BOXSIZE=64              # box size for inital subtomogram extraction (in pixels)
TOMOSIZEX=4096          # pixels
TOMOSIZEY=4096          # pixels
TOMOSIZEZ=3000          # pixels
MOTIONCOR_EXECUTABLE=/programs/x86_64-linux/system/sbgrid_bin/MotionCor2_1.6.4_Cuda112_Mar31cd w    2023

### END PARAMETERS ###

ANGPIX_BIN2=$(echo "$ANGPIX * 2" | bc)
ANGPIX_BIN4=$(echo "$ANGPIX * 4" | bc)
ANGPIX_REC=$(echo "$ANGPIX * $RECBINNING" | bc)

echo "TOMONAME: $TOMONAME"
echo "ROOT: $ROOT"
echo "REPOSITORY: $REPOSITORY"
echo "ANGPIX: $ANGPIX"
echo "MAGNIFICATION: $MAGNIFICATION"
echo "FRAMEEXPOSURE: $FRAMEEXPOSURE"
echo "RECBINNING: $RECBINNING"
echo "BOXSIZE: $BOXSIZE"
echo "TOMOSIZEX: $TOMOSIZEX"
echo "TOMOSIZEY: $TOMOSIZEY"
echo "TOMOSIZEZ: $TOMOSIZEZ"
echo "MOTIONCOR_EXECUTABLE: $MOTIONCOR_EXECUTABLE"
echo "ANGPIX_BIN2: $ANGPIX_BIN2"
echo "ANGPIX_BIN4: $ANGPIX_BIN4"
echo "ANGPIX_REC: $ANGPIX_REC"
