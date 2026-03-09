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


def parse_star_file(filename):
    """
    Parse a STAR file and return header info and data lines.
    
    Returns:
        header_lines: List of lines before the data section
        column_names: List of column names in order
        column_dict: Dictionary mapping column name to index
        data_lines: List of data lines (as strings)
        data_values: List of data lines split into values
    """
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    header_lines = []
    column_names = []
    column_dict = {}
    data_lines = []
    data_values = []
    
    in_loop = False
    in_data = False
    
    for line in lines:
        stripped = line.strip()
        
        # Track loop section
        if stripped == 'loop_':
            in_loop = True
            header_lines.append(line)
            continue
        
        # Parse column names
        if in_loop and stripped.startswith('_'):
            parts = stripped.split()
            col_name = parts[0]
            column_names.append(col_name)
            # Column index in the dict (0-based)
            column_dict[col_name] = len(column_names) - 1
            header_lines.append(line)
            continue
        
        # Data section starts
        if in_loop and stripped and not stripped.startswith('_') and not stripped.startswith('#'):
            in_data = True
        
        # Store data lines
        if in_data:
            if stripped:  # Skip empty lines in data section
                data_lines.append(line)
                data_values.append(stripped.split())
        elif not in_data:
            header_lines.append(line)
    
    return header_lines, column_names, column_dict, data_lines, data_values


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


def edit_dynamo_tbl(tbl_file, merged_star_file, min_tilt, max_tilt):
    """
    Edit the Dynamo .tbl file with specific column values and write to a new file.
    
    Args:
        tbl_file: Path to particles.tbl file
        merged_star_file: Path to merged star file to get HelicalTubeID
        min_tilt: Minimum tilt angle (column 14)
        max_tilt: Maximum tilt angle (column 15)
    """
    print(f"\nReading {tbl_file}...")
    
    # Parse merged star file to get HelicalTubeID values
    _, _, star_dict, _, star_data = parse_star_file(merged_star_file)
    
    if '_rlnHelicalTubeID' not in star_dict:
        print(f"ERROR: _rlnHelicalTubeID not found in {merged_star_file}")
        sys.exit(1)
    
    tube_ids = []
    for values in star_data:
        tube_id = values[star_dict['_rlnHelicalTubeID']]
        tube_ids.append(tube_id)
    
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
        values[12] = '1'  # Column 13
        values[13] = str(min_tilt)  # Column 14
        values[14] = str(max_tilt)  # Column 15
        values[19] = '1'  # Column 20
        
        # Column 23: HelicalTubeID from merged star file
        if particle_idx < len(tube_ids):
            values[22] = tube_ids[particle_idx]  # Column 23
        
        # Write back the modified line
        output_line = ' '.join(values) + '\n'
        output_lines.append(output_line)
        particle_idx += 1
    
    # Write to new tbl file (particles_edit.tbl)
    output_tbl_file = os.path.join(os.path.dirname(tbl_file), 'particles_edit.tbl')
    with open(output_tbl_file, 'w') as f:
        f.writelines(output_lines)
    
    print(f"Modified {particle_idx} particles")
    print(f"  Column 13: set to 1")
    print(f"  Column 14: set to {min_tilt}")
    print(f"  Column 15: set to {max_tilt}")
    print(f"  Column 20: set to 1")
    print(f"  Column 23: set to _rlnHelicalTubeID from merged star file")
    print(f"Output written to: {output_tbl_file}")


