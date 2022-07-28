import itertools

# Split combined shuffled networks (split_pairwise_networks.py)

HEADINGS = ["developmental_biology", "genetics","microbiology",
            # Informatics subheadings
            "cheminformatics", "computational_biology", "consumer_health_informatics",
            # Algorithms subheadings
            "artificial_intelligence",
            ]

COCI_DIR = '/mnt/SlowData/coci'

SPLIT_HEADINGS = [h1 + '-' + h2 for h1, h2 in itertools.combinations(HEADINGS, 2)]
SPLIT_HEADINGS2 = [h2 + '-' + h1 for h1, h2 in itertools.combinations(HEADINGS, 2)]

rule all:
    input:
        # expand("data/networks/{heading}.pkl", heading=HEADINGS),
        # expand("data/shuffled_networks/{heading}_{shuffle}.pkl",
        #        heading=HEADINGS
        #        shuffle=list(range(100))),
        expand("data/networks/{split_heading}_{shuffle}.pkl",
                split_heading=SPLIT_HEADINGS, shuffle=list(range(100))),
        expand("data/networks/{split_heading}_{shuffle}.pkl",
                split_heading=SPLIT_HEADINGS2, shuffle=list(range(100))),

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
    input:
        COCI_DIR
    output:
        "data/networks/{heading1}+{heading2}.pkl"
    shell:
        "python indices/build_pairwise_network.py {wildcards.heading1} {wildcards.heading2} "
        "--data_dir " + COCI_DIR

rule shuffle_networks:
    input:
        "data/networks/{heading}.pkl"
    output:
        "data/shuffled_networks/{heading}_{shuffle}.pkl"

    shell:
        "python indices/shuffle_graph.py {input} data/shuffled_networks"

rule split_combined_shuffled_networks:
    input:
        "data/shuffled_networks/{heading1}+{heading2}_{shuffle}.pkl"
    output:
        "data/networks/{heading1}-{heading2}_{shuffle}.pkl",
        "data/networks/{heading2}-{heading1}_{shuffle}.pkl"
    shell:
        "python indices/split_pairwise_network.py {input}"