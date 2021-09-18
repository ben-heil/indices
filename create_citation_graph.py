import glob
import gzip
import json

from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from multiprocessing import Lock
from typing import List, Dict

from pymongo import MongoClient
from tqdm import tqdm


def chunk_generator(doi_cursor, chunk_size=50):
    """
    To avoid having to create a new client millions of times, we want to pass
    groups of dois into the calculate_backlinks function
    """
    current_index = 0

    i = 0
    try:
        while True:
            doc_list = []
            i += 1
            for _ in range(chunk_size):
                doc_list.append(doi_cursor.next())
            if i % 100 == 0:
                print(i)
            yield doc_list

    except StopIteration:
        pass


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
    doi = entry.get('DOI', None)
    authors = entry.get('author', None)
    paper_cites = entry.get('reference', None)
    journal = entry.get('short-container-title', None)

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

    pub_dict = {'doi':doi, 'authors':authors, 'title':title, 'journal': journal,
                'paper_cites':paper_cites, 'date_published':date_published, '_id': doi}

    return pub_dict

def validate_publication(pub: Publication):
    """Check to see whether all fields are filled out in the publication"""
    fields = ['doi', 'authors', 'title', 'paper_cites', 'date_published', '_id']
    for field in fields:
        if field not in pub:
            return False
        if pub[field] is None:
            return False
    # Remove papers that don't cite anything
    if len(pub['paper_cites']) <= 0:
        return False

    return True


def parse_file(path: str, files_read: set):
    if path in files_read:
        return
    pubs = []

    client = MongoClient()
    database = client.disrupt_vs_develop
    citation_table = database.citations
    files_table = database.files_read

    with gzip.open(path) as in_file:
        file_json = json.load(in_file)
        for entry in file_json['items']:
            current_pub = parse_entry(entry)

            entry_contents_valid = validate_publication(current_pub)

            if not entry_contents_valid:
                continue

            if current_pub is not None:
                results = citation_table.replace_one(filter={'_id': current_pub['doi']},
                                                     replacement=current_pub, upsert=True)

    file_record = {'_id': path, 'path': path}
    result = files_table.insert_one(file_record)

def calculate_backlinks(doi_entries: list) -> None:
    client = MongoClient()
    database = client.disrupt_vs_develop
    citation_table = database.citations
    for doi_entry in doi_entries:
        doi = doi_entry['_id']


        current_pub = citation_table.find_one({'_id': doi})

        if current_pub is None:
            print("{} wasn't found in the database".format(doi))
            return

        paper_cites = current_pub['paper_cites']
        for citation in paper_cites:
            if 'DOI' in citation:
                citation_table.find_one_and_update(filter={'_id': citation['DOI']},
                                                update={'$push': {'cited_by': doi}})

    client.close()
    return


def calculate_disruption_index(doi_entries) -> None:
    client = MongoClient()
    database = client.disrupt_vs_develop
    citation_table = database.citations

    for doi_entry in doi_entries:
        doi = doi_entry['_id']
        current_pub = citation_table.find_one({'_id': doi})

        # Remove duplicate entries in the cited_by list
        if 'cited_by' not in current_pub:
            continue
        cited_by = list(set(current_pub['cited_by']))


        # TODO maybe precalculate this to rerun faster?
        current_paper_cites_doi = set()
        for citation in current_pub['paper_cites']:
            if 'DOI' in citation:
                current_paper_cites_doi.add(citation['DOI'])

        # The number of papers citing both this article and at least one paper this article cites
        current_and_ref = 0
        # The number of papers citing this article but not the papers it cites
        current_only = 0
        # The number of papers citing papers cited by this article but not this article itself
        ref_only = 0

        for future_doi in cited_by:
            future_pub = citation_table.find_one({'_id': future_doi})

            future_cites = future_pub['paper_cites']
            for citation in future_cites:
                if 'DOI' in citation:
                    if citation['DOI'] in current_paper_cites_doi:
                        current_and_ref += 1
                    else:
                        current_only += 1

            for citation_doi in current_paper_cites_doi:
                citation = citation_table.find_one({'_id': citation_doi})
                if citation is not None:
                    current_cited_by = list(set(citation['cited_by']))
                    ref_only += len(current_cited_by)

        # Papers that cite the current paper shouldn't be counted in ref only
        ref_only -= current_and_ref

        total_citations = current_only + current_and_ref + ref_only
        if total_citations == 0:
            continue
        disruption_index = (current_only - current_and_ref) / total_citations

        citation_table.find_one_and_update(filter={'_id': doi},
                                                update={'$set': {'disruption_index': disruption_index,
                                                                 'current_and_ref': current_and_ref,
                                                                 'ref_only': ref_only,
                                                                 'current_only': current_only}})


if __name__ == '__main__':

    client = MongoClient()
    database = client.disrupt_vs_develop
    citation_table = database.citations
    files_table = database.files_read

    # files_read = set(files_table.find().distinct('_id'))

    # files = glob.glob('crossref_public_data_file_2021_01/*.json.gz')

    chunk_size = 10000
    executor = ProcessPoolExecutor(max_workers=2)

    #list(tqdm(executor.map(parse_file, files, repeat(files_read)), total=len(files)))

    # # Too many entries to use distinct so we have to get a bit fancier and iterate over a cursor
    dois = citation_table.find({}, {'_id': 1}, hint=([('_id', 1)]))

    # # https://stackoverflow.com/questions/9786736/how-to-read-through-collection-in-chunks-by-1000
    # generator = chunk_generator(dois, 10000)

    # print('Processing backlinks')

    # tqdm(executor.map(calculate_backlinks, generator), total=dois.count() // chunk_size)

    print('Done!')
    print('Calculating disruption indices')

    generator = chunk_generator(dois, chunk_size)

    tqdm(executor.map(calculate_disruption_index, generator), total=dois.count() // chunk_size)

