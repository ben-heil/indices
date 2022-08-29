import itertools

# HEADINGS = ["botany", "developmental_biology", "genetics","microbiology", "ecology",
#             # Informatics subheadings
#             "cheminformatics", "computational_biology", "consumer_health_informatics","medical_informatics",
#             # Algorithms subheadings
#             "artificial_intelligence", "latent_class_analysis",
#             ]

#HEADINGS = ["artificial_intelligence", "computational_biology", "ecology", "genetics",
#            "medical_informatics", "microbiology"]

HEADINGS = ["Anatomy", "Histocytochemistry", "Immunochemistry", "Molecular Biology",
            "Proteomics", "Metabolomics", "Human Genetics", "Genetics Population",
            "Genetic Research", "Food Microbiology", "Soil Microbiology", "Water Microbiology",
            "Computational Biology", "Biophysics", "Biotechnology", "Neurosciences",
            "Pharmacology", "Physiology", "Toxicology", "Chemistry Pharmaceutical",
            "Crystallography", "Electrochemistry", "Photochemistry", "Statistics as Topic",
            "Nonlinear Dynamics", "Acoustics", "Electronics", "Magnetics",
            "Nuclear Physics", "Rheology", "Fiber Optic Technology", "Microscopy",
            "Operations Research", "Research Design", "Health Services Research",
            "Nursing Evaluation Research", "Nursing Methodology Research",
            "Outcome Assessment Health Care", "Translational Research Biomedical",
            "Empirical Research", "Nanotechnology", "Microtechnology", "Ecology",
            "Geography", "Paleontology"]


# TODO use pickle file to read in headings
HEADINGS = [h.lower().replace(' ', '_') for h in HEADINGS]

#HEADINGS = ["artificial_intelligence", "computational_biology"]

COCI_DIR = '/mnt/SlowData/coci'

SPLIT_HEADINGS = [h1 + '-' + h2 for h1, h2 in itertools.combinations(sorted(HEADINGS), 2)]
SPLIT_HEADINGS2 = [h2 + '-' + h1 for h1, h2 in itertools.combinations(sorted(HEADINGS), 2)]

wildcard_constraints:
    # Random seeds should be numbers
    shuffle="\d+",
    # The headings wildcard used in shuffle_networks can contain letters, underscores,
    # and dashes, but no other characters such as numbers
    combined_heading="[a-z_]*\+[a-z_]*",
    heading="[a-z_]+",
    heading1="[a-z_-]+",
    heading2="[a-z_-]+",

rule all:
    input:
        expand("output/shuffle_results/{split_heading}-{shuffle}-pagerank.pkl",
                split_heading=SPLIT_HEADINGS, shuffle=list(range(100))),
        expand("output/shuffle_results/{split_heading}-{shuffle}-pagerank.pkl",
                split_heading=SPLIT_HEADINGS2, shuffle=list(range(100))),
        expand("output/{split_heading}-pagerank.pkl",
                split_heading=SPLIT_HEADINGS, shuffle=list(range(100))),
        expand("output/{split_heading}-pagerank.pkl",
                split_heading=SPLIT_HEADINGS2, shuffle=list(range(100))),
        expand("output/{heading}-pagerank.pkl",
                heading=HEADINGS)

rule download_citation_data:
    output:
        COCI_DIR
    shell:
        "bash download_citations.sh"

rule download_article_metadata:
    output:
        expand("data/pubmed/efetch/{heading}.xml.xz",
                heading=HEADINGS)
    shell:
        "python download_article_metadata.py {wildcards.heading} --overwrite "

# This assumes that data/coci actually has data in it, but I don't really
# want to specify file names since the dataset updates over time
rule build_single_heading_networks:
    input:
        COCI_DIR
    output:
        expand("data/networks/{heading}.pkl",
               heading=HEADINGS)
    shell:
        "python indices/build_single_heading_networks.py "
        "--data_dir " + COCI_DIR

rule build_pairwise_networks:
    threads:
        8
    input:
        COCI_DIR
    output:
        ["data/combined_networks/" + h1 + "+" + h2 + ".pkl" for h1, h2 in itertools.combinations(sorted(HEADINGS), 2)]
    shell:
        "python indices/build_pairwise_networks.py " + ' '.join(HEADINGS) + ' '
        " --data_dir " + COCI_DIR + " --out_dir data/combined_networks "

rule shuffle_combined_networks:
    input:
        "data/combined_networks/{combined_heading}.pkl"
    output:
        ["data/shuffled_combined_networks/{combined_heading}-"+ str(i) + ".pkl" for i in range(100)]

    shell:
        "python indices/shuffle_graph.py {input} data/shuffled_combined_networks "

rule split_combined_shuffled_networks:
    input:
        "data/shuffled_combined_networks/{heading1}+{heading2}-{shuffle}.pkl"
    output:
        "data/shuffled_combined_networks/{heading1}-{heading2}-{shuffle}.pkl",
        "data/shuffled_combined_networks/{heading2}-{heading1}-{shuffle}.pkl"
    shell:
        "python indices/split_pairwise_network.py {input} --out_dir data/shuffled_combined_networks"

rule split_combined_networks:
    input:
        "data/combined_networks/{heading1}+{heading2}.pkl"
    output:
        "data/combined_networks/{heading1}-{heading2}.pkl",
        "data/combined_networks/{heading2}-{heading1}.pkl"
    shell:
        "python indices/split_pairwise_network.py {input} --out_dir data/combined_networks"

rule calculate_combined_pagerank:
    input:
        "data/combined_networks/{heading1}-{heading2}.pkl"
    output:
        "output/{heading1}-{heading2}-pagerank.pkl"
    shell:
        "python indices/run_metric_on_graph.py {input} pagerank output"

rule calculate_combined_shuffled_pagerank:
    input:
        "data/shuffled_combined_networks/{heading1}-{heading2}-{shuffle}.pkl"
    output:
        "output/shuffle_results/{heading1}-{heading2}-{shuffle}-pagerank.pkl"
    shell:
        "python indices/run_metric_on_graph.py {input} pagerank output/shuffle_results"

rule calculate_pagerank:
    input:
        "data/networks/{heading}.pkl"
    output:
        "output/{heading}-pagerank.pkl"
    shell:
        "python indices/run_metric_on_graph.py {input} pagerank output"
