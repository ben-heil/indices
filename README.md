# PageRank by Field
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7458535.svg)](https://doi.org/10.5281/zenodo.7458535)

This repo contains code and data to reproduce the results of the manuscript "The field-dependent nature of PageRank values in citation networks".
In short, we devise a method to compare PageRanks for papers shared between fields and determine that there is field-specific interest in some papers.

![field comparison figure](https://raw.githubusercontent.com/greenelab/indices/main/figures/percentile_figure.png)

## Installation
The Python dependencies for this project are managed via [Conda](https://docs.conda.io/en/latest/miniconda.html).
To install them and activate the environment, use the following commands in bash:

``` bash
conda env create --file environment.yml
conda activate indices 
```

## Running the pipeline
The pipeline we used to run our analyses is best suited for running in a cluster environment, because it generates multiple terabytes of intermediate outputs and runs tens of thousands of easily paralellizable processes.
For an example of how to run the analysis portion of the pipeline on a Slurm cluster, see the `cluster_pipeline/` directory.
There is also a Snakemake file in the main directory titled `Snakefile`.
We don't recommend using it as it doesn't contain all the steps of the pipeline (and it takes half an hour to build the DAG), but we left it in to give usage examples for some of the scripts.

The order in which to run the scripts, and a brief description of what the scripts do, can be found below:

|Script|Description|
|--------|-----------|
|download_mesh_tree.sh|Download the structure of the MeSH vocabulary for further processing|
|src/get_mesh_headings.py|Extract the headings that define our fields|
|download_article_metadata.py|Download article metadata for the relevant headings (note, using an NCBI API key will make the download process faster, see https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/)|
|download_citations.sh|Download citation data from COCI version 14|
|src/build_single_heading_networks.py|Build networks corresponding to citations between two articles in a single heading|
|src/build_pairwise_networks.py|Build networks corresponding to citations between two articles within all pairs of headings|
|src/shuffle_graph.py|Generate shuffled graphs for all pairwise networks|
|src/split_combined_networks.py|Split the pairwise networks into their constituent fields (run this for both shuffled and true pairwise networks)|
|src/run_metric_on_graph.py|Calculate the PageRanks for articles within the resulting networks (run this for both shuffled and true split networks)|
|src/store_percentile_dataframes.py|Condense the results into a format more easily stored on a desktop computer and compatible with the visualization notebook|
|notebooks/figures.ipynb|Visualize results and generate figures for publication|

## Results
The dataframes produced by our analysis pipeline can be downloaded from https://zenodo.org/record/7458535 (DOI 10.5281/zenodo.7458535)
