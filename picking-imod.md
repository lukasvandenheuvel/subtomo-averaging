# Pick filaments in IMOD and extract coordinates

1. Open the tomogram in ```3dmod```.
2. Select mode to **model**.
3. Edit >> Object >> Type...: In the object window, set Object type to **Open** and close the object window.

    ![Imod change object](imgs/imod-01.png "How to change the object type in imod")

4. Press ```v``` to open Model window.

5. In Model window, Edit >> Object.

6. In the Object window, choose the desired sphere size for visualisation (e.g., 3).

    ![Imod change sphere size](imgs/imod-02.png "How to change the sphere size in imod")

7. In the ZaP window: 
    - Go to one end of one filament 
    - Click mouse middle key to create a point for the new Contour 
    - Move along the Z with “page up&down” to the next slices 
    - Click mouse middle key to create the next point 
    - Make a few points until the other end of the filament 
    - Left click on an empty space to unselect the current Contour 
    - To the next filament and repeat...
    - Press ```\``` to open the slicer view, where you can change the tomogram rotation to better visualize your filaments in any direction.

    ![Imod picking](imgs/imod-03.png "How to pick filaments in imod")

    Useful shortcuts:
    - Press ```n``` to start a new filament
    - ```Shift + d``` to delete a filament

8. After picking, save the model as ```filaments.mod``` (on ZaP window, press ```s```).

9. Add points between start-end coordinates and create a coordinate file:
    ```shell
    # Add points between start-end, every 1 (binned) pixel
    addModPts filaments.mod 1 
    # Convert to coordinate file
    model2point -c filaments_PtsAdded.mod filaments_PtsAdded.coords
    ```

10. Export particles with cryolo:
    ```shell
    cryolo_boxmanager_tools.py coords2star -i filaments_PtsAdded.coords -o out_warp/ --scale 4 --apix 1.98 --mag 64000 --flipratio 0.5
    ```
    
End of filament picking!<p align=center>
[<- Back](tomo-reconstruction.md) | [Next ->](dynamo-extraction.md) 
</p>