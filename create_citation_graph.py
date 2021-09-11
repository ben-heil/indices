import glob
import gzip
import itertools
import json
import pickle
from dataclasses import dataclass, field
from datetime import date, datetime
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Lock
from typing import List, Dict

from tqdm import tqdm

class Graph():
    def __init__(self):
        self.nodes = {}

@dataclass
class Publication:
    doi: str = None
    authors: List[Dict[str, str]] = field(default_factory=list)
    cited_by: set = field(default_factory=set)
    paper_cites: set = field(default_factory=set)
    title: str = None
    journal: str = None
    date_published: datetime = None


def parse_entry(entry: dict) -> Publication:
    # TODO check whether article has citations/is cited, and has all the data we need
    # print(entry.keys())

    # print('-'* 80)
    # for key in entry.keys():
    #     print(key)
    #     print(entry[key])
    #     print('-'* 80)

    doi = entry.get('DOI', None)
    authors = entry.get('author', None)
    paper_cites = entry.get('reference', None)

    title = entry.get('title', None)
    journal = entry.get('journal-title')
    if len(title) == 0:
        title = None
    if title is not None:
        try:
            title = title[0]
        except IndexError:
            print(title)

    if 'created' in entry:
        date_published = entry['created'].get('date-time', None)
    if date_published is not None:
        date_published = datetime.strptime(date_published, '%Y-%m-%dT%H:%M:%SZ')

    current_pub = Publication(doi=doi, authors=authors, title=title,
                              paper_cites=paper_cites, date_published=date_published, )

    return current_pub

def validate_publication(pub: Publication):
    """Check to see whether all fields are filled out in the publication"""
    if None in [pub.doi, pub.title, pub.date_published, pub.authors, pub.title,
                pub.date_published, pub.paper_cites]:
        return False
    if len(pub.paper_cites) <= 0:
        return False

    return True


def parse_file(path: str):
    pubs = []
    with gzip.open(path) as in_file:
        file_json = json.load(in_file)
        for entry in file_json['items']:
            current_pub = parse_entry(entry)

            entry_contents_valid = validate_publication(current_pub)

            if not entry_contents_valid:
                continue

            pubs.append(current_pub)
    return pubs


def build_graph(publications: List[Publication]) -> Graph:
    pub_graph = Graph()

    print('Creating graph')
    # Create a map from doi to publication
    for pub in tqdm(publications):
        if hasattr(pub, 'doi'):
            pub_graph.nodes[pub.doi] = pub

    # Track which articles cite the current article
    print('Building backlinks')

    for pub in tqdm(pub_graph.nodes.values()):
        pub.paper_cites_doi = set()
        for citation in pub.paper_cites:
            if 'DOI' in citation and citation['DOI'] in pub_graph.nodes:
                cited_doi = citation['DOI']
                cited_publication = pub_graph.nodes[cited_doi]
                pub.paper_cites_doi.add(cited_doi)

                if cited_publication.cited_by is None:
                    cited_publication.cited_by = set(pub.doi)
                else:
                    cited_publication.cited_by.add(pub.doi)

    return pub_graph


def calculate_disruption_index(pub_graph: Graph) -> Graph:
    print('Calculating disruption indices')

    i = 0
    for current_pub in tqdm(pub_graph.nodes.values()):
        # The number of papers citing both this article and at least one paper this article cites
        current_and_ref = 0
        # The number of papers citing this article but not the papers it cites
        current_only = 0
        # The number of papers citing papers cited by this article but not this article itself
        ref_only = 0

        for future_doi in current_pub.cited_by:
            future_pub = pub_graph.nodes[future_doi]
            for citation in future_pub.paper_cites:
                if 'DOI' in citation:
                    if citation['DOI'] in current_pub.paper_cites_doi:
                        current_and_ref += 1
                    else:
                        current_only += 1

            for citation_doi in current_pub.paper_cites_doi:
                if citation_doi in pub_graph.nodes:
                    cited_paper = pub_graph.nodes[citation_doi]
                    ref_only += len(cited_paper.cited_by)

        # Papers that cite the current paper shouldn't be counted in ref only
        ref_only -= current_and_ref

        total_citations = current_only + current_and_ref + ref_only
        if total_citations == 0:
            continue
        i += 1
        disruption_index = (current_only - current_and_ref) / total_citations

        current_pub.disruption_index = disruption_index
        #print(current_pub.paper_cites)
        #print('Cite stats', len(current_pub.paper_cites), len(current_pub.paper_cites_doi))
        #print(current_only, current_and_ref, ref_only, total_citations)
        #print(disruption_index)
    print('Pubs in calc_disruption_index', i)

    return pub_graph


if __name__ == '__main__':

    try:
        with open('publications.pkl', 'rb') as in_file:
            publications = pickle.load(in_file)
    except FileNotFoundError:
        # TODO use argparse to get the directory with the json files
        files = glob.glob('crossref_public_data_file_2021_01/*.json.gz')
        executor = ProcessPoolExecutor(max_workers=8)
        publications = list(tqdm(executor.map(parse_file, files[:1000]), total=len(files)))

        with open('publications.pkl', 'wb') as out_file:
            pickle.dump(publications, out_file)

    #{executor.submit(parse_file, file): file for file in tqdm(files)}
    # Should this just be a database?

    print(len(publications))
    publications = list(itertools.chain.from_iterable(publications))
    print(len(publications))
    files = glob.glob('crossref_public_data_file_2021_01/*.json.gz')
    print(len(files))



    graph = build_graph(publications)

    graph = calculate_disruption_index(graph)

    print(len(graph.nodes))

    # for file in tqdm(files):
    #     parse_file(file)