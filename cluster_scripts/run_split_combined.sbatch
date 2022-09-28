#!/bin/bash

#SBATCH --job-name split_combined_network
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=16G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/split_combined-%j.out

module purge
eval "$(conda shell.bash hook)"

conda activate indices

# TODO conda env
if [ "$#" -eq 0 ] 
then
    echo "At least one argument required, $# provided"
    exit 1
fi

echo "$@"

python indices/split_pairwise_network.py "$@" \
--out_dir '/scratch/summit/benheil@xsede.org/indices/data/combined_networks' \
--metadata_dir '/scratch/summit/benheil@xsede.org/indices/data/pubmed/eftech' \
--original_network_dir '/scratch/summit/benheil@xsede.org/indices/data/networks'
