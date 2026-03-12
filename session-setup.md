---
layout: default
---

# Session setup

## Make individual folders for tomograms

After aquiring a set of tilt series on a Titan Krios with the Tomo software, all tilts are usually saved individually into one master folder:
```
.
│   20251210_120836_EER_GainReference.gain
│   Position_1_001_10.00_20251210_163641_EER.eer
│   Position_1_002_13.00_20251210_163753_EER.eer
│   ...
│   Position_XXX_X_039_-67.00_20251213_012516_EER.eer
```
First, we found it useful to generate seperate folders for each position, and move all EER files of that position to a subfolder called ```frames```.

  ```bash
  #! /bin/bash
  
  mkdir Position_$1
  mkdir Position_$1/frames
  
  # Move mdoc & mrc
  mv Position_$1.m* Position_$1/
  # Move frames
  mv Position_$1_0* Position_$1/frames
  ```
  For each position you want to analyse, e.g. ```Position_2_3```, run this bash script:
  ```shell
  bash move_eer_frames.sh 2_3
  ```

  ## Data organisation
After executing the above bash script, the folder for each individual tomogram is as follows:

```bash
Position_XX_X
│   Position_XX_X.mrc       # raw tilt series
│   Position_XX_X.mrc.mdoc  # mdoc file
│
└───frames # subfolder for individual frames
│       Position_XX_X_001_-10.00_20251212_214747_EER.eer
│       Position_XX_X_002_-7.00_20251212_214827_EER.eer
│       ...

```
We assume this data organisation throughout the rest of the tutorial.

**All subsequent steps will show the processing of only a single position.**

  ## Session setup with shell variables

To run all upcoming command-line steps smoothly, it is useful to setup a parameters file that contains some specifications of where your data is stored. Fill these parameters by editing the file ```params.sh```:

```bash
#!/bin/bash  
TOMONAME=Position_2_3
ROOT=/path/to/your/tomogram/folder/Position_2_3
REPOSITORY=/path/to/repository/subtomo-averaging
ANGPIX=1.98
BOXSIZE=64

echo "TOMONAME: $TOMONAME"
echo "ROOT: $ROOT"
echo "REPOSITORY: $REPOSITORY"
echo "ANGPIX: $ANGPIX"
echo "BOXSIZE: $BOXSIZE"
```

Then store these parameters as shell variables by sourcing this file:

```
source params.sh
```
Note: you will have to repeat that command every time you open a new terminal and continue with the analysis!





<p align="center">
  <a href="installation.html">← Back</a> | <a href="tomo-reconstruction.html">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>