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

5. Run the motion correction with tomotools

    ```bash
    conda activate tomotools
    # Set motioncor executable
    export MOTIONCOR_EXECUTABLE=$MOTIONCOR_EXECUTABLE
    # Motion / gain correction
    tomotools preprocess --mcbin 1 --frames ./frames_tiff/frames/ --gainref ./frames_tiff/gain-reference.mrc $TOMONAME.mrc ./ts-aligned/ 
    ```

6. Reconstruct the tomogram with tomotools

    ```bash
    tomotools reconstruct -d 3000 -b 4 --aretomo $TOMONAME.mrc
    ```

7. Export the tomotools alignment to warp
    ```bash
    cd $ROOT
    mkdir warp
    conda activate tomotools
    ```
    ```bash
    tomotools aretomo2warp --v2 --frames-dir frames_tiff -n $TOMONAME ts-aligned warp
    ```
8. With the shell script, reconstruct the tiltseries with warp
    ```bash
    cd $ROOT/warp/$TOMONAME
    $REPOSITORY/warp_reconstruction.sh $ANGPIX $FRAMEEXPOSURE $RECBINNING
    ```
9. Finally, move the warp output folders outside ```Position_XX```, to avoid confusion with the duplicate folder name.
    ```bash
    cd $ROOT/warp
    mv $TOMONAME/* .
    rm -r $TOMONAME
    ```
    And update all paths accordingly:
    ```bash
    cd $ROOT/warp/processing
    sed -i 's|'$TOMONAME'/warp/'$TOMONAME'/frames|'$TOMONAME'/warp/frames|g' ${TOMONAME}_ali_sec_*.xml
    ```


Finally, the folder structure should look something like this:

```bash
Position_XX_X
│   • Position_XX_X.mrc # Raw tilt series
│   • Position_XX_X.mrc.mdoc # Mdoc file
│
└───frames # Subfolder for EER frames
│       • Position_XX_X_001_-10.00_20251212_214747_EER.eer
│       • Position_XX_X_002_-7.00_20251212_214827_EER.eer
│       ...
│       
└───frames_tiff
│   │   • gain-reference.mrc
│   │
│   └───frames # Subfolder for .tif frames
│       │   • Position_XX_X_001_-10.00_20251212_214747_EER.tif
│       │   • Position_XX_X_002_-7.00_20251212_214827_EER.tif
│       │   ...
│   
└───ts-aligned # alignment and reconstruction by tomotools
│   │   • file021.txt
│   │   • file022.txt
│
└───warp # warp reconstruction
│   │   • file021.txt
│   │   • file022.txt
```

---

<p align="center">
  <a href="session-setup.html">← Back</a> | <a href="imod-picking.html">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>
