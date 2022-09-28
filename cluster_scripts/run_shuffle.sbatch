#!/bin/bash
# Run the shuffle script to shuffle combined networks

#SBATCH --job-name shuffle_network
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=32G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/shuffle_combined-%j.out

module purge
eval "$(conda shell.bash hook)"

conda activate indices

# TODO conda env
if [ "$#" -eq 0 ] 
then
    echo "At least one argument required, $# provided"
    exit 1
fi

echo $1

python indices/shuffle_graph.py --out_dir '/scratch/summit/benheil@xsede.org/indices/data/shuffled_combined_networks' $1

