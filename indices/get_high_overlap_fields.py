import argparse
import glob
import os
import pickle as pkl
import shutil

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('in_dir', help='The pagerank results to be filtered')
    parser.add_argument('out_dir', help='The location to store results with high overlap')
    parser.add_argument('overlap_threshold',
                        help='The minimum number of shared papers to include a field pair',
                        default=1000,
                        type=int)
    args = parser.parse_args()

    i = 0
    for path in glob.glob(os.path.join(args.in_dir, '*.pkl')):
        filename = os.path.basename(path)
        try:
            with open(path, 'rb') as in_file:
                df = pkl.load(in_file)
        except FileNotFoundError:
            continue

        if len(df) > OVERLAP_THRESHOLD:
            i += 1
            shutil.copyfile(path, os.path.join(args.out_dir, filename))

    print(f'{i} heading pairs have > {args.overlap_threshold} shared papers')