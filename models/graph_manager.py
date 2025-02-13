# models/graph_manager.py
import networkx as nx

class GraphManager:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node):
        self.graph.add_node(node.id, data=node)

    def remove_node(self, node_id):
        self.graph.remove_node(node_id)

    def add_edge(self, start_node, end_node):
        self.graph.add_edge(start_node.id, end_node.id)

    def remove_edge(self, start_node, end_node):
        self.graph.remove_edge(start_node.id, end_node.id)
