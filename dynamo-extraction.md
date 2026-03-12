---
layout: default
---

# Extraction for dynamo

1. Move inside the ```$ROOT/warp``` directory.
    ```shell
    source params.sh
    cd $ROOT/warp
    ```
    

2. Export the subtomograms with ```WarpTools```:
    ```shell
    # Compute angpix binned by 8 and box diameter (floor)
    ANGPIX_BINNED=$(echo "$ANGPIX * 8" | bc)
    BOXDIM=$(awk "BEGIN { print int($ANGPIX_BINNED * $BOXSIZE) }")
    # Export particles
    WarpTools ts_export_particles \ 
    --settings warp_tiltseries.settings \
    --input_star particles_warp.star \
    --output_star relion3_b8_particles.star \
    --coords_angpix $ANGPIX \
    --output_angpix $ANGPIX_BINNED \
    --box $BOXSIZE \
    --diameter $BOXDIM \
    --relative_output_paths \
    --3d \
    --output_processing bin_8_3d
    ```
    This will take a few minutes.

3. Run the python script ```convert_warp_to_tbl.py``` which does the following:
    - Creates a ```dynamo``` subfolder
    - Adds tilt, psi priors to bin8_particles.star
    - Convert to tbl with warp2dynamo
    - Edits tbl file to include min and max tilt angle and helical tube ID.
    ```shell
    python3 convert_warp_to_tbl.py \
    -r $ROOT/warp \
    -i particles_warp.star relion3_b8_particles.star \
    -o relion3_b8/particles_merged.star \
    -t processing/tomostar/$TOMONAME'_ali.tomostar' \
    -bs $BOXSIZE -b 8
    ```

4. Do CTF correction of the extracted particles with ```correct_ctf_subtomo.py```:
    ```bash
    conda activate tomotools

    python3 correct_ctf_subtomo.py \
    -r $ROOT/warp \
    -s relion3_b8_particles_merged.star \
    -t dynamo/particles_edit.tbl \
    -o dynamo/filamentsData_ctf/ \
    --bpf 0.002 0.5 \
    --ctf_method wiener \
    --wiener_epsilon 0.1 \
    --nproc 54 
    ```
    This will take a few minutes with 54 processes.
    

End of particle extraction!

---

<p align="center">
  <a href="imod-picking.html">← Back</a> | <a href="dynamo-average.html">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>

