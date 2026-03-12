import pandas as pd
import subprocess

def read_star(file_path):
    """
    Reads a STAR file (relion4 and relion5 format).

    For relion5 files with multiple data_ blocks, the last data_ block
    (typically data_particles) is read as the DataFrame. Everything up to
    and including the 'data_particles' / 'data_*' line and the subsequent
    'loop_' line is stored as the header.

    Returns:
        header: list of strings (lines up to and including 'loop_')
        df: DataFrame with column names from the STAR file
    """
    with open(file_path, 'r') as f:
        all_lines = f.readlines()

    # Find the last 'data_' block (relion5 may have data_optics + data_particles)
    last_data_idx = None
    for i, line in enumerate(all_lines):
        if line.strip().startswith('data_'):
            last_data_idx = i

    if last_data_idx is None:
        raise ValueError(f"No 'data_' block found in {file_path}")

    # Find 'loop_' after the last data_ line
    loop_idx = None
    for i in range(last_data_idx, len(all_lines)):
        if all_lines[i].strip() == 'loop_':
            loop_idx = i
            break

    if loop_idx is None:
        raise ValueError(f"No 'loop_' found after last data_ block in {file_path}")

    # Header = everything up to and including 'loop_'
    header = all_lines[:loop_idx + 1]

    # Parse column names (lines starting with '_rln' after loop_)
    column_names = []
    data_start_idx = loop_idx + 1
    for i in range(loop_idx + 1, len(all_lines)):
        stripped = all_lines[i].strip()
        if stripped.startswith('_'):
            column_names.append(stripped.split()[0])
            data_start_idx = i + 1
        elif stripped and not stripped.startswith('#'):
            data_start_idx = i
            break

    # Read data lines
    data_lines = [
        line.strip() for line in all_lines[data_start_idx:]
        if line.strip() and not line.strip().startswith('#')
    ]

    data = [line.split() for line in data_lines]
    df = pd.DataFrame(data, columns=column_names)

    return header, df


def write_star(file_path, header, df):
    """
    Writes a STAR file by first writing the header lines, then the column
    definitions, then the DataFrame rows.

    Args:
        file_path: output file path
        header: list of strings returned by read_star (up to and including 'loop_')
        df: DataFrame whose column names are the STAR column labels
    """
    with open(file_path, 'w') as f:
        for line in header:
            f.write(line if line.endswith('\n') else line + '\n')
        for i, col in enumerate(df.columns, start=1):
            f.write(f"{col} #{i}\n")
        f.write('\n')
        df.to_csv(f, sep=' ', index=False, header=False, na_rep='0')

## -------------------------------------------------------------------- 
def write_em_via_mrc(tmp_mrc: str, out_em: str):
    """Call EMAN2 to convert an MRC volume to EM."""
    subprocess.run(['e2proc3d.py', '--mult=-1', tmp_mrc, out_em], check=True, stdout=subprocess.DEVNULL)
