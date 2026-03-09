#!/usr/bin/env python3
"""
Convert subtomogram STAR file to helical processing format.

This script transforms Euler angles such that:
- rlnAngleTilt = 90 degrees (required for RELION helical processing)
- rlnAngleTiltPrior = 90 degrees
- The combined orientation (A_subtomogram × A_particle) remains unchanged

Based on RELION's ZYZ Euler angle convention from src/jaz/tomography/particle_set.cpp
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
import sys


def read_star_file(filename):
    """Read RELION STAR file and parse particles data block."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Find data_particles block
    particles_start = None
    for i, line in enumerate(lines):
        if line.strip() == 'data_particles':
            particles_start = i
            break
    
    if particles_start is None:
        raise ValueError("Could not find data_particles block")
    
    # Find loop_ and column headers
    loop_start = None
    for i in range(particles_start, len(lines)):
        if lines[i].strip().startswith('loop_'):
            loop_start = i
            break
    
    # Parse column headers
    headers = {}
    i = loop_start + 1
    col_idx = 0
    while i < len(lines) and lines[i].strip().startswith('_'):
        parts = lines[i].strip().split()
        if parts[0].startswith('_rln'):
            header_name = parts[0]
            headers[header_name] = col_idx
            col_idx += 1
        i += 1
    
    # Parse data lines
    data_start = i
    data_lines = []
    for i in range(data_start, len(lines)):
        line = lines[i].strip()
        if line and not line.startswith('#') and not line.startswith('data_'):
            data_lines.append(line)
    
    return lines, particles_start, data_start, headers, data_lines


def euler_zyz_to_matrix(phi, theta, psi):
    """
    Convert ZYZ Euler angles to rotation matrix.
    
    Following RELION convention from src/jaz/math/Euler_angles_relion.h:
    R = Rz(psi) * Ry(theta) * Rz(phi)
    
    Args:
        phi, theta, psi: Euler angles in degrees (ZYZ convention)
    
    Returns:
        3x3 rotation matrix
    """
    # RELION uses ZYZ intrinsic rotations
    # scipy Rotation uses extrinsic by default, so we reverse the order
    # or use intrinsic with lowercase 'zyz'
    rot = R.from_euler('zyz', [phi, theta, psi], degrees=True)
    return rot.as_matrix()


def matrix_to_euler_zyz(matrix):
    """
    Convert rotation matrix to ZYZ Euler angles.
    
    Following RELION convention.
    
    Args:
        matrix: 3x3 rotation matrix
    
    Returns:
        phi, theta, psi in degrees
    """
    rot = R.from_matrix(matrix)
    angles = rot.as_euler('zyz', degrees=True)
    return angles[0], angles[1], angles[2]


def decompose_with_fixed_tilt(total_matrix, target_tilt=90.0):
    """
    Decompose total rotation into subtomogram and particle rotations
    such that particle has angles (0, target_tilt, 0).
    
    A_total = A_subtomogram × A_particle
    
    We fix A_particle = Euler(0, target_tilt, 0) = Ry(target_tilt)
    
    Then solve for:
    A_subtomogram = A_total × A_particle^(-1)
    
    Args:
        total_matrix: Current combined rotation matrix
        target_tilt: Desired tilt angle for particle (default 90.0)
    
    Returns:
        tuple: (subtomo_rot, subtomo_tilt, subtomo_psi, 
                particle_rot, particle_tilt, particle_psi)
    """
    # The current combined rotation is what we need to preserve
    R_total = R.from_matrix(total_matrix)
    
    # Fix particle angles to (0, target_tilt, 0)
    # In ZYZ convention: Euler(0, theta, 0) = Ry(theta)
    R_particle_fixed = R.from_euler('zyz', [0, target_tilt, 0], degrees=True)
    
    # Solve for subtomogram rotation
    # A_total = A_subtomo × A_particle
    # A_subtomo = A_total × A_particle^(-1)
    R_subtomo_new = R_total * R_particle_fixed.inv()
    
    subtomo_angles = R_subtomo_new.as_euler('zyz', degrees=True)
    particle_angles = [0, target_tilt, 0]
    
    return (subtomo_angles[0], subtomo_angles[1], subtomo_angles[2],
            particle_angles[0], particle_angles[1], particle_angles[2])


