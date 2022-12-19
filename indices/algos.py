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


def all_nodes_disruption_index(graph) -> dict:
    """
    Run the disruption_index function on all nodes

    This function wraps `disruption_index` to make it behave the same way as networkx
    graph centrality functions

    Arguments
    ---------
    graph: The graph containing all citations

    Returns
    -------
    node_to_metric: A dict mapping each graph node to its corresponding disruption index value
    """
    node_to_metric = {}
    for node in graph.nodes:
        node_to_metric[node] = disruption_index(node, graph)
    return node_to_metric


def disruption_index(doi: str, graph: DiGraph) -> float:
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

    out_dois = set(graph.successors(doi))

    for in_node in graph.predecessors(doi):
        if cites_downstream(in_node, graph, out_dois):
            center_and_cited += 1
        else:
            center_only += 1

    downstream_citations = count_papers_citing(out_dois, graph)

    # If we're missing data about what the paper cites, the metric probably isn't meaningful
    if downstream_citations == 0:
        return None

    # Don't count center paper
    downstream_citations -= 1

    di_denom = center_only + downstream_citations
    di_num = center_only - center_and_cited

    # Return None for singleton nodes
    if di_denom == 0:
        return None

    try:
        assert abs(di_num / di_denom) <= 1
    except AssertionError as e:
        print(downstream_citations)
        print(doi)
        raise AssertionError

    return di_num / di_denom
