queries = {
    # Pattern 1: Simple Aggregations
    "CQ13": """
        MATCH (s:Student)-[c:completed]->(lt:Learning_Task)
        RETURN AVG(c.score) AS AverageTotalScore
    """,
    
    "CQ19": """
        MATCH (ls:Learning_Session)
        RETURN AVG(duration.between(datetime(ls.start_time), datetime(ls.end_time)).minutes) AS AverageSessionLengthMinutes
    """,

    # Pattern 4: Ontology & Taxonomy Mapping
    "CQ61": """
        MATCH (t:Learning_Task)-[r:TRAINS]->(req)
        WHERE req.name = $requirement_name 
          AND labels(req)[0] = $requirement_type
        RETURN t.title AS Task, type(r) AS Relationship
    """
}

base_ontology_query = """
    MATCH (t:Learning_Task)-[r]->(req)
    WHERE labels(req)[0] = $requirement_type
    RETURN t.title AS Task, req.title AS Requirement
"""

queries = {
    "CQ61": base_ontology_query, # In which tasks is a competence/skill trained?
    "CQ67": base_ontology_query, # Which cognitive processes are required?
    "CQ69": base_ontology_query  # In which knowledge dimension is it required?
}