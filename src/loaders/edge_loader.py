import src.schema as schema

def load_edges_to_neo4j(driver, edge_name, validated_data):
    """Generates the Cypher query dynamically and executes the batch edge load."""
    
    # Fetch the class from src.schema using the string name
    try:
        model_class = getattr(schema, edge_name)
    except AttributeError:
        raise ValueError(f"Pipeline Error: Class '{edge_name}' not found in src.schema!")

    # 1. Extract the routing metadata (Updated to match new ClassVars)
    rel_type  = getattr(model_class, 'label', edge_name)
    src_label = getattr(model_class, 'source_label')
    tgt_label = getattr(model_class, 'target_label')
    
    # 2. Dynamically find the property names using Pydantic aliases
    src_id_field = None
    tgt_id_field = None
    edge_id_field = None

    for field_name, field_info in model_class.model_fields.items():
        # Updated to check validation_alias instead of alias
        if getattr(field_info, 'validation_alias', None) == "source_id":
            src_id_field = field_name
        elif getattr(field_info, 'validation_alias', None) == "target_id":
            tgt_id_field = field_name
        elif field_name.endswith("_id"):
            # Automatically identifies the edge's own ID 
            # assuming it's the only other field ending in '_id'
            edge_id_field = field_name

    # Safety check to ensure the schema was configured correctly
    if not src_id_field or not tgt_id_field:
        raise ValueError(f"Schema Error: {edge_name} is missing 'source_id' or 'target_id' aliases.")
    
    if not edge_id_field:
        raise ValueError(f"Schema Error: Could not identify the edge's primary ID field for {edge_name}.")
        
    # Dynamically build the query
    # We MATCH both nodes by their specific IDs, then MERGE the relationship
    query = f"""
        UNWIND $data AS row
        MATCH (source:{src_label} {{{src_id_field}: row.{src_id_field}}})
        MATCH (target:{tgt_label} {{{tgt_id_field}: row.{tgt_id_field}}})
        MERGE (source)-[r:{rel_type} {{{edge_id_field}: row.{edge_id_field}}}]->(target)
        SET r += row
        RETURN row.{edge_id_field} AS id
    """
    with driver.session() as session:
        # Upload edges
        result = session.run(query, data=validated_data)
        
        ##FAILED INSERTS
        successful_ids = {r["id"] for r in result}
        failed_ids = [row[edge_id_field] for row in validated_data if row[edge_id_field] not in successful_ids]
        if failed_ids: 
            print(f"Failed to insert: {failed_ids}")
        
        # Counter
        counter = result.consume().counters
        count_query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS total_count"
        total_edges = session.run(count_query).single()["total_count"]
        
        return counter.relationships_created, total_edges