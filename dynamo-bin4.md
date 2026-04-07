---
layout: default
---

# Dynamo: Refine the model at bin4

## Re-extract particles

12. Now, convert the refined tbl files to star files for warp exports:

    ```shell
    python convert_tbl_to_warp.py \
    -r $ROOT/warp \
    -t1 dynamo/dynamo_project_b8/abp_align_eo/results/ite_0004/averages/refined_table_ref_001_ite_0004.tbl \
    -t2 dynamo/dynamo_project_b8/abp_align_eo/results/ite_0004/averages/refined_table_ref_002_ite_0004.tbl \
    -w particles_warp.star \
    -o particles_dynamo_b4.star \
    -a $ANGPIX \
    -tm dynamo/particles_b8.reextract.doc \
    -b 8 # binning of the reference (was bin8) 
    ```

13. Do the warp export at bin 4:
    ```shell
    # Compute angpix binned by 4 and box diameter (floor)
    ANGPIX_BIN4=$(echo "$ANGPIX * 4" | bc)
    BOXDIM=$(awk "BEGIN { print int($ANGPIX_BIN4 * $BOXSIZE) }")
    # Export particles
    cd $ROOT/warp
    WarpTools ts_export_particles \
    --settings warp_tiltseries.settings \
    --input_star particles_dynamo_b4.star \
    --output_star relion3_b4_particles.star \
    --coords_angpix $ANGPIX \
    --output_angpix $ANGPIX_BIN4 \
    --box $BOXSIZE \
    --diameter $BOXDIM \
    --relative_output_paths \
    --3d \
    --output_processing bin_4_3d
    ```
    Then convert the warp file to a table:
    ```shell
    cd $REPOSITORY
    conda activate tomotools
    python3 convert_warp_to_tbl.py \
    -r $ROOT/warp \
    -i relion3_b4_particles.star particles_dynamo_b4.star \
    -o relion3_b4_particles_merged.star \
    -t processing/tomostar/$TOMONAME'_ali.tomostar' \
    -bs $BOXSIZE -b 4
    ```
    And subsequently the CTF correction:

    ```bash
    python3 correct_ctf_subtomo.py \
    -r $ROOT/warp \
    -s relion3_b4_particles_merged.star \
    -t dynamo/particles_b4_edit.tbl \
    -o dynamo/filamentsData_b4_ctf/ \
    --bpf 0.002 0.5 \
    --ctf_method wiener \
    --wiener_epsilon 0.1 \
    --nproc 54 
    ```
    Now, generate the ```dynamo_project_b4``` directory and copy the files there:
    ```bash
    cd $ROOT/warp/dynamo
    mkdir dynamo_project_b4 && cd dynamo_project_b4
    cp ../particles_b4_edit.tbl ./particles_b4_edit.tbl
    mv ../filamentsData_b4_ctf ./
    ```
14. You are ready to create a dynamo average here:
    ```bash
    dynamo
    ```
    ```matlab
    oa=daverage('filamentsData_b4_ctf','t','particles_b4_edit.tbl','mw',50);
    ```
    ```matlab
    dwrite(oa.average,'raw_template.em');
    ```
    The twist should be visible, so you can search it:
    ```shell
    e2proc3d.py --mult=-1 raw_template.em raw_template.mrc
    ```
    ```shell
    relion_image_handler --i raw_template.mrc --o raw_template.mrc --force_header_angpix $ANGPIX_BIN4
    ```
    ```shell
    relion_helix_toolbox --i raw_template.mrc --twist_min 1 --twist_max 1.9 --rise_min 4.75 --rise_max 4.8 --z_percentage 0.3 --search --cyl_outer_diameter 200 --angpix $ANGPIX_BIN4
    ```
    Below, set the twist and rise to the optima found above:
    ```shell
    # Apply symmetry
    relion_helix_toolbox --i raw_template.mrc --twist 1.09 --rise 4.8 --z_percentage 0.3 --impose --cyl_outer_diameter 160 --angpix $ANGPIX_BIN4 --o raw_template_sym.mrc
    ```
    ```shell
    # Convert back to .em with pixel size 1
    relion_image_handler --i raw_template_sym.mrc --o raw_template_sym.mrc --force_header_angpix 1
    ```
    ```shell
    e2proc3d.py --mult=-1 raw_template_sym.mrc raw_template_sym.em
    ```
15. Setup the dynamo project as below:
    ```
    dynamo
    ```
    ```matlab
    dcp.new('abp_align', 'd', 'filamentsData_b4_ctf','template','raw_template_sym.em','masks','default','t','particles_b4_edit.tbl');
    ```

    Mask parameters:

    | Parameter    | Value      |
    | --------     | -------    |
    | r            | ~12         |
    | h            | 30         |
    | Gaussian     | 3          |

    Numerical parameters:

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
    | symmetry                      | c1 or h[-1.01,0.606]    |
    | particle dimensions           | 64         |
    | shift limits                  | 4 4 2      |
    | shift limiting way            | 4          |

    You can apply helical symmetry, but **note that the sign of the twist is opposite of that in Relion, and that the rise is defined in *pixels*, not in Angstrom**.

    Now, adopt 2 references and particle sets:
    - multireferece > adaptive filtering..... > Derive a project
    - change project name to abp_align_eo
    - multireferece > adaptive filtering > Edit for adaptive run:

        | Parameter    | Value      |
        | --------     | -------    |
        | threshold            | 0.143         |
        | low-pass reolution            | 25         |
        | push back     | 0          |  

    Then check and unfold the project, and run the executable:

    ```
    ./abp_align_eo.exe
    ```





---

<p align="center">
  <a href="dynamo-bin8.html">← Back</a> | <a href="relion-refine.html">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>