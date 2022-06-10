from networkx import DiGraph


def cites_downstream(in_doi: str, graph: DiGraph, out_dois: set) -> bool:
    """
    Checks whether `in_doi` cites (has an out_edge pointing to) any papers in `out_dois`.

    Arguments
    ---------
    in_doi: The doi to check
    graph: The graph containing all citations
    out_dois: The set of dois that may be cited by `in_doi`

    Returns
    -------
    is_cited: True if `in_doi` cites something in `out_doi`, otherwise False
    """
    citations = 0
    for _, in_target in graph.out_edges(in_doi):
        if in_target in out_dois:
            return True
    return False

def count_papers_citing(dois: set, graph: DiGraph) -> int:
    """
    Get the papers citing the given set of dois.

    Arguments
    ---------
    dois: The dois whose citations should be listed
    graph: The graph containing all citations

    Returns
    -------
    citations: The number of articles citing the given dois
    """
    papers_citing = set()
    for doi in dois:
        for source, _ in graph.in_edges(doi):
            papers_citing.add(source)
    return len(papers_citing)

def disruption_index(doi: str, graph: DiGraph) ->  float:
    """
    Calculates the disruption index from Wu, Wang, and Evans.

    In short, the disruption index is the difference between the number of the articles citing
    `doi` but none of its children and the number of articles citing both `doi` and at least
    one of its children.

    Intuitively, a paper with values near 1 is "disruptive" in that the papers citing it don't
    cite the papers it cites, while a paper with a value near -1 is "developmental" in that
    the papers citing it also cite the papers it cites. Papers with values near zero are deemed
    neither disruptive nor developmental.

    Arguments
    ---------
    doi: The doi to calculate the disruption index for
    graph: The graph containing all citations

    Returns
    -------
    disruption - The disruption index for the given doi

    References
    ----------
    - Wu, L., Wang, D. & Evans, J.A. Large teams develop and small teams disrupt science
      and technology. Nature 566, 378–382 (2019). https://doi.org/10.1038/s41586-019-0941-9
    """
    # The set of all dois cited by the node of interest
    out_dois = set()
    # Nodes citing the node of interest but not the articles it cites
    center_only = 0
    # Nodes citing both the node of interest and the articles it cites
    center_and_cited = 0

    for _, out_node in graph.out_edges(doi):
        out_dois.add(out_node)

    for in_node, _ in graph.in_edges(doi):
        if cites_downstream(in_node, graph, out_dois):
            center_and_cited += 1
        else:
            center_only += 1

    downstream_citations = count_papers_citing(out_dois, graph)
    # Don't count center paper
    downstream_citations -= 1

    di_denom = center_only + downstream_citations
    di_num = center_only - center_and_cited

    # Return 0 for singleton nodes
    if di_denom == 0:
        return 0

    return di_num / di_denom