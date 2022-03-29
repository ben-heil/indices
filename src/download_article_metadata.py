"""
This script uses the pubmedby package to download information about articles
with specific MeSH headings from pubmed.
The code is a modification of
https://github.com/greenelab/iscb-diversity/blob/master/01.download-pubmed.ipynb
and is used in accordance with their licenses
"""

import argparse
import pathlib
import lzma
import tqdm

from pubmedpy.eutilities import esearch_query, download_pubmed_ids

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mesh_term', help='The MeSH term whose article info should be downloaded')

    args = parser.parse_args()

payload = {
    'db': 'pubmed',
    'term': f'"journal article"[pt] AND "{args.mesh_term}"[MeSH Terms] AND English[Language]',
}

pubmed_ids = esearch_query(payload)
pubmed_ids = sorted(map(int, pubmed_ids))
print(f'{len(pubmed_ids):,} articles for English {args.mesh_term}')

# Make the term safe for putting in a path
path_term = '_'.join(args.mesh_term.split(' '))


# # TODO remove this block?
# path = pathlib.Path(f'data/pubmed/esummary/{path_term}.xml.xz')
# path.parent.mkdir(parents=True, exist_ok=True)
# with lzma.open(path, 'wt') as write_file:
#     download_pubmed_ids(
#         pubmed_ids, write_file, endpoint='esummary',
#         retmax=200, retmin=50, sleep=0, error_sleep=1,
#     )

path = pathlib.Path(f'data/pubmed/efetch/{path_term}.xml.xz')
path.parent.mkdir(parents=True, exist_ok=True)
with lzma.open(path, 'wt') as write_file:
    download_pubmed_ids(
        pubmed_ids, write_file, endpoint='efetch',
        retmax=200, retmin=50, sleep=0, error_sleep=1,
    )