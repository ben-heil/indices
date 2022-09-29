#!/bin/bash
#SBATCH --job-name coord_build_network
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=4G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/build_network_coordinator-%j.out


for SPLIT in {0..15};
do
    sbatch -W run_build_pairwise.sh $SPLIT &
done
wait
