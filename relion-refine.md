---
layout: default
---

# Relion: Refine

```
python convert_tbl_to_warp.py \
-r $ROOT/warp \ 
-t1 dynamo/dynamo_project_b4/abp_align_eo/results/ite_0004/averages/refined_table_ref_001_ite_0004.tbl \
-t2 dynamo/dynamo_project_b4/abp_align_eo/results/ite_0004/averages/refined_table_ref_002_ite_0004.tbl \ 
-w particles_dynamo_b4.star \
-o particles_dynamo_b2.star \
-a $ANGPIX \
-b 4 # binning of the reference (was bin4)
```
```
WarpTools ts_export_particles \
--settings warp_tiltseries.settings \
--input_star particles_dynamo_b2.star \
--output_star relion5_b2/particles.star \
--coords_angpix $ANGPIX \
--output_angpix 3.96 \
--box 64 \
--diameter 253 \
--relative_output_paths \
--2d \
--output_processing bin_2
```
```
Wen-Lu's notebook to rotate particles 90 degrees and re-define coordinates.
```

<p align="center">
  <a href="dynamo-bin4.html">← Back</a> | <a href=".">Next →</a>
  <br><br>
  <a href=".">Home</a>
</p>