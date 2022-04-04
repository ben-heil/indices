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
    base_name = file_path.split('.')[0]
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
            pickle.dump(article_df, out_file)

    return article_df


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
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
    args = parser.parse_args()

    print('Initializing graphs...')
    metadata_files = glob.glob(f'{args.metadata_dir}/*.xz')
    heading_to_graph = {}
    heading_to_dois = {}
    headings = []
    for metadata_path in metadata_files:
        heading = os.path.basename(metadata_path)
        heading = heading.split('.')[0]
        headings.append(heading)
        heading_to_graph[heading] = nx.DiGraph()

        article_df = parse_metadata(metadata_path)
        dois = set(article_df['doi'])
        heading_to_dois[heading] = dois

    print('Building graphs...')
    # For reasons that are unclear to me, this is faster than either inserting all
    # edges at once or constructing the graph in one shot
    for file_path in tqdm(glob.glob(f'{args.data_dir}/*')):
        citation_list = pd.read_csv(file_path)
        for heading in headings:
            heading_dois = heading_to_dois[heading]
            for citing, cited in zip(citation_list['citing'], citation_list['cited']):
                if citing in heading_dois and cited in heading_dois:
                    heading_to_graph[heading].add_edge(citing, cited)

    for heading in headings:
        out_file_path = os.path.join(args.out_dir, heading + '.pkl')
        with open(out_file_path, 'wb') as out_file:
            pickle.dump(heading_to_graph[heading], out_file)
