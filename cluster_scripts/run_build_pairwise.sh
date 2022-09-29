#!/bin/bash
# Run the build_pairwise_networks script across a sixteenth of the headings

#SBATCH --job-name build_pairwise_networks
#SBATCH -p shas
#SBATCH --time 24:00:00
#SBATCH --mem=100G

module purge
eval "$(conda shell.bash hook)"

conda activate indices

if [ ! "$#" -eq 1 ] 
then
    echo "1 argument required, $# provided"
    exit 1
fi

echo $1

python indices/build_pairwise_networks.py \
    --data_dir '/scratch/summit/benheil@xsede.org/indices/data/coci' \
    --metadata_dir '/scratch/summit/benheil@xsede.org/indices/data/pubmed/efetch' \
    --out_dir '/scratch/summit/benheil@xsede.org/indices/data/combined_networks' \
    $1 \
    "Anatomy" "Histocytochemistry" "Immunochemistry" "Molecular Biology" "Proteomics" \
    "Metabolomics" "Human Genetics" "Genetics Population"                             \
    "Genetic Research" "Food Microbiology" "Soil Microbiology" "Water Microbiology"   \
    "Computational Biology" "Biophysics" "Biotechnology" "Neurosciences"              \
    "Pharmacology" "Physiology" "Toxicology" "Chemistry Pharmaceutical"               \
    "Crystallography" "Electrochemistry" "Photochemistry" "Statistics as Topic"       \
    "Nonlinear Dynamics" "Acoustics" "Electronics" "Magnetics"                        \
    "Nuclear Physics" "Rheology" "Fiber Optic Technology" "Microscopy"                \
    "Operations Research" "Research Design" "Health Services Research"                \
    "Nursing Evaluation Research" "Nursing Methodology Research"                      \
    "Outcome Assessment Health Care" "Translational Research Biomedical"              \
    "Empirical Research" "Nanotechnology" "Microtechnology" "Ecology"                 \
    "Geography" "Paleontology"                                                        \
