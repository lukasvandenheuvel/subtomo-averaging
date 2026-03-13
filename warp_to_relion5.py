# Add angles, track length, prior angle, and random subset to the new star file


import argparse
import pandas as pd
import numpy as np
import os
from scipy.spatial.transform import Rotation as R
from utils import read_star, write_star


def convert_star_to_relion5(warp_file, relion_file, tomo_file, output_file):
    # Read star files
    warp_header, warp_df = read_star(warp_file)

    relion_header_list, relion_df_list = read_star(relion_file)
    relion_header = relion_header_list[2] # assuming the first data_ block contains the relevant particle information
    relion_df = relion_df_list[2] # assuming the first data_ block contains the relevant particle information
    assert relion_header[0].startswith('data_particles'), "The second data block in the relion star file needs to contain the particle data."

    tomo_header_list, tomo_df_list = read_star(tomo_file) # there are 2 data_ blocks in the tomo star file
    tomo_header = tomo_header_list[0] # assuming the first data_ block contains the relevant tomogram information
    tomo_df = tomo_df_list[0] # assuming the first data_ block contains the relevant tomogram information

    # Obtain tomogram dimensions from the tomo star file
    tomo_sizeX = float(tomo_df['_rlnTomoSizeX'].iloc[0])
    tomo_sizeY = float(tomo_df['_rlnTomoSizeY'].iloc[0])
    tomo_sizeZ = float(tomo_df['_rlnTomoSizeZ'].iloc[0])

    # assume column 1 is the “orig_filename” that embeds the particle number
    # relion_df['relion_particlenumber'] = pd.to_numeric(relion_df.iloc[:, 1], errors='coerce').astype('Int64')
    idx = (relion_df['_rlnTomoParticleId'].astype(int) - 1).to_numpy()

    # # 1. READ ANGLES (From Relion 3D STAR)
    aligned_angles = relion_df[['_rlnAngleRot', '_rlnAngleTilt', '_rlnAnglePsi']].astype(float).to_numpy()

    # 2. DEFINE ROTATIONS (Using Lowercase 'zyz' for Intrinsic/Relion Standard)
    r_aligned = R.from_euler('zyz', aligned_angles, degrees=True)
    r_prior   = R.from_euler('zyz', [0.0, 90.0, 0.0], degrees=True)

    # 3. CALCULATE SUBTOMO ANGLES
    # Logic: The Final Alignment = Subtomo_Orientation * Prior_Offset
    # Therefore: Subtomo_Orientation = Final_Alignment * Inverse(Prior_Offset)
    r_subtomo = r_aligned * r_prior.inv()

    # 4. EXTRACT NEW ANGLES
    new_subtomo_angles = r_subtomo.as_euler('zyz', degrees=True)

    # 5. UPDATE DATAFRAME
    relion_df[['_rlnAngleRot', '_rlnAngleTilt', '_rlnAnglePsi']] = new_subtomo_angles
    relion_df['_rlnHelicalTrackLengthAngst'] = warp_df['_rlnHelicalTrackLengthAngst'].loc[idx].astype(float).values
    relion_df['_rlnAnglePsiFlipRatio'] = 0.5
    relion_df['_rlnAngleRotPrior'] = 0
    relion_df['_rlnAngleTiltPrior'] = 90
    relion_df['_rlnAnglePsiPrior'] = 0
    relion_df['_rlnHelicalTubeID'] = warp_df['_rlnHelicalTubeID'].loc[idx].astype(float).astype(int).values
    relion_df['_rlnCenteredCoordinateXAngst'] = (warp_df['_rlnCoordinateX'].astype(float)-tomo_sizeX/2)
    relion_df['_rlnCenteredCoordinateYAngst'] = (warp_df['_rlnCoordinateY'].astype(float)-tomo_sizeY/2)
    relion_df['_rlnCenteredCoordinateZAngst'] = (warp_df['_rlnCoordinateZ'].astype(float)-tomo_sizeZ/2)
    relion_df['_rlnRandomSubset'] = 0

    # Assign random subset for each filament
    filamentIDs = relion_df['_rlnHelicalTubeID'].unique()
    for fid in filamentIDs:
        mask = relion_df['_rlnHelicalTubeID'] == fid  
        # Put the same filament coordinarte into the same group
        relion_df.loc[mask, '_rlnRandomSubset'] = float(fid) % 2 + 1

    # Write the updated star file: remember there are 2 data_ blocks in the relion star file, 
    # we need to keep the first one unchanged and only update the second one
    write_star(output_file, relion_header_list, [relion_df_list[0],relion_df_list[1],relion_df])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Warp star file to Relion5 format with angles, track length, and random subset.')
    parser.add_argument('--root', required=True, help='Root path')
    parser.add_argument('--warp', required=True, help='Path to warp star file')
    parser.add_argument('--relion', required=True, help='Path to relion5 star file')
    parser.add_argument('--tomo', required=True, help='Path to tomostar file')
    parser.add_argument('--out', required=True, help='Path to output star file')
    args = parser.parse_args()

    warp_path = os.path.join(args.root, args.warp)
    relion_path = os.path.join(args.root, args.relion)
    tomo_path = os.path.join(args.root, args.tomo)
    tomo_out = os.path.join(args.root, args.out)
    convert_star_to_relion5(warp_path, relion_path, tomo_path, tomo_out)
