import collections
from functools import lru_cache
import glob
import os
import pickle as pkl
from typing import List, Dict, Union, Tuple, Set

import lxml.etree
import networkx as nx
import numpy as np
import pandas as pd
from pubmedpy.efetch import extract_identifiers
from pubmedpy.xml import iter_extract_elems
from tqdm import tqdm


def extract_all(elem: lxml.etree._Element) -> dict:
    """
    Extract a dictionary of all supported fields from a <PubmedArticle> XML element

    Note
    ----
    This code is from pubmedpy, modified to omit the authors, nlm_ids, and publication dates
    to save memory and decrease runtime
    https://github.com/dhimmel/pubmedpy/blob/main/pubmedpy/efetch.py
    """
    result = collections.OrderedDict()
    result.update(extract_identifiers(elem))
    result["journal"] = elem.findtext("MedlineCitation/MedlineJournalInfo/MedlineTA")
    result["title"] = elem.findtext("MedlineCitation/Article/ArticleTitle")
    return result


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
    pickle_path = base_name + ".pkl"

    # For speed, load the pickled version if it's available
    if os.path.exists(pickle_path):
        with open(pickle_path, "rb") as in_file:
            article_df = pkl.load(in_file)
    else:
        articles = []
        # generator of XML PubmedArticle elements
        article_elems = iter_extract_elems(file_path, tag="PubmedArticle")

        seen_pmids = set()
        i = 0
        for elem in tqdm(article_elems):
            # Example efetch XML for <PubmedArticle> at https://github.com/dhimmel/pubmedpy/blob/f554a06e13e24d661dc5ff93ad07179fb3d7f0af/pubmedpy/data/efetch.xml
            result = extract_all(elem)

            try:
                assert result["doi"] not in seen_pmids
            except AssertionError:
                print({result["doi"]}, " already in set iteration ", i)

            seen_pmids.add(result["pmid"])

            articles.append(result)
            i += 1

        article_df = pd.DataFrame(articles)

        with open(pickle_path, "wb") as out_file:
            pkl.dump(article_df, out_file)

    return article_df


def build_graphs(
    coci_dir: str,
    heading_to_dois: Dict[str, List[str]],
    include_first_degree: bool = False,
) -> Dict[str, nx.DiGraph]:
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
    heading_to_graph: A mapping between MeSH terms and their corresponding graphs

    """
    heading_to_graph = {heading: nx.DiGraph() for heading in heading_to_dois.keys()}

    for file_path in tqdm(glob.glob(f"{coci_dir}/*")):
        citation_list = pd.read_csv(file_path)
        for heading, dois in heading_to_dois.items():
            for citing, cited in zip(citation_list["citing"], citation_list["cited"]):
                if citing is None or cited is None:
                    continue
                if len(citing) == 0 or len(cited) == 0:
                    continue
                if include_first_degree:
                    if citing in dois or cited in dois:
                        heading_to_graph[heading].add_edge(citing, cited)
                else:
                    if citing in dois and cited in dois:
                        heading_to_graph[heading].add_edge(citing, cited)

    return heading_to_graph


def parse_mesh_headings(
    metadata_dir: str, filter_headings: Union[set, None] = None
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
    metadata_files = glob.glob(f"{metadata_dir}/*.xz")

    headings = []
    heading_to_dois = {}
    for metadata_path in tqdm(metadata_files):
        print(metadata_path)
        heading = os.path.basename(metadata_path)
        heading = heading.split(".")[0]
        if filter_headings is not None and heading not in filter_headings:
            continue
        headings.append(heading)

        article_df = parse_metadata(metadata_path)
        dois = set(article_df["doi"])
        heading_to_dois[heading] = dois

    return heading_to_dois


def calculate_percentiles(true_vals, doi_to_shuffled_metrics):
    dois, pageranks = [], []
    for doi, pagerank in true_vals.items():
        if pagerank is not None:
            dois.append(doi)
            pageranks.append(pagerank)

    percentiles = []
    for doi in dois:
        if doi not in doi_to_shuffled_metrics:
            percentiles.append(None)
            continue

        shuffled_metrics = doi_to_shuffled_metrics[doi]
        # If the node is unshuffleable for some reason, its percentile isn't meaningful
        if len(set(shuffled_metrics)) == 1:
            percentiles.append(None)
            continue
        true_val = true_vals[doi]

        percentile = np.searchsorted(shuffled_metrics, true_val) / 100
        percentiles.append(percentile)

    result_df = pd.DataFrame(
        {"doi": dois, "pagerank": pageranks, "percentile": percentiles}
    )
    return result_df


@lru_cache(2)
def load_single_heading(heading_str, base_dir="output"):
    heading_shuffled = glob.glob(
        f"{base_dir}/shuffle_results/{heading_str}*-pagerank.pkl"
    )

    doi_to_shuffled_metrics = {}

    for path in heading_shuffled:
        with open(path, "rb") as in_file:
            result = pkl.load(in_file)
            for doi, value in result.items():
                if doi in doi_to_shuffled_metrics:
                    doi_to_shuffled_metrics[doi].append(value)
                else:
                    doi_to_shuffled_metrics[doi] = [value]
    for doi, vals in doi_to_shuffled_metrics.items():
        doi_to_shuffled_metrics[doi] = sorted(vals)

    with open(f"{base_dir}/{heading_str}-pagerank.pkl", "rb") as in_file:
        true_vals = pkl.load(in_file)

    heading_df = calculate_percentiles(true_vals, doi_to_shuffled_metrics)
    return heading_df


def load_pair_headings(heading1, heading2, base_dir="output"):
    heading1_df = load_single_heading(f"{heading1}-{heading2}", base_dir)
    heading2_df = load_single_heading(f"{heading2}-{heading1}", base_dir)

    merged_df = heading1_df.merge(heading2_df, on="doi")
    merged_df = merged_df.rename(
        {
            "pagerank_x": f"{heading1}_pagerank",
            "pagerank_y": f"{heading2}_pagerank",
            "percentile_x": f"{heading1}_percentile",
            "percentile_y": f"{heading2}_percentile",
        },
        axis="columns",
    )
    merged_df[f"{heading1}-{heading2}"] = (
        merged_df[f"{heading1}_percentile"] - merged_df[f"{heading2}_percentile"]
    )
    merged_df[f"{heading2}-{heading1}"] = (
        merged_df[f"{heading2}_percentile"] - merged_df[f"{heading1}_percentile"]
    )

    metadata_df = parse_metadata(f"data/pubmed/efetch/{heading1}.xml.xz")
    full_df = merged_df.merge(metadata_df, on="doi")

    return full_df


def load_text(file_path: str) -> str:
    """A convenience function for reading in the markdown files used for the site's text"""
    with open(file_path) as in_file:
        return in_file.read()


