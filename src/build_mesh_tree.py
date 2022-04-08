import argparse
import os
import pickle
from typing import List

import pandas as pd
import tqdm
from pubmedpy.eutilities import esearch_query

ARTICLE_THRESHOLD = 30000
CACHE_FILE = 'heading.tmp'

class Node():
    def __init__(self, heading: str, id: str):
        self.heading = heading
        self.id = id
        self.children = []

    def add_child(self, child: "Node"):
        self.children.append(child)


def persist_to_file(file_name):
    # https://stackoverflow.com/questions/16463582/memoize-to-disk-python-persistent-memoization
    def decorator(original_func):
        try:
            cache = pickle.load(open(file_name, 'rb'))
        except (IOError, ValueError):
            cache = {}

        def new_func(param):
            if param not in cache:
                cache[param] = original_func(param)
                pickle.dump(cache, open(file_name, 'wb'))
            return cache[param]

        return new_func
    return decorator


def make_path_safe(path: str) -> str:
    # https://stackoverflow.com/questions/7406102/create-sane-safe-filename-from-any-unsafe-string
    return "".join([c for c in path if c.isalpha() or c.isdigit() or c==' ']).rstrip()


@persist_to_file(CACHE_FILE)
def get_heading_article_count(heading: str) -> pd.DataFrame:
    """
    Return the number of unique dois that fall under the given MeSH heading

    Arguments
    ---------
    heading: The MeSH heading to examine

    Returns
    -------
    count: The number or dois for the heading

    Note:
    This function is based on code from Le et al., and used in accordance with their license:
    https://github.com/greenelab/iscb-diversity/blob/master/02.process-pubmed.ipynb
    """
    payload = {
        'db': 'pubmed',
        'term': f'"journal article"[pt] AND "{heading}"[MeSH Terms] AND English[Language]',
    }

    pubmed_ids = esearch_query(payload)
    return len(pubmed_ids)


def get_headings(current_node: Node) -> List[str]:
    children = current_node.children
    print(current_node.heading)
    article_count = get_heading_article_count(current_node.heading)

    # If the current heading has less than the threshold amount, we filter out both it
    # and its children
    if article_count < ARTICLE_THRESHOLD:
        return [None]

    if len(children) == 0:
        # Either return heading if X citations or None otherwise
        if article_count >= ARTICLE_THRESHOLD:
            return [current_node.heading]
        else:
            return [None]
    else:
        child_headings = []
        for child in children:
            heading = get_headings(child)
            child_headings.extend(heading)
        child_headings = [h for h in child_headings if h is not None]

        # If there are sufficiently sized children, return only them to avoid double counting
        if len(child_headings) > 0:
            return child_headings
        # If this is the smallest node in the subtree that meets the cutoff, return this
        else:
            return [current_node.heading]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mesh_file', help='File containing mesh descriptors in ascii format')
    parser.add_argument('out_file', help='Location to store the headings to use')
    args = parser.parse_args()

    descriptors_by_depth = {}

    with open(args.mesh_file) as in_file:

        heading = None
        ids = None
        for line in in_file:
            line = line.strip()
            if 'NEWRECORD' in line:
                if ids is not None:
                    for id in ids:
                        depth = len(id.split('.'))

                        if depth in descriptors_by_depth:
                            descriptors_by_depth[depth].append((heading, id))
                        else:
                            descriptors_by_depth[depth] = [(heading, id)]

                heading = None
                ids = None
            elif 'MH = ' in line:
                heading = line.split('=')[-1].strip()
            elif 'MN = ' in line:
                # Headings are unique, but their location in the tree may not be

                id = line.split('=')[-1].strip()
                if ids is None:
                    ids = [id]
                else:
                    ids.append(id)

    ids = []
    for heading, id in descriptors_by_depth[1]:
        ids.append(id)

    depths = sorted(descriptors_by_depth.keys())

    id_to_node = {}
    trees = []
    headings_seen = set()

    for depth in depths:
        for heading, id in descriptors_by_depth[depth]:
            if heading in headings_seen:
                continue

            current_node = Node(heading, id)

            parent = id.rsplit('.', 1)[0]
            if parent not in id_to_node:
                if depth == 1:
                    trees.append(current_node)
                # Skip orphan nodes, but allow their heading to show up elsewhere
                else:
                    continue
            else:
                id_to_node[parent].add_child(current_node)

            id_to_node[id] = current_node
            headings_seen.add(heading)

    filtered_headings = []
    for root in tqdm.tqdm(trees):
        filtered_headings.extend(get_headings(root))
        print(filtered_headings)

    with open(args.out_file, 'wb') as out_file:
        pickle.dump(filtered_headings, out_file)

    os.remove(CACHE_FILE)

    # TODO store results