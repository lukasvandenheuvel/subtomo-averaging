---
layout: default
---

# Tilt-series preparation, alignment and tomogram reconstruction
Our initial steps for tilt-series motioncorrection, alignment and reconstruction are based on the [tomotools](https://github.com/tomotools/tomotools) package.

## Motion Correction

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

## Tilt-series alignment and initial tomogram reconstruction

{:start="6"}
6. The tomotools reconstruct command will run a tilt-series alignment with AreTomo and a tomogram reconstruction in IMOD:

    ```bash
    tomotools reconstruct -d 3000 -b 4 --aretomo ./ts-aligned/$TOMONAME.mrc
    ```

    The resulting alignment and reconstruction can be used to check the quality of this tomogram.

## WarpTools tomogram reconstruction
Tomograms that we selected for STA now need to be reconstructed a second time, using the previous AreTomo tilt-series alignment, and including a patch CTF estimation. For this, we use the [WarpTools](https://warpem.github.io/warp/user_guide/warptools/installation/) software.

{:start="7"}
7. Export the tomotools alignment to warp
    ```bash
    cd $ROOT
    mkdir warp
    conda activate tomotools
    ```
    ```bash
    tomotools aretomo2warp --v2 --frames-dir ./frames_tiff ./ts-aligned ./
    ```
8. With the shell script, reconstruct the tiltseries with warp
    ```bash
    cd $ROOT/warp
    $REPOSITORY/warp_reconstruction.sh $ANGPIX $FRAMEEXPOSURE $RECBINNING
    ```

Finally, the folder structure should look something like this:

```bash

Tomograms
└───Position_XX_X
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
    │   └───frames # Subfolder for summed .tif frames
    │           • Position_XX_X_001_-10.00_20251212_214747_EER.tif
    │           • Position_XX_X_002_-7.00_20251212_214827_EER.tif
    │           ...
    │   
    └───ts-aligned # alignment and reconstruction by tomotools (AreTomo and IMOD)
    │   │   • Position_XX_X_ali_filtered_rec_bin_X.mrc # IMOD reconstruction 
    │   │   • Position_XX_X_ali.mrc # tilt series aligned with AreTomo
    │   │   ... # additional AreTomo alignment files, including even and odd tilt series
    │   │
    │   └───Position_XX_X_ali_Imod # Subfolder with Imod reconstruction files
    │         
    │
    └───warp # warp reconstruction
    │   │   • warp_frameseries.settings 
    │   │   • warp_tiltseries.settings    
    │   │
    │   └───frames  # raw frames
    │   └───imod    # imod alignment files 
    │   └───mdoc    
    │   └───processing   
    │       └───reconstruction
    │           │   • Position_XX_ali_X.XXApx.mrc # warp reconstruction (for picking)
    │           │   
    │           └───deconv
    │               │   • Position_XX_ali_X.XXApx.mrc # warp high-contrast reconstruction
    │
```

# Improve tilt-series alignment with MissAlign

We have found the recently developed [MissAlign](https://github.com/warpem/miss-alignment/tree/main) software to drastically improve the quality of tilt-series alignments. Here, we show how to use MissAlign to improve the AreTomo alignment made with the previous steps. MissAlign is a neural network which can be trained on multiple tilt-series.

{:start="9"}
9. Inside the ```Tomograms``` folder, generate a folder called ```miss-alignment``` and ```cd``` into it.

10. Copy the ```update_warp_xml.py``` and ```config_template.yaml``` from MissAlign into this folder and update their content according to your specifications, as detailed in the [MissAlign docs](https://github.com/warpem/miss-alignment/blob/main/docs/usage.md).

11. For each tilt-series that you want to use for MissAlign training, copy its ```_ali.xml``` file (generated by warp) into the ```miss-alignment``` folder:
    ```bash
    cp ../Position_XX_X/warp/processing/Position_XX_X_ali.xml .
    ```

12. Configure miss-alignment
    ```bash
    conda activate miss-alignment
    python update_warp_xml.py
    ```

13. Run miss-alignment training
    ```bash
    miss-alignment train --config-file config_template.yaml --training-devices 0,1 --reconstruction-devices 2,2,2,2,2,3,3,3,3,3 --dataloaders-per-trainer 5 --start-at-iteration 0 --prepare-stacks $ANGPIX_REC
    ```

    This will take several hours, depending on your GPU configuration.

14. Copy the ```_ali.xml``` files (which now contain the refined alignments) back into the warp processing folders:
    ```bash
    cp Position_XX_X_ali.xml ../Position_XX_X/warp/processing
    ```
    
15. Reconstruct the tomogram again with WarpTools, now without first importing the alignments or doing CTF correction:
    ```bash
    WarpTools ts_defocus_hand --settings warp_tiltseries.settings --set_auto
    WarpTools ts_ctf --settings warp_tiltseries.settings --defocus_max 8 --range_high 4
    WarpTools ts_reconstruct --settings warp_tiltseries.settings --angpix $ANGPIX_REC --dont_invert --deconv
    ```

---

<p align="center">
  <a href="session-setup.html">← Back</a> | <a href="imod-picking.html">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>
