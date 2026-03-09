# Tomogram reconstruction

1. With tomotools
    ```
    conda activate tomotools
    tomotools reconstruct -b 4 -d 3000 --aretomo *.mrc```

2. With Warp
    ```shell
    mkdir warp
    cd warp
    conda activate tomotools
    tomotools aretomo2warp --v2 --frames-dir ../frames_tiff -n Position_91_3 ../ts-aligned ./
    ```
    Move all files and folders to ./warp, remove ././warp/Position_##:
    ```shell
    mv Position_91_3/* .
    rm -r Position_91_3
    ```

    Start warp reconstruction:
    ```shell
    WarpTools create_settings --folder_data frames --output warp_frameseries.settings --extension "*.mrc" --angpix 1.98 --exposure 3.83 --folder_processing processing   

    WarpTools fs_motion_and_ctf --settings warp_frameseries.settings --m_grid 1x1x1 --c_grid 2x2x1 --c_range_min 50 --c_range_max 10 --c_defocus_max 8 --out_averages --c_use_sum --out_average_halves

    WarpTools filter_quality --settings warp_frameseries.settings --histograms

    WarpTools ts_import --mdocs ./mdoc --frameseries ./processing --tilt_exposure 3.83 --output ./processing/tomostar

    WarpTools create_settings --folder_data processing/tomostar --output warp_tiltseries.settings --extension *.tomostar --angpix 1.98 --exposure 3.83 --folder_processing processing --tomo_dimensions 4096x4096x3000

    WarpTools ts_import_alignments --settings warp_tiltseries.settings --alignments ./imod --alignment_angpix 1.98

    WarpTools ts_defocus_hand --settings warp_tiltseries.settings --set_auto

    WarpTools ts_ctf --settings warp_tiltseries.settings --defocus_max 8 --range_high 4

    WarpTools filter_quality --settings warp_tiltseries.settings --histograms

    WarpTools ts_reconstruct --settings warp_tiltseries.settings --angpix 7.92 --dont_invert --deconv

    ```

# Picking, extracting and averaging -- Warp version

1. Pick in imod.
2. Convert imod to .coords file with Wen-Lu's instructions
3. Convert coords to star file with cryolo's coords2warp module
    ```
    cryolo_boxmanager_tools.py coords2star -i Position_91_3_ali.coords -o out_warp/ --scale 4 --apix 1.98 --mag 64000 --flipratio 0.5
    ```

    The path to the script is here in case you want to make your own version:
    /programs/x86_64-linux/cryolo/1.9.9_cu11/miniconda/lib/python3.8/site-packages/cryoloBM_tools/coords2warp.py

    Change Micrographname:

    ```bash
    sed -i 's/_ali_c/_ali/g' particles_warp.star
    ```

    Copy particle star file
    ```bash
    cd ../..
    cp processing/reconstruction/out_warp/particles_warp.star .
    ```

4. Star to tbl:

    ```bash
    # Warp export particles
    WarpTools ts_export_particles --settings warp_tiltseries.settings --input_star particles_warp.star --output_star relion3_b8_particles.star --coords_angpix 1.98 --output_angpix 15.84 --box 64 --diameter 1013 --relative_output_paths --3d --output_processing bin_8_3d

    # Run the script that
    # - Adds tilt, psi priors to bin8_particles.star
    # - Convert to tbl with warp2dynamo
    # - Edits tbl file to include min and max tilt angle and helical tube ID.
    python3 convert_warp_to_tbl.py \
    -r /mnt/storage/data/users/lukas/20251127_MSA_liftout/Session2/Titan3_EPFL_LBEM_Lukas2_20251210/msa_human/20251127_lift_out/Position_91_3/warp \
    -i particles_warp.star relion3_b8_particles.star \
    -o relion3_b8_particles_merged.star \
    -t processing/tomostar/Position_91_3_ali.tomostar \
    -bs 64 -b 8
    ```

5. Do CTF correction

    ```bash
    conda activate /mnt/storage/data/users/lukas/software/miniconda3/envs/tomotools

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

5. Dynamo: randomize azimuth angle and make a first average.
    ```matlab
    dynamo

    T = dread('particles_edit.tbl');
    T2 = dtrandomize_azimuth(T);
    dwrite(T2,'particles_edit_mod.tbl');
    oa=daverage('filamentsData_ctf','t','particles_edit_mod.tbl','mw',50);
    dwrite(oa.average,'raw_template_ctf.em');
    ```

    Check in ChimeraX, don't forget to flip the volume:
    ```chimerax vop scale #1 factor -1```

5. Copy the particles_edit_mod.tbl, giving it the same name as the tomogram:

    ```
    cp particles_edit_mod.tbl Position_91_3_8.00Apx.tbl
    ```

6. Back in Scipion, import the subtomos from tbl with a ```tomo - import coordinates 3D``` job.

