---
layout: default
---

# Relion: Refine your volume

1. From the .tbl files of the 2 half-steps in the previous step, generate a .star file:
    ```shell
    python convert_tbl_to_warp.py \
    -r $ROOT/warp \ 
    -t1 dynamo/dynamo_project_b4/abp_align_eo/results/ite_0004/averages/refined_table_ref_001_ite_0004.tbl \
    -t2 dynamo/dynamo_project_b4/abp_align_eo/results/ite_0004/averages/refined_table_ref_002_ite_0004.tbl \ 
    -w particles_dynamo_b4.star \
    -o particles_dynamo_b2.star \
    -a $ANGPIX \
    -b 4 # binning of the .tbl files (was bin4)
    ```

2. Use this star file to re-extract particles with warp:

    ```shell
    # Compute angpix binned by 2 and box diameter (floor)
    ANGPIX_BIN2=$(echo "$ANGPIX * 2" | bc)
    BOXDIM=$(awk "BEGIN { print int($ANGPIX_BIN2 * $BOXSIZE) }")
    # Export particles
    cd $ROOT/warp
    WarpTools ts_export_particles \
    --settings warp_tiltseries.settings \
    --input_star particles_dynamo_b2.star \
    --output_star relion5_b2/Extract/bin2_box$BOXSIZE/particles.star \
    --coords_angpix $ANGPIX \
    --output_angpix $ANGPIX_BIN2 \
    --box $BOXSIZE \
    --diameter $BOXDIM \
    --relative_output_paths \
    --2d \
    --output_processing relion5_b2/Extract/bin2_box$BOXSIZE/
    ```

3. To do helical processing, Relion5 expects a ```_rnlAngleTilt``` of 90. The script ```warp_to_relion5.py``` rotates the Euler angle of the subtomograms such that ```_rnlAngleTilt``` is 90. Also, it converts the coordinates to be compatible with Relion5 (in Angstroms and measured from the center of the tomogram).
    ```shell
    cd $REPOSITORY
    python warp_to_relion5.py \
    --relionroot $ROOT/warp/relion5_b2 \
    --warp ../particles_dynamo_b2.star \
    --relion Extract/bin2_box$BOXSIZE/particles.star \
    --tomo Extract/bin2_box$BOXSIZE/particles_tomograms.star \
    --out Extract/bin2_box$BOXSIZE/particles_rot90.star
    ```

4. Rescale one of the two halfmaps from dynamo bin4 to bin2.
First, convert one of the halfmaps to an mrc file:
    ```shell
    cd $ROOT/warp
    ANGPIX_BIN4=$(echo "$ANGPIX * 4" | bc)
    ANGPIX_BIN2=$(echo "$ANGPIX * 2" | bc)
    e2proc3d.py --mult=-1 dynamo/dynamo_project_b4/abp_align_eo/results/ite_0004/averages/average_ref_001_ite_0004.em dynamo_bin4_ite4.mrc
    relion_image_handler --i dynamo_bin4_ite4.mrc --o dynamo_bin4_ite4.mrc --force_header_angpix $ANGPIX_BIN4
    relion_helix_toolbox --i dynamo_bin4_ite4.mrc --twist_min 1 --twist_max 1.9 --rise_min 4.6 --rise_max 4.8 --z_percentage 0.3 --search --cyl_outer_diameter 200 --angpix $ANGPIX_BIN4
    ```
    Rescale to the new boxsize and pixel size:
    ```shell
    # Rescale to the new box- and pixel size
    relion_image_handler --i dynamo_bin4_ite4_sym.mrc --o relion5_b2/dynamo_bin2_ite4_sym.mrc --angpix $ANGPIX_BIN4 --rescale_angpix $ANGPIX_BIN2 --new_box $BOXSIZE --force_header_angpix $ANGPIX_BIN2
    ```
    Below, set the twist and rise to the optima found above:
    ```shell
    # Apply symmetry
    relion_helix_toolbox --i dynamo_bin4_ite4.mrc --twist 1.09 --rise 4.8 --z_percentage 0.3 --impose --cyl_outer_diameter 160 --angpix $ANGPIX_BIN4 --o dynamo_bin4_sym.mrc
    # Rescale to the new pixel size
    relion_image_handler --i dynamo_bin4_ite4_sym.mrc --o relion5_b2/dynamo_bin2_ite4_sym.mrc --angpix $ANGPIX_BIN4 --rescale_angpix $ANGPIX_BIN2 --new_box $BOXSIZE --force_header_angpix $ANGPIX_BIN2
    ```

<p align="center">
  <a href="dynamo-bin4.html">← Back</a> | <a href=".">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>