import argparse
import pickle
import os
from copy import deepcopy

import networkx as nx
from tqdm import tqdm


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('graph_paths', help='The paths to the graphs to shuffle', nargs='+')
    parser.add_argument('--out_dir', help='The directory to store shuffled graphs in', default='data/shuffled_combined_networks')
    parser.add_argument('--n_graphs', help='The number of shuffled graphs to create', default=100)
    args = parser.parse_args()

    graph_path = args.graph_paths
    for graph_path in args.graph_paths:
        file_base = os.path.basename(graph_path)
        file_base = os.path.splitext(file_base)[0]

        with open(graph_path, 'rb') as in_file:
            original_network = pickle.load(in_file)

        n_edges = len(original_network.edges)
        for i in tqdm(range(args.n_graphs)):
            out_file_name = f'{file_base}-{i}.pkl'
            out_file_path = os.path.join(args.out_dir, out_file_name)
            # Skip creating files that already exist
            if os.path.exists(out_file_path):
                continue

            graph_copy = deepcopy(original_network)
            # Directed edge swap swaps three edges at a time
            n_swap = n_edges * 2

            shuffled_graph = nx.directed_edge_swap(graph_copy,
                                                nswap=n_swap,
                                                max_tries=100*n_edges,
                                                seed=42*i)


            with open(out_file_path, 'wb') as out_path:
                pickle.dump(shuffled_graph, out_path)



