---
layout: default
---

# Dynamo: Generate an initial model

## Subtomogram extraction at bin 8 

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
    - Adds tilt, psi priors to relion3_bin8_particles.star
    - Convert to tbl with warp2dynamo
    - Edits tbl file to include min and max tilt angle and helical tube ID.
    ```shell
    python3 convert_warp_to_tbl.py \
    -r $ROOT/warp \
    -i relion3_b8_particles.star particles_warp.star \
    -o relion3_b8_particles_merged.star \
    -t processing/tomostar/$TOMONAME'_ali.tomostar' \
    -bs $BOXSIZE -b 8
    ```

4. Do CTF correction of the extracted particles with ```correct_ctf_subtomo.py```:
    ```bash
    conda activate tomotools

    python3 correct_ctf_subtomo.py \
    -r $ROOT/warp \
    -s relion3_b8_particles_merged.star \
    -t dynamo/particles_b8_edit.tbl \
    -o dynamo/filamentsData_b8_ctf/ \
    --bpf 0.002 0.5 \
    --ctf_method wiener \
    --wiener_epsilon 0.1 \
    --nproc 54 
    ```
    This will take a few minutes with 54 processes.
    

## Average tube at bin 8

5. Move into ```warp/dynamo``` and create a project directory called ```dynamo_project_b8```:

    ```bash
    source params.sh # if you hadn't done it yet
    cd $ROOT/warp/dynamo
    mkdir dynamo_project_b8 && cd dynamo_project_b8
    cp ../particles_edit.tbl ./particles_edit.tbl
    mv ../filamentsData_ctf ./
    ```


    With the dynamo software, randomize the azimuth (=rot) angle and make a first average:
    ```shell
    dynamo
    ```
    ```matlab
    T = dread('particles_edit.tbl');
    T2 = dtrandomize_azimuth(T);
    dwrite(T2,'particles_edit_mod.tbl');
    % Generate average (should be a tube)
    oa = daverage('filamentsData_ctf','t','particles_edit_mod.tbl','mw',50);
    dwrite(oa.average,'raw_template_ctf.em');
    ```

    Check the output volume ```raw_template_ctf.em``` in ChimeraX. In ChimeraX, don't forget to flip the volume:  
    ```vop scale #1 factor -1```

    ![Dynamo average](imgs/dynamo-01.png "Dynamo average")

## Particle alignment at bin 8

6. Generate a new dynamo project with the tube as a template:
    ```matlab
    dcp.new('bin8_align_1', 'd', 'filamentsData_ctf','template','raw_template_ctf.em','masks','default','t','particles_edit_mod.tbl');

    dcp bin8_align_1
    ```

    The dynamo window will open. 
    
7. Generate a mask: Click on "masks", then "masks editor".

    ![Dynamo open mask editor](imgs/dynamo-02.png "Dynamo open mask editor")

    Generate a mask with the following specifications:

    | Parameter    | Value      |
    | --------     | -------    |
    | r            | 15         |
    | h            | 50         |
    | Gaussian     | 3          |

    Then, click "create mask", and you can "view" it to check. Once you are happy, click "Transfer mask to Wizard" (top left) and hit all 3 options individually (alignment mask, classification mask and smoothing mask). Close the mask editor.

    ![Dynamo generate mask](imgs/dynamo-03.png "Dynamo generate mask")

8. In the "Input mask" window, hit "Fill with ones" for "Fourier mask on template", then OK:

    ![Dynamo fill fourier mask](imgs/dynamo-04.png "Dynamo fill fourier mask")

9. Set the numerical parameters of the alignment (only the parameters to change are listed, leave the rest default):

    | Parameter                 | round 1    | round 2    |
    | --------                  | -------    | -------    |
    | iterations                | 2          | 2         |
    | cone aperture             | 20         | 20         |
    | cone sampling             | 3          | 3          |
    | **Advanced:** cone flip   | 2          | 2          |
    | azymuth rotation angle    | 360        | 45          |
    | azymuth rotation sampling | 15         | 5          |
    | refine                    | 2          | 2          |
    | refine factor             | 2          | 2          |
    | high pass                 | 2          | 2          |
    | low                       | 25         | 25          |
    | particle dimensions       | 64         | 64          |
    | shift limits              | 4 4 2      | 4 4 2          |
    | shift limiting way        | 4          | 4          |


    ![Dynamo numerical parameters](imgs/dynamo-05.png "Dynamo numerical parameters")

10. Set the computing environment to the specifications of your computing system.  
    In our case: *GPU standalone*,
    
    | Parameter    | Value      |
    | --------     | -------    |
    | GPU identifier            | 0 1 2 3         |
    | CPU core            | 1         |
    | Parallelize     | 50          |

11. In the dynamo main window, hit "check", then "unfold". Close dynamo.

