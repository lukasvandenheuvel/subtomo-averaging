## !/usr/bin/env python3
# make particles.tbl from warp star file and reconstructed .mrc file
# ------------------------------------------------------------------

import os, subprocess, numpy as np, pandas as pd, mrcfile, argparse, re
from multiprocessing import Pool, cpu_count

def bandpass_filter(vol, pixel_size, low_f, high_f):
    """
    Apply an ideal 3D band-pass filter to `vol`.
    - vol: 3D numpy array
    - pixel_size: in Å
    - low_f: minimum frequency (1/Å)
    - high_f: maximum frequency (1/Å)
    """
    dims = vol.shape
    # build frequency axes for each dimension
    freq_axes = [np.fft.fftfreq(n, d=ps) for n, ps in zip(dims, [pixel_size]*3)]
    fx, fy, fz = np.meshgrid(*freq_axes, indexing='ij')
    radius = np.sqrt(fx**2 + fy**2 + fz**2)

    # ideal band-pass mask
    mask = (radius >= low_f) & (radius <= high_f)

    # forward FFT, apply mask, inverse FFT
    vol_fft = np.fft.fftn(vol)
    vol_fft *= mask
    filtered = np.fft.ifftn(vol_fft)

    return np.real(filtered)

# ------------ helpers --------------------------------------------------------
def write_em_via_mrc(tmp_mrc: str, out_em: str):
    """Call EMAN2 to convert an MRC volume to EM."""
    subprocess.run(['e2proc3d.py', '--mult=-1', tmp_mrc, out_em], check=True, stdout=subprocess.DEVNULL)

def read_star(file_path):
    """
    Reads a STAR file, automatically detecting column headers and data rows.
    Returns a DataFrame with proper column names from the STAR file.
    """
    with open(file_path, 'r') as f:
        all_lines = f.readlines()
    
    # Find the column definitions (lines starting with _rln)
    column_names = []
    data_start_idx = 0
    
    for i, line in enumerate(all_lines):
        stripped = line.strip()
        if stripped.startswith('_rln'):
            # Extract column name (e.g., "_rlnImageName #1" -> "_rlnImageName")
            col_name = stripped.split()[0]
            column_names.append(col_name)
        elif stripped and not stripped.startswith('#') and column_names:
            # First data line after column definitions
            data_start_idx = i
            break
    
    # Read data lines
    data_lines = all_lines[data_start_idx:]
    data_lines = [line.strip() for line in data_lines if line.strip() and not line.startswith('#')]
    
    # Create DataFrame with column names
    data = [line.split() for line in data_lines]
    df = pd.DataFrame(data, columns=column_names)
    
    return df

# ------------ configuration --------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='CTF correction for subtomogram averaging',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-r', '--root_path', required=True,
                        help='Root path containing the data')
    parser.add_argument('-s', '--star_file', required=True,
                        help='Input STAR file (warp file)')
    parser.add_argument('-t', '--tbl_file', required=True,
                        help='Input table file (.tbl)')
    parser.add_argument('-o', '--output_folder', required=True,
                        help='Output folder for processed particles')
    parser.add_argument('--no_ctf_correction', action='store_true',
                        help='Disable CTF correction (enabled by default)')
    parser.add_argument('--bpf', nargs=2, type=float, default=[1/500, 1/2],
                        metavar=('LOW', 'HIGH'),
                        help='Band-pass filter frequencies (1/Å): LOW HIGH')
    parser.add_argument('--ctf_method', choices=['phase_flip', 'wiener'], default='wiener',
                        help='CTF correction method')
    parser.add_argument('--wiener_epsilon', type=float, default=0.1,
                        help='Wiener filter epsilon parameter')
    parser.add_argument('--nproc', type=int, default=None,
                        help='Number of processes (default: all CPUs, max 52)')
    return parser.parse_args()

