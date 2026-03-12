# Session setup
## Data organisation
In the current tutorial, we have setup our tomography data as follows:

```
Position_XX_X
│   • Position_XX_X.mrc
│   • Position_XX_X.mrc.mdoc
│
└───frames
│       • Position_XX_X_001_-10.00_20251212_214747_EER.eer
│       • Position_XX_X_002_-7.00_20251212_214827_EER.eer
│       ...
│       
└───frames_tiff
│   │   • gain-reference.mrc
│   │
│   └───frames
│       │   • Position_XX_X_001_-10.00_20251212_214747_EER.tif
│       │   • Position_XX_X_002_-7.00_20251212_214827_EER.tif
│       │   ...
│   
└───ts-aligned
│   │   • file021.txt
│   │   • file022.txt
│
└───warp
│   │   • file021.txt
│   │   • file022.txt
```


## Session setup with shell variables

To run all command-line steps smoothly, it is useful to setup a parameters file that contains some specifications of where your data is stored. Fill these parameters by editing the file ```params.sh```:

```bash
#!/bin/bash  
TOMONAME=Position_91_3
ROOT=/path/to/your/tomogram/folder/Position_XX_X
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
Note: you will have to repeat that command every time you open a new terminal!

<p align="center">
  <a href="installation.html">← Back</a> | <a href="imod-picking.html">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>