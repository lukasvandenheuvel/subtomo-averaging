import os
import argparse
import numpy as np

def interleave_particles(particle_table):
    # Reshuffles particles so that particles from the same filament are not grouped together, improving S/N for abp job. 
    # The function assumes that the filament number is in column 22 of the particle table.

    # obtain filament number in the column 22 and reorder for better grouping
    helical_id = particle_table[:, 22]

    # Count particles per filament
    unique_ids, counts = np.unique(helical_id, return_counts=True)
    filament_counts = sorted(zip(unique_ids, counts), key=lambda x: x[1], reverse=True)

    # Assign filaments to groups to balance sizes
    group1_ids = []
    group2_ids = []
    group1_count = 0
    group2_count = 0

    for filament_id, count in filament_counts:
        if group1_count <= group2_count:
            group1_ids.append(filament_id)
            group1_count += count
        else:
            group2_ids.append(filament_id)
            group2_count += count

    # Create masks for each group
    group1_mask = np.isin(helical_id, group1_ids)
    group2_mask = np.isin(helical_id, group2_ids)

    # Get particles for each group
    group1_particles = particle_table[group1_mask]
    group2_particles = particle_table[group2_mask]

    # Interleave: 1/2/1/2/1/2...
    max_len = max(len(group1_particles), len(group2_particles))
    interleaved_list = []

    for i in range(max_len):
        if i < len(group1_particles):
            interleaved_list.append(group1_particles[i])
        if i < len(group2_particles):
            interleaved_list.append(group2_particles[i])

    edit_particle_table = np.array(interleaved_list)

    return edit_particle_table

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--i', required=True, help='Path to input .tbl file')
    args = parser.parse_args()

    input_tbl = args.i
    particle_table = np.loadtxt(input_tbl, comments='#', dtype=str)

    output_table = os.path.splitext(input_tbl)[0] + '_mod.tbl'
    edit_particle_table = interleave_particles(particle_table)
    np.savetxt(output_table, edit_particle_table, delimiter=' ', fmt='%s')
    print(f'Edited table written to: {output_table}')