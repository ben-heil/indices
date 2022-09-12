import argparse
import os
import pickle as pkl
import re

import networkx as nx


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('in_files',
                        help='The files to be split', nargs='+')
    parser.add_argument('--metadata_dir',
                        help='Files from download_article_metadata containing info on the '
                             'articles to add to the network',
                        default='data/pubmed/efetch')
    parser.add_argument('--original_network_dir',
                        help='The directory storing the base networks that the combined nets '
                             'are built from',
                        default='data/networks')
    parser.add_argument('--out_dir',
                        help='The location to save the resulting network to',
                        default='data/combined_networks')
    args = parser.parse_args()

    for file in args.in_files:
        file_base = os.path.basename(file)
        file_noext = os.path.splitext(file_base)[0]
        shuffle_number = None

        if shuffle_number is None:
            filename1 = f'{heading1}-{heading2}.pkl'
            filename2 = f'{heading2}-{heading1}.pkl'
        else:
            filename1 = f'{heading1}-{heading2}-{shuffle_number}.pkl'
            filename2 = f'{heading2}-{heading1}-{shuffle_number}.pkl'

        file1_out = os.path.join(args.out_dir, filename1)
        file2_out = os.path.join(args.out_dir, filename2)
        if os.path.exists(file1_out) and os.path.exists(file2_out):
            continue

        shuffle_regex = '-[0-9]+.pkl'
        if re.search(shuffle_regex, file_base):
            headings, shuffle_number = file_noext.split('-')
            heading1, heading2 = headings.split('+')
        else:
            heading1, heading2 = file_noext.split('+')

        heading1_network_file = os.path.join(args.original_network_dir, f'{heading1}.pkl')
        heading2_network_file = os.path.join(args.original_network_dir, f'{heading2}.pkl')

        with open(heading1_network_file, 'rb') as in_file:
            heading1_network = pkl.load(in_file)
        with open(heading2_network_file, 'rb') as in_file:
            heading2_network = pkl.load(in_file)

        with open(file, 'rb') as file_handle:
            pairwise_network = pkl.load(file_handle)

        heading1_network = pairwise_network.subgraph(heading1_network.nodes).copy()
        heading2_network = pairwise_network.subgraph(heading2_network.nodes).copy()

        # Remove nodes with no edges (i.e. citations)
        heading1_network.remove_nodes_from(list(nx.isolates(heading1_network)))
        heading2_network.remove_nodes_from(list(nx.isolates(heading2_network)))

        with open(file1_out, 'wb') as out_file:
            pkl.dump(heading1_network, out_file)
        with open(file2_out, 'wb') as out_file:
            pkl.dump(heading2_network, out_file)
