import os
from glob import glob


in_dir = '/scratch/summit/benheil@xsede.org/indices/data/shuffled_combined_networks'

for first_file in glob(in_dir + '/*+*-1.pkl'):
    #print(first_file)

    file_name = os.path.basename(first_file)
    base = file_name.split('-')[0]

    file_group = glob(in_dir + '/' + base + '*')

    try:
        assert len(file_group) == 100
    except AssertionError:
        print(f'{file_name} is missing {100 - len(file_group)} files')
