import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
#from neo4j.exceptions import Neo4jError
#import src.schema as pydantic_schema
#import inspect
#from pydantic import BaseModel

class GraphDB:
    
    def __init__(self):
        """Load environment variables and returns them as a dictionary."""
        load_dotenv(override = True)
        
        URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687") # Default if not found
        USER     = os.getenv("NEO4J_USER", "neo4j")
        PASSWORD = os.getenv("NEO4J_PASSWORD")

        try:
            # Create the driver
            self.driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
            # Explicitly ping the database to verify credentials and status
            self.driver.verify_connectivity()
        except Exception as e:
            print(f"No connection at {URI}. \nIs your Neo4j database running?\nDid you create a .env file?")
            print(f"Error Details: {e}\n")
        
        print(f"Connection with database established at {URI}.")
        self.driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    
    def close(self):
        """Safely closes the database connection."""
        print("Connection with database closed.")
        if self.driver is not None:
            self.driver.close()
    

    
    
    
    
    
    
    
    # def set_constraints(self):
    #     """
    #     Reads Pydantic models and dynamically applies Neo4j uniqueness constraints 
    #     for fields tagged with 'is_unique_neo4j'.
    #     """
    #     print("Checking and applying dynamic constraints from schema...")
        
    #     # Extract all Pydantic models from the schema
    
    #     models = [obj for name, obj in inspect.getmembers(pydantic_schema, inspect.isclass)
    #     if issubclass(obj, BaseModel) and obj is not BaseModel]
 
        
    #     constraint_targets = (
    #         (model.__name__, field_name)
    #         for model in models
    #         for field_name, field_info in model.model_fields.items()
    #         if (field_info.json_schema_extra or {}).get("is_unique_neo4j")
    #     )

    #     with self.driver.session() as session:
    #         for label, field in constraint_targets:
    #             c_name = f"{label}_{field}_unique"
    #             query = f"CREATE CONSTRAINT {c_name} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{field} IS UNIQUE"
                
    #             try:
    #                 session.run(query)
    #                 print(f"Applied constraint: {c_name}")
    #             except Neo4jError as e:
    #                 print(f"Failed to apply {c_name}. Error: {e.message}")

    #     print("Dynamic constraint generation complete.")
        
        
        