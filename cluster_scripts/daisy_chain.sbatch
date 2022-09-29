#!/bin/bash
#SBATCH --job-name daisychain
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=4G
#SBATCH -o /scratch/summit/benheil@xsede.org/logs/daisy-%j.out


sbatch run_all.sbatch

sleep 23h
sleep 50m

# Cancel all other processes
squeue -o"%.18i %.9P %.30j %.8u %.2t %.10M %.6D %R" | grep benh | grep -v daisychain | awk '{print $1}' | xargs -n 1 scancel

# Run self
sbatch daisy_chain.sbatch
