#!/bin/bash
#SBATCH --job-name run_all
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=4G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/run_all-%j.out

#sbatch -W pairwise_coordinator.sh
sbatch -W shuffle_coordinator.sh
sbatch -W shuffle_coordinator.sh
sbatch -W shuffle_coordinator.sh
sbatch -W split_combined_coordinator.sh
sbatch -W split_combined_shuffled_coordinator.sh
sbatch -W pagerank_coordinator.sh
sbatch -W shuffled_pagerank_coordinator.sh
sbatch -W condense_results_coordinator.sbatch


