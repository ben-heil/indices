#!/bin/bash

#SBATCH --job-name condense_results
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=16G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/condense_results-%j.out

module purge
eval "$(conda shell.bash hook)"

conda activate indices

python indices/store_percentile_dataframes.py
