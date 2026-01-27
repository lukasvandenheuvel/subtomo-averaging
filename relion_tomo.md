1. Reconstruct tomograms at bin2, using only a single MPI node (otherwise it won't fit in memory) 

2. Generate real-space subtomos and write out projections along the tilt axes:  
```mpirun -n 5 `which relion_tomo_subtomo_mpi` --p Picks/job012/particles.star --t Tomograms/job011/tomograms_bin1.star --theme classic --o Extract/job029/ --b 512 --div --nrm --float16 --real_subtomo --bin 1 --min_frames 1 --j 10 --pipeline_control Extract/job029/```

3. Save the lowest tilt angle projections as mrcs files and give them the correct tilt angles and priors:   
```python extract_2d_for_classification.py --i Extract/job032/particles_for_class2d.star --o Class2D_prep/job036/ --bg_radius 5 --normalize```

4. Do 2D classification with the resulting star file

5. Select 2D classes

6. Create a coordinates file with only picked particles:  
    ```python filter_particles_by_selection.py Select/job044/particles.star Picks/job012/particles.star -o Select/job044/tomo_particles.star -v```

7. Make an optimization set file:
    ```
    # Created by the starfile Python package (version 0.5.8) at 13:12:16 on 26/01/2026


    data_optimisation_set

    loop_
    _rlnTomoParticlesFile #1
    _rlnTomoTomogramsFile #2
    Select/job044/tomo_particles.star Tomograms/job011/tomograms.star
    ```

8. Run 3D classification


 Imod 2D pipeline

 1. ```python select_tif_from_star.py /mnt/storage/data/users/lukas/20251127_MSA_liftout/Session1/msa_human/RelionProcessing/Block1-ROI7-Nuclear/ExcludeTiltImages/job004/tilt_series/Position_24.star /mnt/storage/data/users/lukas/20251127_MSA_liftout/Session1/msa_human/20251127_lift_out/Position_24/frames_tiff/frames -o /mnt/storage/data/users/lukas/20251127_MSA_liftout/Session1/msa_human/20251127_lift_out/Position_24/frames_tiff_selected/frames -m /mnt/storage/data/users/lukas/20251127_MSA_liftout/Session1/msa_human/20251127_lift_out/Position_24/Position_24.mrc.origin.mdoc --mdoc-output /mnt/storage/data/users/lukas/20251127_MSA_liftout/Session1/msa_human/20251127_lift_out/Position_24/Position_24.mrc.selected.mdoc -v```

    Rename ```Position_24.mrc.selected.mdoc``` to ```Position_24.mrc.mdoc```, keep the original mdoc.

    Copy gain reference:

    ```cp frames_tiff/gain-reference.mrc frames_tiff_selected/```

    Preprocess and reconstruct tomogram:

    ```tomotools preprocess --mcbin 1 --frames ./frames_tiff_selected/frames --gainref ./frames_tiff_selected/gain-reference.mrc Position_24.mrc ./lukas-ts-aligned/```

    ```cd lukas-ts-aligned```

    ```tomotools reconstruct -d 3000 -b 4 --aretomo Position_24.mrc```

    ```cd ..```

    

    Aretomo 2 warp:

    ```mkdir lukas_warp```

    ```tomotools aretomo2warp --v2 --frames-dir frames_tiff_selected/frames -n Position_24 lukas-ts-aligned lukas_warp```

    Warp reconstruction:

    ```cp warp_reconstruction.sh ./lukas_warp/Position_24/```

    ```./warp_reconstruction.sh```


