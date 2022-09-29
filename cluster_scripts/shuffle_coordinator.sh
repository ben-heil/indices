#!/bin/bash
#SBATCH --job-name shuffle_coordinator
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=4G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/shuffle_combined_coordinator-%j.out

DATADIR='/scratch/summit/benheil@xsede.org/indices/data/combined_networks/'

FILES=`find $DATADIR | grep '[a-z_]*+[a-z_]*.pkl'`
echo $FILES
echo $FILES | xargs -P 0 -n 1 sbatch -W run_shuffle.sbatch 
wait