7. Relion extraction:
    - Start a Relion extraction job (do not use the queue)
    - Stop it after a few seconds
    - Go to /extra and rename ```inParticles.star``` to ```inParticlesBackup.star```.
    - Convert the STAR file to helical coordinates with

    ```
    python convert_to_helical.py /mnt/storage/data3/scipion_data/projects/Lukas_MSA_Session2_Position_91_3/Runs/001062_ProtRelion5ExtractSubtomos/extra/inParticlesBackup.star /mnt/storage/data3/scipion_data/projects/Lukas_MSA_Session2_Position_91_3/Runs/001062_ProtRelion5ExtractSubtomos/extra/inParticles.star
    ```
    - Relaunch Relion extraction.





# Picking, extracting and averaging -- Scipion version

1. Pick in imod.
2. Convert imod to .coords file with Wen-Lu's instructions
3. Convert coords to star file with cryolo's coords2warp module
    ```
    cryolo_boxmanager_tools.py coords2star --i 000177_ProtWarpTomoReconstruct/extra/warp_tiltseries/reconstruction/deconv/Position_91_3_8p00Apx_filaments_PtsAdded_XYZI.coords --o 000177_ProtWarpTomoReconstruct/extra/warp_tiltseries/reconstruction/deconv/ --apix 1.98 --mag 68000 --flipratio 0.5 --scale 4
    ```

    The path to the script is here in case you want to make your own version:
    /programs/x86_64-linux/cryolo/1.9.9_cu11/miniconda/lib/python3.8/site-packages/cryoloBM_tools/coords2warp.py

    Change Micrographname:

    ```bash
    sed -i 's/Position_91_3_8p00Apx_filaments_PtsAdded_.tomostar/Position_91_3.tomostar/g' particles_warp.star
    ```

4. Star to tbl:

    ```bash
    # In Scipion project directory
    mkdir Conversions
    mkdir Conversions/001_WarpToTbl
    cd Conversions/001_WarpToTbl
    cp ../../Runs/000177_ProtWarpTomoReconstruct/extra/warp_tiltseries/reconstruction/deconv/particles_warp.star .
    cp ../../Runs/000177_ProtWarpTomoReconstruct/extra/tomostar/Position_91_3.tomostar .

    # Warp export particles
    WarpTools ts_export_particles --settings ../../Runs/000177_ProtWarpTomoReconstruct/extra/settings/Position_91_3_warp_tiltseries.settings --input_star particles_warp.star --output_star bin8_particles.star --coords_angpix 1.98 --output_angpix 15.84 --box 64 --diameter 1013 --relative_output_paths --3d --output_processing bin8_3d 

    # Run the script that
    # - Adds tilt, psi priors to bin8_particles.star
    # - Convert to tbl with warp2dynamo
    # - Edits tbl file to include min and max tilt angle and helical tube ID.
    python3 convert_warp_to_tbl.py \
    -r /mnt/storage/data3/scipion_data/projects/Lukas_MSA_Session2_Position_91_3/Conversions/001_WarpToTbl \
    -i particles_warp.star bin8_particles.star \
    -o bin8_particles_merged.star \
    -t Position_91_3.tomostar \
    -bs 64 -b 8
    ```

5. Do CTF correction

    ```bash
    conda activate /mnt/storage/data/users/lukas/software/miniconda3/envs/tomotools

    python3 correct_ctf_subtomo.py \
    -r /mnt/storage/data3/scipion_data/projects/Lukas_MSA_Session2_Position_91_3/Conversions/001_WarpToTbl \
    -s bin8_particles_merged.star \
    -t dynamo/particles_edit.tbl \
    -o dynamo/filamentsData_ctf/ \
    --bpf 0.002 0.5 \
    --ctf_method wiener \
    --wiener_epsilon 0.1 \
    --nproc 54 
    ```

5. Dynamo: randomize azimuth angle and make a first average.
    ```matlab
    dynamo

    T = dread('particles_edit.tbl');
    T2 = dtrandomize_azimuth(T);
    dwrite(T2,'particles_edit_mod.tbl');
    oa=daverage('filamentsData_ctf','t','particles_edit_mod.tbl','mw',50);
    dwrite(oa.average,'raw_template_ctf.em');
    ```

5. Copy the particles_edit_mod.tbl, giving it the same name as the tomogram:

    ```
    cp particles_edit_mod.tbl Position_91_3_8.00Apx.tbl
    ```

6. Back in Scipion, import the subtomos from tbl with a ```tomo - import coordinates 3D``` job.

7. Relion extraction:
    - Start a Relion extraction job (do not use the queue)
    - Stop it after a few seconds
    - Go to /extra and rename ```inParticles.star``` to ```inParticlesBackup.star```.
    - Convert the STAR file to helical coordinates with

    ```
    python convert_to_helical.py /mnt/storage/data3/scipion_data/projects/Lukas_MSA_Session2_Position_91_3/Runs/001062_ProtRelion5ExtractSubtomos/extra/inParticlesBackup.star /mnt/storage/data3/scipion_data/projects/Lukas_MSA_Session2_Position_91_3/Runs/001062_ProtRelion5ExtractSubtomos/extra/inParticles.star
    ```
    - Relaunch Relion extraction.



