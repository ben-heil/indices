"""This script runs a user-selected metric on a citation graph and saves the result"""

import argparse
import os
import pickle

import networkx as nx

import algos

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('graph_file',
                        help='The file containing the pickled graph for a MeSH heading')
    parser.add_argument('metric',
                        help='The metric to calculate for the graph',
                        choices=['betweenness_centrality', 'pagerank', 'disruption_idx'],
                        type=str.lower)
    parser.add_argument('out_dir',
                        help='The dictory to store the results to')
    args = parser.parse_args()

    # Load graph
    with open(args.graph_file, 'rb') as in_file:
        graph = pickle.load(in_file)

    # Run metric on graph
    if args.metric == 'betweenness_centrality':
        node_to_metric = nx.betweenness_centrality(graph, k=100)
    elif args.metric == 'pagerank':
        node_to_metric = nx.pagerank(graph)
    elif args.metric == 'disruption_idx':
        node_to_metric = algos.all_nodes_disruption_index(graph)

    # Build path to save the results to
    in_file_name = os.path.basename(args.graph_file)
    in_file_base = os.path.splitext(in_file_name)[0]
    file_description = f'-{args.metric}.pkl'
    out_file_path = os.path.join(args.out_dir, in_file_base + file_description)

    with open(out_file_path, 'wb') as out_file:
        pickle.dump(node_to_metric, out_file)