# ------------ worker ---------------------------------------------------------
def convert_particle(task):
    global root_path, outputfolder, do_ctf_correction, ctf_correction_method, wiener_epsilon, pixel_size, low_f, high_f
    """Run on a single particle (execution happens in forked worker)."""
    i, mrc_name, ctf_name, particle_num = task
    in_mrc  = os.path.join(root_path, mrc_name)
    in_ctf  = os.path.join(root_path, ctf_name)
    out_em  = os.path.join(outputfolder, f'particle_{particle_num:06d}.em')
    out_ctf = os.path.join(outputfolder, f'pfmask_{particle_num:06d}.em')

    if do_ctf_correction == 1:
        with mrcfile.open(in_mrc, permissive=True) as m:
            subtomo = m.data.astype(np.float32)
        dim = subtomo.shape
        with mrcfile.open(in_ctf, permissive=True) as m:
            ctf_vol = m.data.astype(np.float32)
        
        expected_dim = (dim[0], dim[1], dim[2]//2+1)
        
        if ctf_vol.shape == expected_dim:  # half-spectrum
            subtomo_fft = np.fft.rfftn(subtomo)
            
            if ctf_correction_method == 'phase_flip':
                ctf_filter = np.sign(ctf_vol)
            elif ctf_correction_method == 'wiener':
                ctf_filter = ctf_vol / (ctf_vol**2 + wiener_epsilon)
            else:
                raise ValueError(f"Unknown method: {ctf_correction_method}")
            
            corrected = np.fft.irfftn(subtomo_fft * ctf_filter, s=dim)
            
        else:  # full-spectrum
            subtomo_fft = np.fft.fftn(subtomo)
            
            if ctf_correction_method == 'phase_flip':
                ctf_filter = np.sign(ctf_vol)
            elif ctf_correction_method == 'wiener':
                ctf_filter = ctf_vol / (ctf_vol**2 + wiener_epsilon)
            else:
                raise ValueError(f"Unknown method: {ctf_correction_method}")
            
            corrected = np.real(np.fft.ifftn(subtomo_fft * ctf_filter))
    
            
        corrected = bandpass_filter(corrected, pixel_size, low_f, high_f)         
        tmp_mrc = os.path.join(outputfolder, f'_tmp_{particle_num:06d}.mrc')
        with mrcfile.new(tmp_mrc, overwrite=True) as m:
            m.set_data(corrected.astype(np.float32))
    
        write_em_via_mrc(tmp_mrc, out_em)
        os.remove(tmp_mrc)
            
    elif do_ctf_correction == 0:
        write_em_via_mrc(in_mrc, out_em)
    
    return particle_num                              # for progress reporting

# ------------ main driver ----------------------------------------------------
if __name__ == '__main__':
    args = parse_arguments()
    
    root_path       = args.root_path
    warp_file       = os.path.join(root_path, args.star_file)
    tbl_file        = os.path.join(root_path, args.tbl_file)
    outputfolder    = os.path.join(root_path, args.output_folder)
    do_ctf_correction = not args.no_ctf_correction
    low_f, high_f = args.bpf
    ctf_correction_method = args.ctf_method
    wiener_epsilon = args.wiener_epsilon
    
    os.makedirs(outputfolder, exist_ok=True)

    # ------------ pre-processing (single-thread) --------------------------------- might change!!
    print(f'Reading STAR file: {warp_file}')
    warp_df = read_star(warp_file)
    
    # Read pixel size from star file
    pixel_size = float(warp_df['_rlnPixelSize'].iloc[0])
    print(f'Pixel size from STAR file: {pixel_size} Å')
    print(f'CTF correction: {"enabled" if do_ctf_correction else "disabled"}')
    if do_ctf_correction:
        print(f'CTF correction method: {ctf_correction_method}')
    print(f'Band-pass filter: {low_f:.6f} - {high_f:.6f} (1/Å)')
    
    # Extract particle numbers from _rlnImageName
    # Example: bin8_3d/subtomo/Position_91_3/Position_91_3_0000013_15.84A.mrc -> 13
    def extract_particle_number(image_name):
        # Match pattern like Position_91_3_0000013_15.84A.mrc
        match = re.search(r'_(\d+)_[\d.]+A\.mrc$', image_name)
        if match:
            return int(match.group(1))
        # Fallback: try to find any sequence of digits before .mrc
        match = re.search(r'_(\d+)[^/]*\.mrc$', image_name)
        if match:
            return int(match.group(1))
        raise ValueError(f"Could not extract particle number from: {image_name}")
    
    warp_df['relion_particlenumber'] = warp_df['_rlnImageName'].apply(extract_particle_number)
    
    print(f'Reading table file: {tbl_file}')
    par_table = np.loadtxt(tbl_file, comments='#', dtype=float)
    par_table = par_table[np.argsort(par_table[:, 0])]
    particle_mask_idx = par_table[:, 0].astype(int) - 1          # zero-based
    
    mrc_particle_list = warp_df.loc[particle_mask_idx, '_rlnImageName'].values
    ctf_list          = warp_df.loc[particle_mask_idx, '_rlnCtfImage'].values
    
    tasks = [(idx, mrc, ctf, int(par_table[idx, 0])) for idx, (mrc, ctf) in enumerate(zip(mrc_particle_list, ctf_list))]

# ------------ parallel driver -----------------------------------------------
    if args.nproc is not None:
        nproc = min(args.nproc, cpu_count())
    else:
        nproc = min(cpu_count(), 52)          # cap if you want; else cpu_count()
    print(f'Launching {nproc} workers for {len(tasks):,} particles…')

    with Pool(processes=nproc) as pool:
        for done_idx in pool.imap_unordered(convert_particle, tasks, chunksize=64):
            if done_idx % 100 == 0:       # lightweight progress ping
                print(f'  finished particle {done_idx}')

    print('ALL DONE.')