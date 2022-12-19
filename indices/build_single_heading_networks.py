import argparse
import os
import pickle

from utils import build_graphs, parse_mesh_headings


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_dir",
        help="The directory containing coci citations",
        default="data/coci",
    )
    parser.add_argument(
        "--metadata_dir",
        help="File from download_article_metadata containing info on the "
        "articles to add to the network",
        default="data/pubmed/efetch",
    )
    parser.add_argument(
        "--out_dir",
        help="The location to save the resulting netoworks to",
        default="data/networks",
    )
    parser.add_argument(
        "--include_first_degree",
        help="Include the citations where only one of the two articles belong "
        "to the MeSH heading ",
        action="store_true",
    )
    args = parser.parse_args()

    print("Initializing graphs...")

    heading_to_dois = parse_mesh_headings(args.metadata_dir)

    print("Building graphs...")
    heading_to_graph = build_graphs(
        args.data_dir, heading_to_dois, args.include_first_degree
    )

    for heading in heading_to_graph.keys():
        graph = heading_to_graph[heading]
        if args.include_first_degree:
            heading += "-first_degree"
        out_file_path = os.path.join(args.out_dir, heading + ".pkl")
        with open(out_file_path, "wb") as out_file:
            pickle.dump(graph, out_file)
