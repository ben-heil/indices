#!/bin/bash
#SBATCH --job-name split_combined_shuffled_coordinator
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=8G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/shuffle_combined-%j.out

DATADIR='/scratch/summit/benheil@xsede.org/indices/data/shuffled_combined_networks/'

FILES=`find $DATADIR | grep '+'`

echo $FILES | xargs -P 0 -n 50 sbatch -W run_split_combined_shuffled.sbatch
