"""
This script uses the pubmedby package to download information about articles
with specific MeSH headings from pubmed.
The code is based on
https://github.com/greenelab/iscb-diversity/blob/master/01.download-pubmed.ipynb
and is used in accordance with their licenses
"""

import argparse
import collections
import logging
import pathlib
import random
import time
import tqdm
from concurrent.futures import ThreadPoolExecutor
from typing import IO

import xml.etree.ElementTree as ET
import lzma
import requests
from ratelimit import limits, sleep_and_retry

HEADINGS = [
    "Anatomy",
    "Histocytochemistry",
    "Immunochemistry",
    "Molecular Biology",
    "Proteomics",
    "Metabolomics",
    "Human Genetics",
    "Genetics, Population",
    "Genetic Research",
    "Food Microbiology",
    "Soil Microbiology",
    "Water Microbiology",
    "Computational Biology",
    "Biophysics",
    "Biotechnology",
    "Neurosciences",
    "Pharmacology",
    "Physiology",
    "Toxicology",
    "Chemistry, Pharmaceutical",
    "Crystallography",
    "Electrochemistry",
    "Photochemistry",
    "Statistics as Topic",
    "Nonlinear Dynamics",
    "Acoustics",
    "Electronics",
    "Magnetics",
    "Nuclear Physics",
    "Rheology",
    "Fiber Optic Technology",
    "Microscopy",
    "Operations Research",
    "Research Design",
    "Health Services Research",
    "Nursing Evaluation Research",
    "Nursing Methodology Research",
    "Outcome Assessment, Health Care",
    "Translational Research, Biomedical",
    "Empirical Research",
    "Nanotechnology",
    "Microtechnology",
    "Ecology",
    "Geography",
    "Paleontology",
]


@sleep_and_retry
@limits(calls=10, period=1)
def check_limit():
    """
    Share ratelimit between esearch_query and download_pubmed_ids
    stackoverflow.com/questions/40748687/python-api-rate-limiting-how-to-limit-api-calls-globally
    """
    return


def limited_esearch_query(
    payload: dict, retmax: int = 10000, sleep: float = 1, tqdm=tqdm.tqdm, api_key=None
):
    """
    Return identifiers using the ESearch E-utility.
    Set `tqdm=tqdm.notebook` to use the tqdm notebook interface.
    Set `tqdm=None` to disable the progress bar.

    Note
    ----
    This function is a version of a pubmedpy function modified to allow rate-limited
    paralellism. The original function can be found here:
    https://github.com/dhimmel/pubmedpy/blob/main/pubmedpy/eutilities.py
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    payload["rettype"] = "xml"
    payload["retmax"] = retmax
    payload["retstart"] = 0
    if api_key:
        payload["api_key"] = api_key
    ids = list()
    count = 1
    progress_bar = None
    while payload["retstart"] < count:
        check_limit()
        response = requests.get(url, params=payload)
        tree = ET.fromstring(response.content)
        count = int(tree.findtext("Count"))
        if tqdm and not progress_bar:
            progress_bar = tqdm(total=count, unit="ids")
        add_ids = [id_.text for id_ in tree.findall("IdList/Id")]
        ids += add_ids
        payload["retstart"] += retmax
        if tqdm:
            progress_bar.update(len(add_ids))
        time.sleep(sleep)
    if tqdm:
        progress_bar.close()
    return ids


def download_pubmed_ids(
    ids: list,
    write_file: IO,
    endpoint: str = "esummary",
    retmax: int = 100,
    retmin: int = 20,
    sleep: float = 0.34,
    error_sleep: float = 10,
    tqdm=tqdm.tqdm,
    api_key=None,
):
    """
    Submit an ESummary or EFetch query for PubMed records and write results as xml
    to write_file.
    Set `tqdm=tqdm.notebook` to use the tqdm notebook interface.

    Note
    ----
    This function is a version of a pubmedpy function modified to allow rate-limited
    paralellism. The original function can be found here:
    https://github.com/dhimmel/pubmedpy/blob/main/pubmedpy/eutilities.py
    """
    # Base URL for PubMed's esummary eutlity
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{endpoint}.fcgi"

    # Set up progress stats
    n_total = len(ids)
    successive_errors = 0
    progress_bar = tqdm(total=n_total, unit="articles")
    initialize_xml = True

    # Set up queue
    idq = collections.deque()

    for i in range(0, len(ids), retmax):
        idq.append(ids[i : i + retmax])

    # Query until the queue is empty
    while idq:
        time.sleep(sleep)
        id_subset = idq.popleft()
        id_subset_len = len(id_subset)

        # Perform eutilities API request
        id_string = ",".join(map(str, id_subset))
        payload = {"db": "pubmed", "id": id_string, "rettype": "xml"}
        if api_key:
            payload["api_key"] = api_key
        try:
            check_limit()
            response = requests.get(url, params=payload)
            response.raise_for_status()
            tree = ET.fromstring(response.content)
            successive_errors = 0
        except Exception as e:
            successive_errors += 1
            logging.warning(
                f"{successive_errors} successive error: {id_subset_len} IDs"
                f"[{id_subset[0]} … {id_subset[-1]}] threw {e}"
            )
            if id_subset_len >= retmin * 2:
                mid = len(id_subset) // 2
                idq.appendleft(id_subset[:mid])
                idq.appendleft(id_subset[mid:])
            else:
                idq.appendleft(id_subset)
            time.sleep(error_sleep * successive_errors)
            continue

        # Write XML to file
        if initialize_xml:
            initialize_xml = False
            write_file.write(f"<{tree.tag}>\n")
        for child in tree:
            xml_str = ET.tostring(child, encoding="unicode")
            write_file.write(xml_str.rstrip() + "\n")

        # Report progress
        progress_bar.update(id_subset_len)

    progress_bar.close()
    # Write final line of XML
    write_file.write(f"</{tree.tag}>\n")


def worker(mesh_term, api_key):
    # Make the term safe for putting in a path
    path_term = mesh_term.replace(" ", "_")
    path_term = path_term.replace("-", "_")
    path_term = path_term.replace(",", "")
    path_term = path_term.lower()
    path = pathlib.Path(f"data/pubmed/efetch/{path_term}.xml.xz")
    if not path.exists():
        payload = {
            "db": "pubmed",
            "term": f'"journal article"[pt] AND "{mesh_term}"[MeSH Terms] AND English[Language]',
        }
        pubmed_ids = limited_esearch_query(
            payload, api_key=api_key, sleep=1, retmax=100000
        )
        pubmed_ids = sorted(map(int, pubmed_ids))
        print(f"{len(pubmed_ids):,} articles for {mesh_term}")

        path.parent.mkdir(parents=True, exist_ok=True)
        with lzma.open(path, "wt") as write_file:
            download_pubmed_ids(
                pubmed_ids,
                write_file,
                endpoint="efetch",
                retmax=200,
                retmin=50,
                sleep=1,
                error_sleep=1,
                api_key=api_key,
            )
    else:
        print(f"{path} exists already; skipping")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--key_file", help="A file containing an NCBI API key", default=None
    )
    args = parser.parse_args()

    api_key = None
    if args.key_file is not None:
        with open(args.key_file, "r") as in_file:
            api_key = in_file.readline().strip()

    # I could be a little more memory eficient by creating a partial function or something,
    # but this is way more readable and I'm only using ~1kB of mem to do this
    api_keys = [api_key] * len(HEADINGS)

    with ThreadPoolExecutor(max_workers=9) as executor:
        results = executor.map(worker, HEADINGS, api_keys)

    for result in results:
        print(result)
