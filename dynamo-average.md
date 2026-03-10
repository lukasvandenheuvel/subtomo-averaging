# Generate an initial model with Dynamo

1. Move into ```warp/dynamo```. With the dynamo software, randomize the azimuth (=rot) angle and make a first average:
    ```matlab
    dynamo

    T = dread('particles_edit.tbl');
    T2 = dtrandomize_azimuth(T);
    dwrite(T2,'particles_edit_mod.tbl');
    oa=daverage('filamentsData_ctf','t','particles_edit_mod.tbl','mw',50);
    dwrite(oa.average,'raw_template_ctf.em');
    ```

    Check the output volume ```raw_template_ctf.em``` in ChimeraX. In ChimeraX, don't forget to flip the volume:
    ```vop scale #1 factor -1```

    ![Dynamo average](imgs/dynamo-01.png "Dynamo average")

2. Generate a new dynamo project with the tube as a template:
    ```matlab
    dcp.new('bin8_align_1', 'd', 'filamentsData_ctf','template','raw_template_ctf.em','masks','default','t','particles_edit_mod.tbl');
    
    dcp bin8_align_1
    ```