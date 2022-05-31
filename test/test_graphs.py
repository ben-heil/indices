import networkx as nx
import pytest

from indices import disruption_index, cites_downstream, get_citation_count


def test_max_disruption():
    disrupt_graph = nx.DiGraph()

    for i in range(10):
        disrupt_graph.add_edge(f'in_{i}', 'center')

    for i in range(12):
        disrupt_graph.add_edge('center', f'out_{i}')

    # Add disconnected nodes
    disrupt_graph.add_edge('disconnected1', 'disconnected2')
    disrupt_graph.add_edge('disconnected2', 'disconnected3')
    disrupt_graph.add_edge('disconnected3', 'disconnected1')

    assert disruption_index('center', disrupt_graph) == pytest.approx(1)


def test_max_development():
    disrupt_graph = nx.DiGraph()

    for i in range(10):
        disrupt_graph.add_edge(f'in_{i}', f'out_{i}')
        disrupt_graph.add_edge(f'in_{i}', 'center')

    for i in range(10):
        disrupt_graph.add_edge('center', f'out_{i}')

    assert disruption_index('center', disrupt_graph) == pytest.approx(-1)


def test_zero_disruption():
    disrupt_graph = nx.DiGraph()

    for i in range(5):
        disrupt_graph.add_edge(f'in_{i}', f'out_{i}')
        disrupt_graph.add_edge(f'in_{i}', 'center')
    for i in range(5,10):
        disrupt_graph.add_edge(f'in_{i}', 'center')

    for i in range(10):
        disrupt_graph.add_edge('center', f'out_{i}')

    assert disruption_index('center', disrupt_graph) == pytest.approx(0)

def test_intermediate_disruption():
    disrupt_graph = nx.DiGraph()

    disrupt_graph.add_edge(4, 1)
    disrupt_graph.add_edge(5, 'center')
    disrupt_graph.add_edge(6, 'center')
    disrupt_graph.add_edge('center', 1)
    disrupt_graph.add_edge('center', 2)
    disrupt_graph.add_edge('center', 3)
    disrupt_graph.add_edge(7, 3)
    disrupt_graph.add_edge(7, 'center')

    assert disruption_index('center', disrupt_graph) == pytest.approx(.25)


def test_cites_downstream():
    graph = nx.DiGraph()
    graph.add_edge('in1', 'out1')
    graph.add_edge('center', 'out1')

    out_dois = set()
    out_dois.add('out1')

    assert cites_downstream('in1', graph, out_dois)


def test_get_citation_count():
    graph = nx.DiGraph()

    graph.add_edge(1, 2)
    graph.add_edge(1, 3)
    graph.add_edge(1, 4)
    assert get_citation_count(set([1, 2, 3, 4]), graph) == 3

    graph.add_edge(4, 1)
    assert get_citation_count(set([1, 2, 3, 4]), graph) == 4

def test_zero_citation_count():
    graph = nx.DiGraph()
    graph.add_edge(1337, 1338)
    assert get_citation_count(set([1337]), graph) == 0

def test_subset_citation_count():
    graph = nx.DiGraph()

    graph.add_edge(1, 2)
    graph.add_edge(1, 3)
    graph.add_edge(1, 4)
    assert get_citation_count(set([1, 2, 3]), graph) == 2


