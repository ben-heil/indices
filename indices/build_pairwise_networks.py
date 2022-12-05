import itertools
import pickle as pkl
import os

import argparse

from utils import build_graphs, parse_mesh_headings


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fragment', help='Which sixteenth of the headings to process', type=int)
    parser.add_argument('--data_dir',
                         help='The directory containing coci citations',
                         default='data/coci')
    parser.add_argument('--metadata_dir',
                        help='File from download_article_metadata containing info on the '
                             'articles to add to the network',
                        default='data/pubmed/efetch')
    parser.add_argument('--out_dir',
                        help='The location to save the resulting netoworks to',
                        default='data/networks')
    parser.add_argument('--include_first_degree',
                        help='Include the citations where only one of the two articles belong '
                             'to the MeSH heading ',
                        action='store_true')
    parser.add_argument('headings_to_process', nargs='+',
                        help='The MeSH headings to make pairwise networks from')

    args = parser.parse_args()

    headings = []
    for heading in args.headings_to_process:
        clean_heading = heading.replace(' ', '_')
        clean_heading = clean_heading.replace('-', '_')
        clean_heading = clean_heading.replace(',', '')
        clean_heading = clean_heading.lower()
        headings.append(clean_heading)

    if len(args.headings_to_process) < 2:
        parser.error('You must include at least two headings to build pairwise networks')

    headings_to_process = set(headings)
    heading_to_dois = parse_mesh_headings(args.metadata_dir, headings_to_process)

    heading_pairs = list(itertools.combinations(sorted(list(heading_to_dois.keys())), 2))
    start_idx = round(len(heading_pairs) * args.fragment / 16)
    end_idx = round(len(heading_pairs) * (args.fragment + 1) / 16)
    heading_pairs = heading_pairs[start_idx: end_idx]

    paired_headings = {}
    for heading1, heading2 in heading_pairs:
        first_dois = heading_to_dois[heading1]
        second_dois = heading_to_dois[heading2]
        combined_dois = first_dois.union(second_dois)

        out_file_path = os.path.join(args.out_dir, f'{heading1}+{heading2}' + '.pkl')

        # Don't need to track heading pairs that we've already built networks for
        if os.path.exists(out_file_path):
            continue

        paired_headings[f'{heading1}+{heading2}'] = combined_dois

    # This is a 20GB object so let's go ahead and deallocate the memory
    del(heading_to_dois)

    heading_to_graph = build_graphs(args.data_dir, paired_headings, args.include_first_degree)

    for heading in heading_to_graph.keys():
        graph = heading_to_graph[heading]
        if args.include_first_degree:
            heading += '-first_degree'
        out_file_path = os.path.join(args.out_dir, heading + '.pkl')
        with open(out_file_path, 'wb') as out_file:
            pkl.dump(graph, out_file)
