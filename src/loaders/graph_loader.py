from src.loaders.node_loader import load_nodes_to_neo4j
from src.loaders.edge_loader import load_edges_to_neo4j

class GraphLoader:
    def __init__(self, driver):
        self.driver = driver

    def load(self, entity_type, label, data):
        """
        Switches between node and edge loading logic.
        """
        if entity_type.upper() == "NODE":
            nodes_created,total_nodes = load_nodes_to_neo4j(self.driver, label, data)
            return [label, nodes_created, total_nodes]
        elif entity_type.upper() == "EDGE":
            edges_created,total_edges = load_edges_to_neo4j(self.driver, label, data)
            return [label, edges_created, total_edges]
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")