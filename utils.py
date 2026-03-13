import pandas as pd
import subprocess

def read_star(file_path):
    """
    Reads a STAR file (relion3/4/5 format).

    For files with a single data_ block (relion3/4), returns:
        header: list of strings (lines up to and including 'loop_')
        df: DataFrame with column names from the STAR file

    For files with multiple data_ blocks (relion5), returns:
        headers: list of N headers (each a list of strings)
        dfs: list of N DataFrames
    """
    with open(file_path, 'r') as f:
        all_lines = f.readlines()

    # Find all data_ block start indices
    data_indices = [i for i, line in enumerate(all_lines)
                    if line.strip().startswith('data_')]

    if not data_indices:
        raise ValueError(f"No 'data_' block found in {file_path}")

    headers = []
    dfs = []

    for block_num, data_idx in enumerate(data_indices):
        # Block spans from this data_ line to the next (or EOF)
        if block_num + 1 < len(data_indices):
            block_end = data_indices[block_num + 1]
        else:
            block_end = len(all_lines)

        block_lines = all_lines[data_idx:block_end]

        # Find loop_ within this block
        loop_offset = None
        for j, line in enumerate(block_lines):
            if line.strip() == 'loop_':
                loop_offset = j
                break

        if loop_offset is not None:
            # --- loop-style block ---
            if block_num == 0:
                header = all_lines[:data_idx] + block_lines[:loop_offset + 1]
            else:
                header = block_lines[:loop_offset + 1]

            column_names = []
            data_start = loop_offset + 1
            for j in range(loop_offset + 1, len(block_lines)):
                stripped = block_lines[j].strip()
                if stripped.startswith('_'):
                    column_names.append(stripped.split()[0])
                    data_start = j + 1
                elif stripped and not stripped.startswith('#'):
                    data_start = j
                    break

            data_lines = [
                line.strip() for line in block_lines[data_start:]
                if line.strip() and not line.strip().startswith('#')
            ]
            data = [line.split() for line in data_lines]
            df = pd.DataFrame(data, columns=column_names)
        else:
            # --- key-value block (no loop_) ---
            if block_num == 0:
                header = all_lines[:data_idx] + [block_lines[0]]
            else:
                header = [block_lines[0]]

            column_names = []
            values = []
            for line in block_lines[1:]:
                stripped = line.strip()
                if stripped.startswith('_'):
                    parts = stripped.split()
                    column_names.append(parts[0])
                    values.append(parts[1] if len(parts) > 1 else '')

            df = pd.DataFrame([values], columns=column_names) if column_names else pd.DataFrame()

        headers.append(header)
        dfs.append(df)

    # Single block: return header and df directly (backward compatible)
    if len(headers) == 1:
        return headers[0], dfs[0]

    return headers, dfs


def write_star(file_path, header, df):
    """
    Writes a STAR file by first writing the header lines, then the column
    definitions, then the DataFrame rows.

    Args:
        file_path: output file path
        header: list of strings or list of lists (for multi-block files)
        df: DataFrame or list of DataFrames (for multi-block files)
    """
    # Multi-block: header and df are both lists
    if isinstance(df, list):
        with open(file_path, 'w') as f:
            for h, d in zip(header, df):
                for line in h:
                    f.write(line if line.endswith('\n') else line + '\n')
                has_loop = any(l.strip() == 'loop_' for l in h)
                if has_loop:
                    for i, col in enumerate(d.columns, start=1):
                        f.write(f"{col} #{i}\n")
                    d.to_csv(f, sep=' ', index=False, header=False, na_rep='0')
                else:
                    for col in d.columns:
                        f.write(f"{col}\t{d[col].iloc[0]}\n")
                f.write('\n')
    else:
        with open(file_path, 'w') as f:
            for line in header:
                f.write(line if line.endswith('\n') else line + '\n')
            has_loop = any(l.strip() == 'loop_' for l in header)
            if has_loop:
                for i, col in enumerate(df.columns, start=1):
                    f.write(f"{col} #{i}\n")
                df.to_csv(f, sep=' ', index=False, header=False, na_rep='0')
            else:
                for col in df.columns:
                    f.write(f"{col}\t{df[col].iloc[0]}\n")

## -------------------------------------------------------------------- 
def write_em_via_mrc(tmp_mrc: str, out_em: str):
    """Call EMAN2 to convert an MRC volume to EM."""
    subprocess.run(['e2proc3d.py', '--mult=-1', tmp_mrc, out_em], check=True, stdout=subprocess.DEVNULL)
