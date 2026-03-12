import argparse
import pandas as pd
from utils import read_star,write_star

def create_rlnHelicalTrackLengthAngst(helicaltubeid: pd.DataFrame, pick_distance: float) -> pd.DataFrame:
    """
    This function takes:
      - `helicaltubeid`: A pandas DataFrame that has a column 'HelicalTubeID' identifying each helical segment.
      - `pick_distance`: The interbox distance (in Å).

    It returns a new DataFrame containing, for each unique HelicalTubeID:
      - HelicalTubeID
      - StartDistance (always 0)
      - TotalDistance (in Å, computed as number_of_rows * pick_distance)
      - PickDistance (in Å, the same for all rows)

    Example:
        If tube_id 1 has 10 particles, and pick_distance=4.7Å,
        TotalDistance for tube_id=1 will be 10 * 4.7 = 47 Å.
    """
    df = helicaltubeid.copy()
    df = helicaltubeid.to_frame(name="HelicalTubeID")
    df['ParticleIndexWithinTube'] = df.groupby('HelicalTubeID').cumcount()
    df['DistanceFromStart'] = df['ParticleIndexWithinTube'] * pick_distance
    return df['DistanceFromStart']

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Merge columns from particles_warp.star into binned particles STAR file.'
    )
    
    parser.add_argument(
        '-i', '--input',
        required=True,
        dest='input',
        metavar='INPUT_STAR',
        help='Input starfile to which _rlnHelicalTrackLengthAngst should be appended'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        dest='output',
        metavar='OUTPUT_STAR',
        help='Output starfile'
    )
    parser.add_argument(
        '-d', '--distance',
        required=True,
        dest='distance',
        metavar='DISTANCE_ANGS',
        help='Distance (in angs) between 2 neigboring boxes (interbox distance) used to calculate _rlnHelicalTrackLengthAngst'
    )
    args = parser.parse_args()
    header,df = read_star(args.input)
    df['_rlnHelicalTrackLengthAngst'] = create_rlnHelicalTrackLengthAngst(df['_rlnHelicalTubeID'], float(args.distance))
    write_star(args.output,header,df)
    print(f"Updated STAR file with _rlnHelicalTrackLengthAngst written to {args.output}")