#! /bin/bash

# Arguments
ANGPIX=$1
EXP=$2
BIN=$3
ANGPIX_BINNED=$(echo "$ANGPIX * $BIN" | bc)

echo ">> Running warp tomogram reconstruction with angpix="$ANGPIX" A, exposure="$EXP" e/A2 per tilt, and a binning of "$BIN" (binned angpix = "$ANGPIX_BINNED" A)"

WarpTools create_settings --folder_data frames --output warp_frameseries.settings --extension "*.mrc" --angpix $ANGPIX --exposure $EXP --folder_processing processing
echo ">> Created settings"

echo ">> CTF correction..."
WarpTools fs_motion_and_ctf --settings warp_frameseries.settings --m_grid 1x1x1 --c_grid 2x2x1 --c_range_min 50 --c_range_max 10 --c_defocus_max 8 --out_averages --c_use_sum --out_average_halves
echo ">> CTF correction DONE"

WarpTools ts_import --mdocs ./mdoc --frameseries ./processing --tilt_exposure $EXP --output ./processing/tomostar
echo ">> Imported tilt series"

WarpTools create_settings --folder_data processing/tomostar --output warp_tiltseries.settings --extension *.tomostar --angpix $ANGPIX --exposure $EXP --folder_processing processing --tomo_dimensions 4096x4096x3000
echo ">> Created settings (2/2)"

WarpTools ts_import_alignments --settings warp_tiltseries.settings --alignments ./imod --alignment_angpix $ANGPIX
echo ">> Imported alignment files"

WarpTools ts_defocus_hand --settings warp_tiltseries.settings --set_auto
echo ">> Handedness check done"

echo ">> CTF estimation ..."
WarpTools ts_ctf --settings warp_tiltseries.settings --defocus_max 8 --range_high 5
echo ">> CTF estimation DONE"

echo ">> Tomogram reconstruction"
WarpTools ts_reconstruct --settings warp_tiltseries.settings --angpix $ANGPIX_BINNED --dont_invert --deconv
echo ">> Done! Find results in processing/reconstruction"


