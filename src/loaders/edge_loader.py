import src.schema as schema

def load_edges_to_neo4j(driver, edge_name, validated_data):
    """Generates the Cypher query dynamically and executes the batch edge load."""
    
    # Fetch the class from src.schema using the string name
    try:
        model_class = getattr(schema, edge_name)
    except AttributeError:
        raise ValueError(f"Pipeline Error: Class '{edge_name}' not found in src.schema!")

    # Extract the routing metadata
    rel_type      = getattr(model_class, 'label', edge_name)
    edge_id_field = getattr(model_class, 'label_id')
    src_label     = getattr(model_class, 'source_label')
    src_id_field  = getattr(model_class, 'source_id_field')
    tgt_label     = getattr(model_class, 'target_label')
    tgt_id_field  = getattr(model_class, 'target_id_field')
    # Dynamically build the query
    # We MATCH both nodes by their specific IDs, then MERGE the relationship
    query = f"""
        UNWIND $data AS row
        MATCH (source:{src_label} {{{src_id_field}: row.{src_id_field}}})
        MATCH (target:{tgt_label} {{{tgt_id_field}: row.{tgt_id_field}}})
        MERGE (source)-[r:{rel_type} {{{edge_id_field}: row.{edge_id_field}}}]->(target)
        SET r += row
    """
    
    with driver.session() as session:
        # Upload edges
        counter = session.run(query, data=validated_data).consume().counters
        
        # How many edges of this type exist?
        count_query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS total_count"
        total_edges = session.run(count_query).single()["total_count"]
        
        return counter.relationships_created, total_edges
