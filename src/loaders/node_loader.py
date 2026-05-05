import src.schema as schema

def load_nodes_to_neo4j(driver, node_name, validated_data):
    """Generates the Cypher query dynamically and executes the batch load."""
    
    # Fetch the class from src.schema using the string name
    try:
        model_class = getattr(schema, node_name)
    except AttributeError:
        raise ValueError(f"Pipeline Error: Class '{node_name}' not found in src.schema!")

    # Extract the label 
    label = getattr(model_class, 'label', node_name)
    
    # Find the unique ID field on the fly
    id_field = next(
        (f_name for f_name, f_info in model_class.model_fields.items() 
         if f_info.json_schema_extra and f_info.json_schema_extra.get("is_unique_neo4j")), 
        None
    )
    
    if not id_field:
        raise ValueError(f"Pipeline Error: Model '{node_name}' is missing a unique ID field!")
    
    # Dynamically build the query
    query = f"""
        UNWIND $data AS row
        MERGE (n:{label} {{{id_field}: row.{id_field}}})
        SET n += row
    """
    
    with driver.session() as session:
        
        # Upload nodes
        counter = session.run(query, data=validated_data).consume().counters
        
        # How many nodes exist?
        count_query = f"MATCH (n:{label}) RETURN count(n) AS total_count"
        total_nodes = session.run(count_query).single()["total_count"]
        
        return counter.nodes_created,total_nodes 
