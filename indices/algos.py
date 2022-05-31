from networkx import DiGraph


def cites_downstream(in_doi: str, graph: DiGraph, out_dois: set) -> bool:
    for in_source, in_target in graph.out_edges(in_doi):
        if in_source == in_doi and in_target in out_dois:
            return True
    return False

def get_citation_count(dois: set, graph: DiGraph) -> int:
    downstream_citations = 0
    for doi in dois:
        downstream_citations += graph.in_degree(doi)
    return downstream_citations

def disruption_index(doi: str, graph: DiGraph) ->  float:
    # The set of all dois cited by the node of interest
    out_dois = set()
    # Nodes citing the node of interest but not the articles it cites
    center_only = 0
    # Nodes citing both the node of interest and the articles it cites
    center_and_cited = 0

    for _, out_node in graph.out_edges(doi):
        out_dois.add(out_node)

    for in_node, _ in graph.in_edges(doi):
        print(graph.edges(in_node))
        if cites_downstream(in_node, graph, out_dois):
            center_and_cited += 1
        else:
            center_only += 1

    downstream_citations = get_citation_count(out_dois, graph)
    downstream_citations -= graph.out_degree(doi)

    di_denom = center_only + downstream_citations
    di_num = center_only - center_and_cited

    # Return 0 for singleton nodes
    if di_denom == 0:
        return 0

    print(f'Center only: {center_only}')
    print(f'Center and downstream: {center_and_cited}')
    print(f'Downstream total: {downstream_citations}')

    return di_num / di_denom