12. In the terminal, leave the dynamo environment (```ctrl + c```) and run the project executable:
    ```bash
    ./bin8_align_1.exe
    ```
    and wait for the alignment to finish (can take >8 hours with ~7000 particles).

## Search for Symmetry
13. When you see helical symmetry in your average, search for that symmetry:

    ```bash
    cd $ROOT/warp/dynamo/dynamo_project_b8
    # Copy the volume and tbl file of the last iteration to your dynamo project folder
    cp bin8_align_1/results/ite_0004/averages/average_ref_001_ite_0004.em ./
    cp bin8_align_1/results/ite_0004/averages/refined_table_ref_001_ite_0004.tbl ./
    # Convert .em volume to .mrc
    e2proc3d.py --mult=-1 average_ref_001_ite_0004.em average_ref_001_ite_0004.mrc
    # Set pixel size
    relion_image_handler --i average_ref_001_ite_0004.mrc --o average_ref_001_ite_0004.mrc --force_header_angpix 15.84
    # Search symmetry in Relion
    relion_helix_toolbox --i average_ref_001_ite_0004.mrc --twist_min 0.5 --twist_max 2 --rise_min 4.5 --rise_max 4.9 --z_percentage 0.3 --search --cyl_outer_diameter 200 --angpix 15.84
    # Impose symmetry to the average (change twist and rise to the optimal values from previous command)
    relion_helix_toolbox --i average_ref_001_ite_0004.mrc --twist 1.01 --rise 4.8 --z_percentage 0.3 --impose --cyl_outer_diameter 200 --angpix 15.84 --o average_ref_001_ite_0004_sym.mrc
    # Set pixel size back to 1 for Dynamo
    relion_image_handler --i average_ref_001_ite_0004_sym.mrc --o average_ref_001_ite_0004_sym.mrc --force_header_angpix 1
    # Convert .em back to .mrc for Dynamo
    e2proc3d.py --mult=-1 average_ref_001_ite_0004_sym.mrc average_ref_001_ite_0004_sym.em
    ```

## Gold-standard refinement at bin 8

14. To generate two half particle sets fo the gold-standard FSC calculation, we need to make sure that particles originating from the same filament end up in different particle sets.  
    ```shell
    cd $REPOSITORY
    
    python generate_goldstandard_tbl.py --i $ROOT/warp/dynamo/dynamo_project_b8/refined_table_ref_001_ite_0004.tbl
    ```
    This will generate a new file, ```refined_table_ref_001_ite_0004_mod.tbl```, where particles of different filaments are listed in an alternating fashion.

15. Create a new dynamo project in ```dynamo_project_b8```:  
    ```shell
    cd $ROOT/warp/dynamo/dynamo_project_b8
    dynamo
    ```
    ```matlab
    dcp.new('abp_align', 'd', 'filamentsData_ctf','template','average_ref_001_ite_0004_sym.em','masks','default','t','refined_table_ref_001_ite_0004_mod.tbl');
    ```

    Generate a new, smaller mask (see dynamo instructions above):

    | Parameter    | Value      |
    | --------     | -------    |
    | r            | ~12         |
    | h            | 30         |
    | Gaussian     | 3          |

    And use the following numeric parameters:

    | Parameter                     | round 1    |
    | --------                      | -------    |
    | iterations                    | 4          |
    | cone aperture                 | 20         |
    | cone sampling                 | 3          |
    | **Advanced:** cone flip       | 2          |
    | azymuth rotation angle        | 20        |
    | azymuth rotation sampling     | 3         |
    | **Advanced:** azymuth flip    | 2          |
    | refine                        | 2          |
    | refine factor                 | 2          |
    | high pass                     | 2          |
    | low                           | 25         |
    | symmetry                      | c1 or h[-1.01,0.3]    |
    | particle dimensions           | 64         |
    | shift limits                  | 4 4 2      |
    | shift limiting way            | 4          |

    You can apply helical symmetry, but **note that the sign of the twist is opposite of that in Relion, and that the rise is defined in *pixels*, not in Angstrom**.

    Now, adopt 2 references and particle sets:
    - multireferece > adaptive filtering..... > Derive a project
    - multireferece > adaptive filtering > Edit for adaptive run:

        | Parameter    | Value      |
        | --------     | -------    |
        | threshold            | 0.143         |
        | low-pass reolution            | 25         |
        | push back     | 0          |  


    - change project name to abp_align_eo

    Then check and unfold the project, and run the executable:

    ```
    ./abp_align_eo.exe
    ```
    Inspect the two half-maps once the job is done. If it looks reasonable, you can move on to the next binning.

{% include mrc-viewer.html id="bin8" file="volumes/dynamo-bin8.mrc" isolevel=3.0 %}

---

<p align="center">
  <a href="imod-picking.html">← Back</a> | <a href="dynamo-bin4.html">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>

