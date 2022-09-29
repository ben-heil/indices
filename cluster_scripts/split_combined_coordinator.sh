#!/bin/bash
#SBATCH --job-name split_combined_coord
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=8G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/split_combined_coordinator-%j.out

DATADIR='/scratch/summit/benheil@xsede.org/indices/data/combined_networks/'

FILES=`find $DATADIR | grep '+'`
echo $FILES

echo $FILES | xargs -P 0 -n 100 sbatch -W run_split_combined.sbatch 
wait