def process_star_file(input_file, output_file):
    """
    Process STAR file to convert to helical format.
    
    Args:
        input_file: Input STAR file path
        output_file: Output STAR file path
    """
    # Read input file
    lines, particles_start, data_start, headers, data_lines = read_star_file(input_file)
    
    # Get column indices
    col_subtomo_rot = headers.get('_rlnTomoSubtomogramRot')
    col_subtomo_tilt = headers.get('_rlnTomoSubtomogramTilt')
    col_subtomo_psi = headers.get('_rlnTomoSubtomogramPsi')
    col_angle_rot = headers.get('_rlnAngleRot')
    col_angle_tilt = headers.get('_rlnAngleTilt')
    col_angle_psi = headers.get('_rlnAnglePsi')
    col_angle_tilt_prior = headers.get('_rlnAngleTiltPrior')
    col_angle_psi_prior = headers.get('_rlnAnglePsiPrior')
    
    # Process each particle
    new_data_lines = []
    
    for line in data_lines:
        parts = line.split()
        
        # Parse current angles
        subtomo_rot = float(parts[col_subtomo_rot])
        subtomo_tilt = float(parts[col_subtomo_tilt])
        subtomo_psi = float(parts[col_subtomo_psi])
        
        particle_rot = float(parts[col_angle_rot])
        particle_tilt = float(parts[col_angle_tilt])
        particle_psi = float(parts[col_angle_psi])
        
        # Compute current combined orientation
        # A_total = A_subtomogram × A_particle (following RELION convention)
        A_subtomo = euler_zyz_to_matrix(subtomo_rot, subtomo_tilt, subtomo_psi)
        A_particle = euler_zyz_to_matrix(particle_rot, particle_tilt, particle_psi)
        A_total = A_subtomo @ A_particle
        
        # Decompose with particle tilt = 90
        (new_subtomo_rot, new_subtomo_tilt, new_subtomo_psi,
         new_particle_rot, new_particle_tilt, new_particle_psi) = decompose_with_fixed_tilt(A_total, 90.0)
        
        # Update the line
        parts[col_subtomo_rot] = f"{new_subtomo_rot:12.6f}"
        parts[col_subtomo_tilt] = f"{new_subtomo_tilt:12.6f}"
        parts[col_subtomo_psi] = f"{new_subtomo_psi:12.6f}"
        parts[col_angle_rot] = f"{new_particle_rot:12.6f}"
        parts[col_angle_tilt] = f"{new_particle_tilt:12.6f}"
        parts[col_angle_psi] = f"{new_particle_psi:12.6f}"
        parts[col_angle_tilt_prior] = f"{90.0:12.6f}"
        parts[col_angle_psi_prior] = f"{0.0:12.6f}"
        
        new_data_lines.append(' '.join(parts))
        
        # Verify the transformation preserves orientation
        A_subtomo_new = euler_zyz_to_matrix(new_subtomo_rot, new_subtomo_tilt, new_subtomo_psi)
        A_particle_new = euler_zyz_to_matrix(new_particle_rot, new_particle_tilt, new_particle_psi)
        A_total_new = A_subtomo_new @ A_particle_new
        
        error = np.linalg.norm(A_total - A_total_new)
        if error > 1e-6:
            print(f"Warning: Large error {error:.2e} for particle in line")
    
    # Write output file
    with open(output_file, 'w') as f:
        # Write everything up to data lines
        for i in range(data_start):
            f.write(lines[i])
        
        # Write new data lines
        for line in new_data_lines:
            f.write(line + '\n')
    
    print(f"Converted {len(new_data_lines)} particles")
    print(f"Output written to: {output_file}")
    print("All particles now have rlnAngleTilt = 90.0 degrees")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python convert_to_helical.py input.star output.star")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    process_star_file(input_file, output_file)
