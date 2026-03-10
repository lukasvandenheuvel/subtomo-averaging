---
layout: default
---

# Extraction for dynamo

1. Inside the ```warp/``` directory, copy the ```particles_warp.star``` from the previous step. 

2. Export the subtomograms with ```WarpTools```:
    ```shell
    WarpTools ts_export_particles \ 
    --settings warp_tiltseries.settings \
    --input_star particles_warp.star \
    --output_star relion3_b8_particles.star \
    --coords_angpix 1.98 \
    --output_angpix 15.84 \
    --box 64 \
    --diameter 1013 \
    --relative_output_paths \
    --3d \
    --output_processing bin_8_3d
    ```
    This will take a few minutes.

3. Run the python script ```convert_warp_to_tbl.py``` which does the following:
    - Adds tilt, psi priors to bin8_particles.star
    - Convert to tbl with warp2dynamo
    - Edits tbl file to include min and max tilt angle and helical tube ID.
    ```shell
    python3 convert_warp_to_tbl.py \
    -r /mnt/storage/data/users/lukas/20251127_MSA_liftout/Session2/Titan3_EPFL_LBEM_Lukas2_20251210/msa_human/20251127_lift_out/Position_91_3/warp \
    -i particles_warp.star relion3_b8_particles.star \
    -o relion3_b8_particles_merged.star \
    -t processing/tomostar/Position_91_3_ali.tomostar \
    -bs 64 -b 8
    ```

4. Do CTF correction of the extracted particles with ```correct_ctf_subtomo.py```:
    ```bash
    conda activate tomotools

    python3 correct_ctf_subtomo.py \
    -r /mnt/storage/data/users/lukas/20251127_MSA_liftout/Session2/Titan3_EPFL_LBEM_Lukas2_20251210/msa_human/20251127_lift_out/Position_91_3/warp \
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

