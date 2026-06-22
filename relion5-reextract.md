---
layout: default
---

```shell
# Compute angpix binned by 4 and box diameter (floor)
ANGPIX_BIN4=$(echo "$ANGPIX * 4" | bc)
ANGPIX_BIN2=$(echo "$ANGPIX * 2" | bc)
BOXSIZE=128
BOXDIM=$(awk "BEGIN { print int($ANGPIX_BIN2 * $BOXSIZE) }")
# Export particles
cd $ROOT/warp
WarpTools ts_export_particles \
--settings warp_tiltseries.settings \
--input_star relion5_b4/Refine_job005_run_data.star \
--output_star relion5_b4/Extract/bin2_box$BOXSIZE/particles.star \
--coords_angpix $ANGPIX_BIN4 \
--output_angpix $ANGPIX_BIN2 \
--box $BOXSIZE \
--diameter $BOXDIM \
--relative_output_paths \
--2d \
--output_processing relion5_b4/Extract/bin2_box$BOXSIZE/
```

We need to update this file for relion5, however, no rotation of the tilt prior is needed:

```shell
conda activate tomotools
cd $REPOSITORY
python warp_to_relion5.py \
--relionroot $ROOT/warp/relion5_b4 \
--warp Refine_job005_run_data.star \
--relion Extract/bin2_box$BOXSIZE/particles.star \
--tomo Extract/bin2_box$BOXSIZE/particles_tomograms.star \
--out Extract/bin2_box$BOXSIZE/particles_relion5.star
```

Rescale your reference:

```shell
cd $ROOT/warp
ANGPIX_BIN4=$(echo "$ANGPIX * 4" | bc)
ANGPIX_BIN2=$(echo "$ANGPIX * 2" | bc)
relion_image_handler --i relion5_b4/Refine3D/job005/run_class001.mrc --o relion5_b4/Refine3D_job005_bin2.mrc --angpix $ANGPIX_BIN4 --rescale_angpix $ANGPIX_BIN2 --new_box $BOXSIZE --force_header_angpix $ANGPIX_BIN2
```

<p align="center">
  <a href="dynamo-to-relion5.html">← Back</a> | <a href=".">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>