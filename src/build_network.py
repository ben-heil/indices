import argparse
import glob
import os
import pickle

import networkx as nx
import pandas as pd
from pubmedpy.efetch import extract_all
from pubmedpy.xml import iter_extract_elems
from tqdm import tqdm


def parse_metadata(file_path: str) -> pd.DataFrame:
    '''
    Convert the file containing information about a set of articles into a dataframe

    Parameters
    ----------
    file_path: The path to the file to load

    Returns
    -------
    article_df: The dataframe of information about the articles

    Note:
    This function is based on code from Le et al., and used in accordance with their license:
    https://github.com/greenelab/iscb-diversity/blob/master/02.process-pubmed.ipynb
    '''
    base_name = os.path.splitext(file_path)
    pickle_path = base_name + '.pkl'

    # For speed, load the pickled version if it's available
    if os.path.exists(pickle_path):
        with open(pickle_path, 'rb') as in_file:
            article_df = pickle.load(in_file)
    else:
        articles = []
        # generator of XML PubmedArticle elements
        article_elems = iter_extract_elems(file_path, tag='PubmedArticle')

        for elem in article_elems:
            # Example efetch XML for <PubmedArticle> at https://github.com/dhimmel/pubmedpy/blob/f554a06e13e24d661dc5ff93ad07179fb3d7f0af/pubmedpy/data/efetch.xml
            articles.append(extract_all(elem))

        article_df = pd.DataFrame(articles)

        with open(pickle_path, 'wb') as out_file:
            pickle.dump(out_file)

    return article_df


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir',
                         help='The directory containing coci citations',
                         default='data/coci')
    parser.add_argument('metadata_file',
                        help='File from download_article_metadata containing info on the '
                             'articles to add to the network')
    parser.add_argument('out_file',
                        help='The file to save the resulting netowrk to')
    args = parser.parse_args()

    print('Parsing metadata...')
    article_df = parse_metadata(args.metadata_file)

    print('Building graph...')
    # For reasons that are unclear to me, this is faster than either inserting all
    # edges at once or constructing the graph in one shot
    graph = nx.DiGraph()
    network_dois = set(article_df['doi'])
    for file_path in tqdm(glob.glob(f'{args.data_dir}/*')):
        citation_list = pd.read_csv(file_path)
        for citing, cited in zip(citation_list['citing'], citation_list['cited']):
            if citing in network_dois or cited in network_dois:
                graph.add_edge(citing, cited)

    with open(args.out_file, 'wb') as out_file:
        pickle.dump(graph, out_file)
