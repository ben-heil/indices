"""
Condense the results of the pipeline into a form useable by the web app

This script was used in the cluster environment to condense the results
into something more easily stored/moved.
"""
import argparse
import glob
import os
import pickle as pkl
from functools import lru_cache
from itertools import combinations

import numpy as np
import pandas as pd
from tqdm import tqdm

DIR_ROOT = '/scratch/summit/benheil@xsede.org/indices'

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
            article_df = pkl.load(in_file)
    else:
        articles = []
        # generator of XML PubmedArticle elements
        article_elems = iter_extract_elems(file_path, tag='PubmedArticle')

        seen_pmids = set()
        i = 0
        for elem in tqdm(article_elems):
            # Example efetch XML for <PubmedArticle> at https://github.com/dhimmel/pubmedpy/blob/f554a06e13e24d661dc5ff93ad07179fb3d7f0af/pubmedpy/data/efetch.xml
            result = extract_all(elem)

            try:
                assert result['doi'] not in seen_pmids
            except AssertionError:
                print({result['doi']}, ' already in set iteration ', i)

            seen_pmids.add(result['pmid'])

            articles.append(result)
            i += 1

        article_df = pd.DataFrame(articles)

        with open(pickle_path, 'wb') as out_file:
            pkl.dump(article_df, out_file)

    return article_df

def calculate_percentiles(true_vals, doi_to_shuffled_metrics):
    dois, pageranks, counts = [], [], []
    for doi, pagerank in true_vals.items():
        if pagerank is not None:
            dois.append(doi)
            pageranks.append(pagerank)

    percentiles = []
    for doi in dois:
        if doi not in doi_to_shuffled_metrics:
            percentiles.append(None)
            counts.append(None)
            continue

        shuffled_metrics = doi_to_shuffled_metrics[doi]
        # If the node is unshuffleable for some reason, its percentile isn't meaningful
        if len(set(shuffled_metrics)) <= 1:
            percentiles.append(None)
            counts.append(len(shuffled_metrics)
            continue
        true_val = true_vals[doi]

        assert

        percentile = np.searchsorted(shuffled_metrics, true_val) / len(shuffled_metrics)
        percentiles.append(percentile)
        counts.append(len(shuffled_metrics))

    result_df = pd.DataFrame({'doi': dois, 'pagerank': pageranks, 'percentile': percentiles,
                              'count': counts})
    return result_df

@lru_cache(2)
def load_single_heading(heading_str):
    heading_shuffled = glob.glob(f'{DIR_ROOT}/output/shuffle_results/{heading_str}*-pagerank.pkl')

    doi_to_shuffled_metrics = {}

    for path in heading_shuffled:
        with open(path, 'rb') as in_file:
            result = pkl.load(in_file)
            for doi, value in result.items():
                if doi in doi_to_shuffled_metrics:
                    doi_to_shuffled_metrics[doi].append(value)
                else:
                    doi_to_shuffled_metrics[doi] = [value]
    for doi, vals in doi_to_shuffled_metrics.items():
        doi_to_shuffled_metrics[doi] = sorted(vals)

    with open(f'{DIR_ROOT}/output/{heading_str}-pagerank.pkl', 'rb') as in_file:
        true_vals = pkl.load(in_file)

    heading_df = calculate_percentiles(true_vals, doi_to_shuffled_metrics)
    return heading_df

def load_pair_headings(heading1, heading2):
    heading1_df = load_single_heading(f'{heading1}-{heading2}')
    heading2_df = load_single_heading(f'{heading2}-{heading1}')

    merged_df = heading1_df.merge(heading2_df, on='doi')
    merged_df = merged_df.rename({'pagerank_x': f'{heading1}_pagerank',
                                  'pagerank_y': f'{heading2}_pagerank',
                                  'percentile_x': f'{heading1}_percentile',
                                  'percentile_y': f'{heading2}_percentile',
                                  'count_x': f'{heading1}_count',
                                  'count_y': f'{heading2}_count',},
                                  axis='columns')
    merged_df[f'{heading1}-{heading2}'] = merged_df[f'{heading1}_percentile'] - merged_df[f'{heading2}_percentile']
    merged_df[f'{heading2}-{heading1}'] = merged_df[f'{heading2}_percentile'] - merged_df[f'{heading1}_percentile']

    metadata_df = parse_metadata(f'{DIR_ROOT}/data/pubmed/efetch/{heading1}.xml.xz')
    full_df = merged_df.merge(metadata_df, on='doi')

    return full_df

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--journal_size_cutoff', type=int, default=25,
                        help='The number of papers in a journal for it to be included'
                        )
    args = parser.parse_args()

    for path1, path2 in tqdm(list(combinations(glob.glob(f'{DIR_ROOT}/data/networks/*.pkl'), 2))):
        path1_file = os.path.basename(path1)
        heading1 = os.path.splitext(path1_file)[0]
        path2_file = os.path.basename(path2)
        heading2 = os.path.splitext(path2_file)[0]
        print(heading1, heading2)

        try:
            percentile_out_path = f'{DIR_ROOT}/viz_dataframes/percentiles/{heading1}-{heading2}.pkl'
            journal_out_path = f'{DIR_ROOT}/viz_dataframes/journals/{heading1}-{heading2}.pkl'

            if os.path.exists(percentile_out_path) and os.path.exists(journal_out_path):
                continue

            df = load_pair_headings(heading1, heading2)
            # Store per-paper results
            out_path = f'{DIR_ROOT}/viz_dataframes/percentiles/{heading1}-{heading2}.pkl'
            with open(out_path, 'wb') as out_file:
                pkl.dump(df, out_file)

            journal_groups = df.groupby('journal')
            medians = journal_groups.median()
            sizes = journal_groups.size()
            medians['journal_title'] = medians.index
            # Store journal-level results
            out_path = f'{DIR_ROOT}/viz_dataframes/journals/{heading1}-{heading2}.pkl'
            with open(out_path, 'wb') as out_file:
                pkl.dump(medians[sizes > args.journal_size_cutoff], out_file)
        except FileNotFoundError:
            print('Results not found')
            continue