def extract_heading_name(file_path: str) -> Tuple[str, str]:
    """
    Parse heading names from a file path
    """
    file_base = os.path.basename(file_path)
    both_headings = os.path.splitext(file_base)[0]
    heading1, heading2 = both_headings.split("-")

    return heading1, heading2


def get_heading_names(base_dir="viz_dataframes") -> List[str]:
    """
    Retrieve the names of all MeSH terms we have dataframes for
    """
    result_files = glob.glob(f"{base_dir}/percentiles/*.pkl")

    headings = set()
    for file in result_files:
        heading1, heading2 = extract_heading_name(file)
        headings.add(heading1)
        headings.add(heading2)

    return list(headings)


def get_journal_names(journal_data: pd.DataFrame) -> List[str]:
    """
    Get the names of the commonly used journals for the current pair
    """
    return list(journal_data["journal_title"])


def get_pair_names(heading: str, base_dir="viz_dataframes") -> List[str]:
    """
    Get the names of all headings that have been compared against the given heading
    """
    result_files = glob.glob(f"{base_dir}/percentiles/*{heading}*.pkl")

    pair_headings = set()

    for file in result_files:
        heading1, heading2 = extract_heading_name(file)
        if heading1 == heading:
            pair_headings.add(heading2)
        else:
            pair_headings.add(heading1)
    return list(pair_headings)


def load_percentile_data(
    heading1: str, heading2: str, base_dir="viz_dataframes"
) -> pd.DataFrame:
    """
    Load the dataframe containing papers' percentiles and pageranks
    """
    path = f"{base_dir}/percentiles/{heading1}-{heading2}.pkl"
    if os.path.exists(path):
        with open(path, "rb") as in_file:
            result_df = pkl.load(in_file)
    else:
        path = f"{base_dir}/percentiles/{heading2}-{heading1}.pkl"
        with open(path, "rb") as in_file:
            result_df = pkl.load(in_file)
    return result_df


def load_journal_data(
    heading1: str, heading2: str, base_dir="viz_dataframes"
) -> pd.DataFrame:
    """
    Load the dataframe containing information about journals across fields
    """
    path = f"{base_dir}/journals/{heading1}-{heading2}.pkl"
    if os.path.exists(path):
        with open(path, "rb") as in_file:
            result_df = pkl.load(in_file)
    else:
        path = f"{base_dir}/journals/{heading2}-{heading1}.pkl"
        with open(path, "rb") as in_file:
            result_df = pkl.load(in_file)
    return result_df
