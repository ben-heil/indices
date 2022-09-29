#!/bin/bash
#SBATCH --job-name pagerank_coord
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=8G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/combined_network_pagerank-%j.out

DATADIR='/scratch/summit/benheil@xsede.org/indices/data/combined_networks/'

FILES=`find $DATADIR | grep '[a-z_]*-[a-z_]*.pkl'`

echo $FILES | xargs -n 100 sbatch run_calculate_pr.sbatch 
