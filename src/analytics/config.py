import os
from dotenv import load_dotenv
import urllib.parse
from neomodel import db

class NeomodelManager:
    """Connects Neomodel to the Neo4j database."""
    
    def __init__(self):
        """Load environment variables when the class is instantiated"""
        load_dotenv(override=True)
        
        self._is_connected = False
        
        # 1. Fetch as local variables
        URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687") 
        USER     = os.getenv("NEO4J_USER", "neo4j")
        PASSWORD = os.getenv("NEO4J_PASSWORD")

        # 2. Parse and encode
        encoded_password = urllib.parse.quote(PASSWORD)
        host_and_port    = URI.split("://")[-1]
        
        # 3. FIX: Use the local 'USER' variable, and save the final string to 'self'
        self.connection_url = f"bolt://{USER}:{encoded_password}@{host_and_port}"

    def connect_neomodel(self):
        """Authenticates and sets up the global neomodel connection."""
        if self._is_connected:
            print("Neomodel is already connected.")
            return

        try:
            # FIX: Use the instance variable we saved in __init__
            db.set_connection(self.connection_url)
            self._is_connected = True
            print("Successfully connected to Neo4j via Neomodel.")
        except Exception as e:
            print(f"Failed to connect Neomodel: {e}")
            raise