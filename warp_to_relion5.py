# Add angles, track length, prior angle, and random subset to the new star file


import argparse
import pandas as pd
import numpy as np
import os
from scipy.spatial.transform import Rotation as R
from utils import read_star, write_star


def convert_star_to_relion5(star1_file, star2_file, tomo_file, output_file, output_file_relative, tiltprior90=False, binning_factor=1):
    # Read star files
    star1_header_list, star1_df_list = read_star(star1_file)
    if len(star1_df_list) > 0:
        # Find the data_particles block in the star1 file
        star1_particles_block_idx = None
        for _i, _h in enumerate(star1_header_list):
            if any(l.strip().startswith('data_particles') for l in _h):
                star1_particles_block_idx = _i
                break
        if star1_particles_block_idx is None:
            star1_particles_block_idx = 0  # fall back to first block if no data_particles found
        star1_df = star1_df_list[star1_particles_block_idx]
    else:
        star1_df = star1_df_list

    star2_header_list, star2_df_list = read_star(star2_file)
    # Find the data_particles block (its index may vary depending on how many blocks the file has)
    particles_block_idx = None
    for _i, _h in enumerate(star2_header_list):
        if any(l.strip().startswith('data_particles') for l in _h):
            particles_block_idx = _i
            break
    if particles_block_idx is None:
        raise ValueError(f"No 'data_particles' block found in {star2_file}")
    star2_header = star2_header_list[particles_block_idx]
    star2_df = star2_df_list[particles_block_idx]

    tomo_header_list, tomo_df_list = read_star(tomo_file) # there are 2 data_ blocks in the tomo star file
    tomo_header = tomo_header_list[0] # assuming the first data_ block contains the relevant tomogram information
    tomo_df = tomo_df_list[0] # assuming the first data_ block contains the relevant tomogram information

    # Obtain tomogram dimensions from the tomo star file
    tomo_sizeX = float(tomo_df['_rlnTomoSizeX'].iloc[0])
    tomo_sizeY = float(tomo_df['_rlnTomoSizeY'].iloc[0])
    tomo_sizeZ = float(tomo_df['_rlnTomoSizeZ'].iloc[0])
    angpix = float(tomo_df['_rlnTomoTiltSeriesPixelSize'].iloc[0])

    # To the tilt-series path, add the relative path to the extraction job
    tomo_df['_rlnTomoTiltSeriesName'] = os.path.dirname(output_file_relative) + '/' + tomo_df['_rlnTomoTiltSeriesName']

    # assume column 1 is the “orig_filename” that embeds the particle number
    # relion_df['relion_particlenumber'] = pd.to_numeric(relion_df.iloc[:, 1], errors='coerce').astype('Int64')
    if '_rlnTomoParticleId' in star2_df.columns:
        idx = (star2_df['_rlnTomoParticleId'].astype(int) - 1).to_numpy()
    else:
        idx = np.arange(len(star2_df))

    # 1. READ ANGLES (From Relion 3D STAR)
    aligned_angles = star2_df[['_rlnAngleRot', '_rlnAngleTilt', '_rlnAnglePsi']].astype(float).to_numpy()

    if tiltprior90:
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
        star2_df[['_rlnAngleRot', '_rlnAngleTilt', '_rlnAnglePsi']] = new_subtomo_angles
        star2_df = star2_df.rename(columns=
                                   {'_rlnAngleRot': '_rlnTomoSubtomogramRot',
                                    '_rlnAngleTilt': '_rlnTomoSubtomogramTilt',
                                    '_rlnAnglePsi': '_rlnTomoSubtomogramPsi'}
        )
        star2_df['_rlnAngleRotPrior'] = 0
        star2_df['_rlnAngleTiltPrior'] = 90
        star2_df['_rlnAnglePsiPrior'] = 0
    else:
        # If tiltprior90 is False, keep the original angles
        star2_df[['_rlnAngleRot', '_rlnAngleTilt', '_rlnAnglePsi']] = aligned_angles
        
        # Take over rot-tilt-psi prior angles from the original star file if they exist
        if '_rlnAngleRotPrior' in star1_df.columns:
            star2_df['_rlnAngleRotPrior'] = star1_df['_rlnAngleRotPrior'].loc[idx].astype(float).values
        if '_rlnAngleTiltPrior' in star1_df.columns:
            star2_df['_rlnAngleTiltPrior'] = star1_df['_rlnAngleTiltPrior'].loc[idx].astype(float).values
        if '_rlnAnglePsiPrior' in star1_df.columns:
            star2_df['_rlnAnglePsiPrior'] = star1_df['_rlnAnglePsiPrior'].loc[idx].astype(float).values
        
        # Take over rot-tilt-psi tomo angles from the original star file if they exist
        if '_rlnTomoSubtomogramRot' in star1_df.columns:
            star2_df['_rlnTomoSubtomogramRot'] = star1_df['_rlnTomoSubtomogramRot'].loc[idx].astype(float).values
        if '_rlnTomoSubtomogramTilt' in star1_df.columns:
            star2_df['_rlnTomoSubtomogramTilt'] = star1_df['_rlnTomoSubtomogramTilt'].loc[idx].astype(float).values
        if '_rlnTomoSubtomogramPsi' in star1_df.columns:
            star2_df['_rlnTomoSubtomogramPsi'] = star1_df['_rlnTomoSubtomogramPsi'].loc[idx].astype(float).values

    # Fill in the new columns with default values or values from the original star file
    if '_rlnHelicalTrackLengthAngst' in star1_df.columns:
        star2_df['_rlnHelicalTrackLengthAngst'] = star1_df['_rlnHelicalTrackLengthAngst'].loc[idx].astype(float).values
    if '_rlnHelicalTubeID' in star1_df.columns:
        star2_df['_rlnHelicalTubeID'] = star1_df['_rlnHelicalTubeID'].loc[idx].astype(float).astype(int).values
    if '_rlnAnglePsiFlipRatio' in star1_df.columns:
        star2_df['_rlnAnglePsiFlipRatio'] = star1_df['_rlnAnglePsiFlipRatio'].loc[idx].astype(float).values
    else:
        star2_df['_rlnAnglePsiFlipRatio'] = 0.5
    
    # Add centered coordinates in Angstroms
    #star2_df['_rlnCenteredCoordinateXAngst'] = (star2_df['_rlnCoordinateX'].loc[idx].astype(float)*binning_factor-tomo_sizeX/2) * angpix * binning_factor
    #star2_df['_rlnCenteredCoordinateYAngst'] = (star2_df['_rlnCoordinateY'].loc[idx].astype(float)*binning_factor-tomo_sizeY/2) * angpix * binning_factor
    #star2_df['_rlnCenteredCoordinateZAngst'] = (star2_df['_rlnCoordinateZ'].loc[idx].astype(float)*binning_factor-tomo_sizeZ/2) * angpix * binning_factor
    
    # # Assign random subset for each filament
    # if '_rlnRandomSubset' in star1_df.columns:
    #     star2_df['_rlnRandomSubset'] = star1_df['_rlnRandomSubset'].loc[idx].astype(int).values
    # elif '_rlnHelicalTubeID' in star2_df.columns:
    #     star2_df['_rlnRandomSubset'] = star2_df['_rlnHelicalTubeID'].astype(int) % 2 + 1
    # else:
    #     star2_df['_rlnRandomSubset'] = 0

    # To the particle paths, add the relative path to the extraction job
    star2_df['_rlnImageName'] = os.path.dirname(output_file_relative) + '/' + star2_df['_rlnImageName']

    # Write the updated star file: replace the particles block, keep all others unchanged
    updated_dfs = [
        star2_df if i == particles_block_idx else star2_df_list[i]
        for i in range(len(star2_df_list))
    ]
    write_star(output_file, star2_header_list, updated_dfs)
    
    # Write the updated tomo star file: remember there are 2 data_ blocks in the tomo star file,
    # we need to keep the second one unchanged and only update the first one
    write_star(os.path.splitext(output_file)[0]+'_tomograms.star', tomo_header_list, [tomo_df, tomo_df_list[1]])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Warp star file to Relion5 format with angles, track length, and random subset.')
    parser.add_argument('--relionroot', required=True, help='Path to the relion project directory')
    parser.add_argument('--prestar', required=True, help='Relative path to star file before warpTools extraction')
    parser.add_argument('--poststar', required=True, help='Relative path to star file after warpTools extraction')
    parser.add_argument('--tomo', required=True, help='Relative path to tomostar file')
    parser.add_argument('--bin', required=True, help='Binning factor of star file after extraction')
    parser.add_argument('--out', required=True, help='Relative path to output star file')
    parser.add_argument('--tiltprior90', action='store_true', help='Update subtomo angles by removing the 90-degree tilt prior')
    args = parser.parse_args()

    star1_path = os.path.join(args.relionroot, args.prestar)
    star2_path = os.path.join(args.relionroot, args.poststar)
    tomo_path = os.path.join(args.relionroot, args.tomo)
    tomo_out = os.path.join(args.relionroot, args.out)
    binning_factor = float(args.bin)
    convert_star_to_relion5(star1_path, star2_path, tomo_path, tomo_out, args.out, tiltprior90=args.tiltprior90, binning_factor=binning_factor)

    # write a new optimisation set star file
    opt_out = os.path.join(args.relionroot, os.path.splitext(args.out)[0]+'_optimisation_set.star')
    tomo_star = os.path.splitext(args.out)[0] + '_tomograms.star'
    with open(opt_out, 'w') as f:
        f.write('\ndata_optimisation_set\n\n')
        f.write('loop_\n')
        f.write('_rlnTomoParticlesFile #1\n')
        f.write('_rlnTomoTomogramsFile #2\n')
        f.write(f'{args.out}\t{tomo_star}\n')
