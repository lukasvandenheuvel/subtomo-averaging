#!/usr/bin/env python3
"""
Merge columns from particles_warp.star into bin8_particles.star.
Adds _rlnHelicalTubeID, _rlnAngleTiltPrior, _rlnAnglePsiPrior, and _rlnAnglePsiFlipRatio
columns to bin8_particles.star.
"""

import sys
import argparse
import random
import subprocess
import os
from utils import read_star, write_star
import pandas as pd


def parse_tomostar_file(filename):
    """
    Parse a tomostar file and extract _wrpAngleTilt values.
    
    Returns:
        min_angle: Minimum value of -_wrpAngleTilt
        max_angle: Maximum value of -_wrpAngleTilt
    """
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    column_dict = {}
    angles = []
    in_loop = False
    in_data = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped == 'loop_':
            in_loop = True
            continue
        
        # Parse column names
        if in_loop and stripped.startswith('_'):
            parts = stripped.split()
            col_name = parts[0]
            column_dict[col_name] = len(column_dict)
            continue
        
        # Data section starts
        if in_loop and stripped and not stripped.startswith('_') and not stripped.startswith('#'):
            in_data = True
        
        # Store angle data
        if in_data and stripped:
            values = stripped.split()
            if '_wrpAngleTilt' in column_dict:
                angle_idx = column_dict['_wrpAngleTilt']
                if angle_idx < len(values):
                    angle = float(values[angle_idx])
                    angles.append(-angle)  # MINUS the angle
    
    if not angles:
        print(f"WARNING: No _wrpAngleTilt values found in {filename}")
        return 0.0, 0.0
    
    return min(angles), max(angles)


def edit_dynamo_tbl(dynamo_output, merged_star_file, min_tilt, max_tilt):
    """
    Edit the Dynamo .tbl file with specific column values and write to a new file.
    
    Args:
        dynamo_output: Path to particles (tbl) file (without .tbl extension)
        merged_star_file: Path to merged star file to get HelicalTubeID
        min_tilt: Minimum tilt angle (column 14)
        max_tilt: Maximum tilt angle (column 15)
    """
    tbl_file = dynamo_output + '.tbl'
    print(f"\nReading {tbl_file}...")
    
    # Parse merged star file to get HelicalTubeID values
    _, star_df = read_star(merged_star_file)
    
    if '_rlnHelicalTubeID' not in star_df.columns:
        print(f"ERROR: _rlnHelicalTubeID not found in {merged_star_file}")
        sys.exit(1)
    
    tube_ids = star_df['_rlnHelicalTubeID'].tolist()
    
    # Read tbl file
    with open(tbl_file, 'r') as f:
        lines = f.readlines()
    
    output_lines = []
    particle_idx = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            # Keep comments and empty lines
            output_lines.append(line)
            continue
        
        # Parse data line
        values = stripped.split()
        
        if len(values) < 23:
            print(f"WARNING: Line has fewer than 23 columns, skipping: {line}")
            output_lines.append(line)
            continue
        
        # Edit specific columns (1-indexed -> 0-indexed)
        values[12] = '2'  # Column 13
        values[15] = str(-max_tilt)  # Column 16
        values[16] = str(-min_tilt)  # Column 17
        values[19] = '1'  # Column 20
        
        # Column 23: HelicalTubeID from merged star file
        if particle_idx < len(tube_ids):
            values[22] = tube_ids[particle_idx]  # Column 23
        
        # Write back the modified line
        output_line = ' '.join(values) + '\n'
        output_lines.append(output_line)
        particle_idx += 1
    
    # Write to new tbl file (particles_edit.tbl)
    output_tbl_file = os.path.join(dynamo_output+'_edit.tbl')
    with open(output_tbl_file, 'w') as f:
        f.writelines(output_lines)
    
    print(f"Modified {particle_idx} particles")
    print(f"  Column 13: set to 2")
    print(f"  Column 16: set to {-max_tilt}")
    print(f"  Column 17: set to {-min_tilt}")
    print(f"  Column 20: set to 1")
    print(f"  Column 23: set to _rlnHelicalTubeID from merged star file")
    print(f"Output written to: {output_tbl_file}")


