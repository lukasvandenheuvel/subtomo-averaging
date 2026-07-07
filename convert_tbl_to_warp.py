# Generating star files for warp in bin4

import numpy as np
import subprocess
import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from utils import read_star,write_star

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert Dynamo .tbl files to Warp STAR file.')
    parser.add_argument('-r', required=True, metavar='ROOT_DIR', dest='root', help='Path to warp directory')
    parser.add_argument('-t1', required=True, metavar='TABLE1', dest='t1', help='Relative path to first half-set .tbl file')
    parser.add_argument('-t2', required=True, metavar='TABLE2', dest='t2', help='Relative path to second half-set .tbl file')
    parser.add_argument('-w', required=True, metavar='WARP_STAR', dest='w', help='Relative path to reference STAR file')
    parser.add_argument('-o', required=True, metavar='OUTPUT_STAR', dest='o', help='Output STAR file name (relative to root)')
    parser.add_argument('-b', type=int, required=True, metavar='BINNING', dest='b', help='Binning factor of the reference STAR file')
    parser.add_argument('-a', type=float, required=True, metavar='ANGPIX', dest='angpix', help='Pixel size in Angstrom')
    parser.add_argument('-tm', required=True, metavar='TABLE_MAP', dest='tm', help='Relative path to Dynamo table map .doc file (e.g. dynamo/particles_b8.reextract.doc)')
    args = parser.parse_args()

    tomo_root_path = args.root
    particle_table1 = os.path.join(tomo_root_path, args.t1)
    particle_table2 = os.path.join(tomo_root_path, args.t2)
    star_ref = os.path.join(tomo_root_path, args.w)

    binning = args.b
    pixel_size = args.angpix

    # get particle index, corrected xyz coordinates, and euler angles for each tomogram

    par_table = np.concatenate((np.loadtxt(particle_table1, comments='#', dtype=str),np.loadtxt(particle_table2, comments='#', dtype=str)),axis=0)
    par_table = par_table[np.argsort(par_table[:, 0].astype(int))]
    tomo_indx = np.unique(par_table[:,19])
    assert len(tomo_indx) == 1, "Currently, only 1 tomogram can be processed at the time"

    # save temp splited table, convert to star for warp, and delet the temp table

    table_temp_path = os.path.join(tomo_root_path,'temp.tbl')
    np.savetxt(table_temp_path,par_table,delimiter=' ',fmt='%s')

    print("Converting Dynamo .tbl to Warp .star using dynamo2warp...")
    subprocess.run(['dynamo2warp','-i',table_temp_path,'-tm',os.path.join(tomo_root_path, args.tm),
                    '-o', os.path.join(tomo_root_path,'temp.star')])
    print("Conversion complete. Now processing the STAR file...")

    star_dyn_path = os.path.join(tomo_root_path,'temp.star')
    star_ref_path = os.path.join(tomo_root_path, args.w)
    # warp_rest_naming = os.path.join(tomo_root_path,'relion3_b8/particles_new_select.star')
    output_star = os.path.join(tomo_root_path, args.o)

    star_dyn_header, star_dyn_df = read_star(star_dyn_path)
    _, star_ref_df = read_star(star_ref_path)
    #_, warp_helical_df = read_star(warp_helical)
    particle_mask = (par_table[:, 0].astype(int)) - 1
    star_dyn_df["_rlnCoordinateX"] = star_dyn_df["_rlnCoordinateX"].astype(float)*binning
    star_dyn_df["_rlnCoordinateY"] = star_dyn_df["_rlnCoordinateY"].astype(float)*binning
    star_dyn_df["_rlnCoordinateZ"] = star_dyn_df["_rlnCoordinateZ"].astype(float)*binning
    star_dyn_df["_rlnMicrographName"] = star_ref_df['_rlnMicrographName'].iloc[0]
    #star_dyn_df["_rlnDetectorPixelSize"] = pixel_size
    star_dyn_df["_rlnHelicalTubeID"] = star_ref_df['_rlnHelicalTubeID'].iloc[particle_mask]
    star_dyn_df["_rlnAnglePsiFlipRatio"] = 0.5
    if '_rlnHelicalTrackLengthAngst' in star_ref_df.columns:
        star_dyn_df["_rlnHelicalTrackLengthAngst"] = star_ref_df['_rlnHelicalTrackLengthAngst'].iloc[particle_mask]
    else:
        print("WARNING: _rlnHelicalTrackLengthAngst not found in reference STAR file. Run add_tracklength_to_star.py to add it.")

    # Write the new STAR file
    write_star(output_star, star_dyn_header, star_dyn_df)
    print(f"Done! Wrote output star file to: {output_star}")

    os.remove(star_dyn_path)
    os.remove(table_temp_path)

