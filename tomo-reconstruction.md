---
layout: default
---

# Tilt-series alignment and tomogram reconstruction

## Tomogram alignment with tomotools
Although we will do the final reconstruction in Warp, we add this initial alignment + reconstruction steps using ```tomotools``` which allows for a quick reconstruction step to see the quality of the tilt-series alignment.

1. Generate a ```movies.star``` file that lists all frames:
    ```bash
    source params.sh
    cd $ROOT
    find frames/ > movies.star
    ```
    Open the ```movies.star``` file and paste the 3 first lines of the below cell on top, so that the final file looks like this:
    ```
    data_global 
    loop_ 
    _rlnMicrographMovieName 
    ./frames/Position_10_001_0.00_20241119_150207_EER.eer 
    ./frames/Position_10_002_3.00_20241119_150229_EER.eer 
    ./frames/Position_10_003_6.00_20241119_150252_EER.eer 
    ...
    ```
2. Copy your gain reference file into ```$ROOT/frames/```.

3. Use the Relion command below to sum EER frames into fractions for the motion correction. Adapt the ```--eer_grouping``` parameter to specify the number of frames that will end up in one fraction. Ideally, you want a total of ~5 fractions with a total dose of ~150 e/A2.
    ```bash
    relion_convert_to_tiff --i ./movie.star --o frames_tiff/ --compression none --gain ./frames/*gain --eer_grouping 92  
    ```
    Move all files that ended up outside of the subfolder into ```./frames_tiff```.

4. Modify the ```.mdoc``` file to update to ```.tif``` file extensions. You might first want to make a backup of the original mdoc:
    ```shell
    cp $TOMONAME.mrc.mdoc $TOMONAME.mrc.origin.mdoc
    sed -i 's/.eer/.tif/' $TOMONAME.mrc.mdoc
    ```


```bash
Position_XX_X
│   • Position_XX_X.mrc # Raw tilt series
│   • Position_XX_X.mrc.mdoc # Mdoc file
│
└───frames # Subfolder for individual frames
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

---

<p align="center">
  <a href="session-setup.html">← Back</a> | <a href="imod-picking.html">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>