def merge_star_files(left_file, right_file, output_file, bin_left=8, bin_right=1, randomize_rot=False):
    """
    Merge two STAR files by matching particles on their coordinates.

    Coordinates are normalised to bin-1 pixel space (coord * bin_factor) before
    matching.  Columns from left_file are merged into right_file.
    _rlnAngleTiltPrior / _rlnAnglePsiPrior are renamed to _rlnAngleTilt / _rlnAnglePsi.
    A new _rlnAngleRot column is appended.
    """
    print(f"Reading {left_file}...")
    _, left_df = read_star(left_file)
    print(f"Reading {right_file}...")
    _, right_df = read_star(right_file)
    print(f"Left file has {len(left_df)} particles")
    print(f"Right file has {len(right_df)} particles")

    # Columns to bring from left, and how to rename them in output
    right_col_map = {
        '_rlnAngleTiltPrior':          '_rlnAngleTilt',
        '_rlnAnglePsiPrior':           '_rlnAnglePsi',
        '_rlnAngleRotPrior':           '_rlnAngleRot'
    }
    right_df = right_df.rename(columns=right_col_map)
    
    # Sanity check: both files must have the same number of particles
    assert len(left_df) == len(right_df), \
        f"Particle count mismatch: left={len(left_df)}, right={len(right_df)}"

    # Verify coordinate correspondence by index
    coord_axes = ['_rlnCoordinateX', '_rlnCoordinateY', '_rlnCoordinateZ']
    left_coords = left_df[coord_axes].astype(float).values * bin_left
    right_coords = right_df[coord_axes].astype(float).values * bin_right
    dists = ((left_coords - right_coords) ** 2).sum(axis=1) ** 0.5
    max_dist = dists.max()
    print(f"Coordinate check: max distance = {max_dist:.4f} px (bin-1 space)")
    bad = dists > 0.1
    if bad.any():
        n_bad = int(bad.sum())
        print(f"WARNING: {n_bad} particles exceed 0.1 px distance:")
        for i in bad.nonzero()[0][:10]:
            print(f"  row {i}: left={left_coords[i]}  right={right_coords[i]}  dist={dists[i]:.4f}")

    # Merge by index: left columns take priority, add right-only columns
    right_only_cols = [c for c in right_df.columns if c not in left_df.columns]
    merged = pd.concat([left_df.reset_index(drop=True),
                        right_df[right_only_cols].reset_index(drop=True)], axis=1)

    # Add _rlnAngleRot
    if '_rlnAngleRot' not in merged.columns:
        if randomize_rot:
            merged['_rlnAngleRot'] = [f"{random.uniform(-180, 180):.6f}" for _ in range(len(merged))]
        else:
            merged['_rlnAngleRot'] = '0.0'

    print(f"Merged {len(merged)} particles")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    write_star(output_file, ["data_particles\n", "\n", "loop_\n"], merged)
    print(f"Output written to: {output_file}")


def star_to_table(output_file, dynamo_output, tomostar_file, box_size=64):
    """
    Convert a merged STAR file to a Dynamo .tbl using warp2dynamo, then
    annotate the table with the tilt-angle range and helical tube IDs.
    """
    import glob

    print(f"\nRunning warp2dynamo...")
    os.makedirs(os.path.dirname(dynamo_output), exist_ok=True)

    for existing_file in glob.glob(dynamo_output+'*'):
        print(f"Removing existing file: {existing_file}")
        os.remove(existing_file)

    cmd = ['warp2dynamo', '-i', output_file, '-o', dynamo_output, '-bs', str(box_size)]
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("warp2dynamo completed successfully")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: warp2dynamo failed with return code {e.returncode}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR: warp2dynamo command not found. Make sure it's in your PATH.")
        sys.exit(1)

    print(f"\nParsing {tomostar_file}...")
    min_tilt, max_tilt = parse_tomostar_file(tomostar_file)
    print(f"Tilt angle range: {min_tilt:.2f} to {max_tilt:.2f}")

    tbl_file = dynamo_output + '.tbl'
    if os.path.exists(tbl_file):
        edit_dynamo_tbl(dynamo_output, output_file, min_tilt, max_tilt)
    else:
        print(f"WARNING: Expected output file {tbl_file} not found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Merge columns from particles_warp.star into binned particles STAR file.'
    )
    
    parser.add_argument(
        '-r', '--root',
        required=True,
        metavar='ROOT_DIR',
        help='Root directory where all files are located'
    )
    
    parser.add_argument(
        '-i', '--input',
        nargs=2,
        metavar=('COORDINATES_STARFILE', 'ANGLES_STARFILE'),
        required=True,
        help='Input STAR filenames (no paths): star file containing correct (binned) coordinates (1st) and file containing euler angles (2nd)'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        metavar='OUTPUT_FILE',
        help='Output merged STAR filename (no path)'
    )
    
    parser.add_argument(
        '-b', '--binning',
        type=int,
        default=8,
        metavar='BINNING',
        help='Binning factor (default: 8)'
    )
    
    parser.add_argument(
        '--randomize_rot',
        action='store_true',
        help='Randomize _rlnAngleRot values uniformly between -180 and 180 (default: fill with 0)'
    )
    
    parser.add_argument(
        '-t', '--tomostar',
        metavar='TOMOSTAR_FILE',
        help='Tomostar filename (no path) for extracting tilt angles (optional). If provided, will run warp2dynamo and edit the output.'
    )
    
    parser.add_argument(
        '-bs', '--box-size',
        type=int,
        default=64,
        metavar='BOX_SIZE',
        dest='box_size',
        help='Box size for warp2dynamo (default: 64)'
    )
    
    args = parser.parse_args()
    
    # Construct full paths from root directory and filenames
    root_dir = args.root
    angles_starfile = os.path.join(root_dir, args.input[0])
    binned_starfile = os.path.join(root_dir, args.input[1])
    output_file = os.path.join(root_dir, args.output)
    binning = args.binning
    randomize_rot = args.randomize_rot
    tomostar_file = os.path.join(root_dir, args.tomostar) if args.tomostar else None
    box_size = args.box_size
    
    merge_star_files(angles_starfile, binned_starfile, output_file, bin_left=binning, bin_right=1, randomize_rot=randomize_rot)
    if tomostar_file:
        dynamo_output = os.path.join(root_dir, f'dynamo/particles_b{binning}')
        star_to_table(output_file, dynamo_output, tomostar_file, box_size)
