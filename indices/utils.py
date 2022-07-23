import glob
import os
import pickle
from typing import List, Dict, Union

import networkx as nx
import pandas as pd
from pubmedpy.efetch import extract_all
from pubmedpy.xml import iter_extract_elems
from tqdm import tqdm

def parse_metadata(file_path: str) -> pd.DataFrame:
    """
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
    """
    # I have no idea why there isn't a better way to get rid of double extensions
    base_name = os.path.splitext(os.path.splitext(file_path)[0])[0]
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

def build_graphs(coci_dir: str,
                         heading_to_dois: Dict[str, List[str]],
                         include_first_degree: bool=False) -> Dict[str, nx.DiGraph]:
    """
    Build the citation graphs for all MeSH headings provided

    Arguments
    ---------
    coci_dir: A path to the directory containing xzipped citations from COCI
    heading_to_dois: A mapping between MeSH heading names and their corresponding dois
    include_first_degree: If True include citations where either paper belongs to the MeSH heading,
                          if False, include only citations where both papers belong to the heading

    Returns
    -------

    """
    heading_to_graph = {heading: nx.DiGraph() for heading in heading_to_dois.keys()}

    for file_path in tqdm(glob.glob(f'{coci_dir}/*')):
        citation_list = pd.read_csv(file_path)
        for heading, dois in heading_to_dois.items():
            for citing, cited in zip(citation_list['citing'], citation_list['cited']):
                if include_first_degree:
                    if citing in dois or cited in dois:
                        heading_to_graph[heading].add_edge(citing, cited)
                else:
                    if citing in dois and cited in dois:
                        heading_to_graph[heading].add_edge(citing, cited)

    return heading_to_graph

def parse_mesh_headings(metadata_dir: str,
                        filter_headings: Union[set, None]=None
                        ) -> Dict[str, List[str]]:
    """
    Read metadata from MeSH stoed in the given directory and use it to generate
    a mapping between dois and

    Arguments
    ---------
    metadata_dir: The directory storing the xzipped MeSH metadata
    filter_headings: Either a set containing the headings to keep, or None to indicate
                     that all headings should be returned

    Returns
    -------
    heading_to_dois: A dict mapping MeSH headings to the dois of publications that fall under them
    """
    metadata_files = glob.glob(f'{metadata_dir}/*.xz')
    headings = []
    heading_to_dois = {}
    for metadata_path in metadata_files:
        heading = os.path.basename(metadata_path)
        heading = heading.split('.')[0]
        if heading not in filter_headings and filter_headings is not None:
            continue
        headings.append(heading)

        article_df = parse_metadata(metadata_path)
        dois = set(article_df['doi'])
        heading_to_dois[heading] = dois

    return heading_to_dois