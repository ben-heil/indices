#!/bin/bash
#SBATCH --job-name shuffled_pagerank_coordinator
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=8G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/shuffled_pr_coordinator-%j.out

DATADIR='/scratch/summit/benheil@xsede.org/indices/data/shuffled_combined_networks/'

FILES=`find $DATADIR | grep '[a-z_]*-[a-z_]*-[0-9]*.pkl'`

echo $FILES | xargs -P 0 -n 500 sbatch -W run_calculate_pr_shuffled.sbatch 
wait