def merge_star_files(warp_file, bin8_file, output_file, binning=8, randomize_rot=False, tomostar_file=None, box_size=64):
    """
    Merge columns from warp_file into bin8_file, then run warp2dynamo and edit the output.
    
    Args:
        warp_file: Path to particles_warp.star file
        bin8_file: Path to binned particles STAR file
        output_file: Path to output merged STAR file
        binning: Binning factor (default: 8)
        randomize_rot: If True, randomize _rlnAngleRot values between -180 and 180 (default: False)
        tomostar_file: Path to tomostar file for extracting tilt angles (optional)
        box_size: Box size for warp2dynamo (default: 64)
    """
    print(f"Reading {warp_file}...")
    warp_header, warp_cols, warp_dict, warp_lines, warp_data = parse_star_file(warp_file)
    
    print(f"Reading {bin8_file}...")
    bin8_header, bin8_cols, bin8_dict, bin8_lines, bin8_data = parse_star_file(bin8_file)
    
    print(f"Warp file has {len(warp_data)} particles")
    print(f"Bin8 file has {len(bin8_data)} particles")
    
    # Columns to merge from warp file (with original names)
    columns_from_warp = [
        '_rlnHelicalTubeID',
        '_rlnAngleTiltPrior',
        '_rlnAnglePsiPrior',
        '_rlnAnglePsiFlipRatio'
    ]
    
    # Output column names (renamed)
    columns_to_output = [
        '_rlnHelicalTubeID',
        '_rlnAngleTilt',
        '_rlnAnglePsi',
        '_rlnAnglePsiFlipRatio',
        '_rlnAngleRot'
    ]
    
    # Check if columns exist in warp file
    for col in columns_from_warp:
        if col not in warp_dict:
            print(f"ERROR: Column {col} not found in {warp_file}")
            sys.exit(1)
    
    # Check if columns already exist in bin8 file
    for col in columns_to_output:
        if col in bin8_dict:
            print(f"WARNING: Column {col} already exists in {bin8_file}, will be overwritten")
    
    # Match particles by coordinates (binned coords * binning should equal warp coords)
    # We'll match based on binned coordinates to handle rounding
    print(f"Matching particles with binning factor {binning}...")
    
    # Build a lookup dict for warp particles
    warp_lookup = {}
    for i, values in enumerate(warp_data):
        # Extract coordinates from warp file
        x = float(values[warp_dict['_rlnCoordinateX']])
        y = float(values[warp_dict['_rlnCoordinateY']])
        z = float(values[warp_dict['_rlnCoordinateZ']])
        
        # Bin them to match binned coordinates
        binned_x = round(x / binning, 3)
        binned_y = round(y / binning, 3)
        binned_z = round(z / binning, 3)
        
        key = (binned_x, binned_y, binned_z)
        warp_lookup[key] = values
    
    # Prepare output
    print("Merging columns...")
    
    # Update header with new columns
    new_column_names = bin8_cols.copy()
    next_col_num = len(bin8_cols) + 1
    
    for col in columns_to_output:
        if col not in bin8_dict:
            new_column_names.append(col)
    
    # Write header
    output_lines = []
    
    # Copy non-column header lines
    for line in bin8_header:
        if line.strip().startswith('_'):
            break
        output_lines.append(line)
    
    # Write updated column definitions
    for i, col_name in enumerate(new_column_names, start=1):
        output_lines.append(f"{col_name} #{i}\n")
    
    # Process data lines
    matched = 0
    unmatched = 0
    
    for bin8_values in bin8_data:
        # Get bin8 coordinates
        x = float(bin8_values[bin8_dict['_rlnCoordinateX']])
        y = float(bin8_values[bin8_dict['_rlnCoordinateY']])
        z = float(bin8_values[bin8_dict['_rlnCoordinateZ']])
        
        key = (round(x, 3), round(y, 3), round(z, 3))
        
        # Look up matching warp particle
        if key in warp_lookup:
            warp_values = warp_lookup[key]
            matched += 1
            
            # Build output line with merged columns
            output_values = bin8_values.copy()
            
            # Add columns from warp file (with renaming)
            for i, col_out in enumerate(columns_to_output):
                if col_out not in bin8_dict:  # Only add if not already present
                    if i < len(columns_from_warp):  # Columns from warp file
                        col_warp = columns_from_warp[i]
                        col_idx = warp_dict[col_warp]
                        output_values.append(warp_values[col_idx])
                    else:  # New column _rlnAngleRot
                        if randomize_rot:
                            angle_rot = random.uniform(-180, 180)
                            output_values.append(f"{angle_rot:.6f}")
                        else:
                            output_values.append("0.0")
            
            # Format and write line
            output_line = "  " + "  ".join(f"{val:>12}" if i < 3 else f"{val:>10}" 
                                           for i, val in enumerate(output_values)) + "\n"
            output_lines.append(output_line)
        else:
            unmatched += 1
            print(f"WARNING: No match found for bin8 particle at ({x}, {y}, {z})")
            
            # Still write the line but with placeholder values
            output_values = bin8_values.copy()
            for col in columns_to_output:
                if col not in bin8_dict:
                    output_values.append("0.0")
            
            output_line = "  " + "  ".join(f"{val:>12}" if i < 3 else f"{val:>10}" 
                                           for i, val in enumerate(output_values)) + "\n"
            output_lines.append(output_line)
    
    # Write output file
    print(f"Writing {output_file}...")
    with open(output_file, 'w') as f:
        f.writelines(output_lines)
    
    print(f"Done! Matched {matched} particles, {unmatched} unmatched")
    print(f"Output written to: {output_file}")
    
    # Run warp2dynamo if tomostar file is provided
    if tomostar_file:
        print(f"\nRunning warp2dynamo...")
        
        # Determine output directory and base name
        output_dir = os.path.dirname(output_file)
        # Create dynamo directory in the same location as output file
        dynamo_dir = os.path.join(output_dir, 'dynamo')
        os.makedirs(dynamo_dir, exist_ok=True)
        
        dynamo_output = os.path.join(dynamo_dir, 'particles')
        
        # Remove all existing output files to avoid conflicts
        import glob
        for existing_file in glob.glob(os.path.join(dynamo_dir, 'particles*')):
            print(f"Removing existing file: {existing_file}")
            os.remove(existing_file)
        
        # Run warp2dynamo command
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
        
        # Parse tomostar file for tilt angles
        print(f"\nParsing {tomostar_file}...")
        min_tilt, max_tilt = parse_tomostar_file(tomostar_file)
        print(f"Tilt angle range: {min_tilt:.2f} to {max_tilt:.2f}")
        
        # Edit the dynamo tbl file
        tbl_file = dynamo_output + '.tbl'
        if os.path.exists(tbl_file):
            edit_dynamo_tbl(tbl_file, output_file, min_tilt, max_tilt)
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
        metavar=('WARP_FILE', 'BINNED_FILE'),
        required=True,
        help='Input STAR filenames (no paths): particles_warp.star and binned particles file'
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
    warp_file = os.path.join(root_dir, args.input[0])
    bin8_file = os.path.join(root_dir, args.input[1])
    output_file = os.path.join(root_dir, args.output)
    binning = args.binning
    randomize_rot = args.randomize_rot
    tomostar_file = os.path.join(root_dir, args.tomostar) if args.tomostar else None
    box_size = args.box_size
    
    merge_star_files(warp_file, bin8_file, output_file, binning, randomize_rot, tomostar_file, box_size)
