from src.database import GraphDB
from src.extractors.data_store import DataStore
from src.loaders.node_loader import load_nodes_to_neo4j
from src.loaders.edge_loader import load_edges_to_neo4j

import src.transformers as tf


# -------------------------------------------------------
#                     NODES
# -------------------------------------------------------

NODE_PIPELINE = [
    ("SKILL",                   tf.SkillTransformer),
    ("KNOWLEDGE",               tf.KnowledgeTransformer),
    ("COMPETENCE",              tf.CompetenceTransformer), 
    ("LEARNING_TASK",           tf.TaskTransformer),
    ("SUPPORTIVE_INFORMATION",  tf.SupportiveTransformer),
    ("PROCEDURAL_INFORMATION",  tf.ProceduralTransformer),
    ("LEARNING_SESSION",        tf.LearningSessionTransformer),
    ("STUDENT",                 tf.StudentTransformer),
    ("TASK_CLASS",              tf.TaskClassTransformer),
    ("PART_TASK_PRACTICE",      tf.PracticeTransformer)
]



def nodes_pipeline(db):
    """
    Converts raw data from CSV files using Transformers into Pydantic validated
    data and uploads nodes to Neo4j
    """
    print(f"\nStarting node pipeline for {len(NODE_PIPELINE)} node types...\n" + "-" * 40)
    
    try:
        for node_label, TransformerClass in NODE_PIPELINE:
            
            current_node   = node_label
            transformer    = TransformerClass()
            validated_data = transformer.execute()
            load_nodes_to_neo4j(db.driver, node_label, validated_data)

    except Exception as e:
        print(f"\nFATAL ERROR during {current_node} processing: {e}")
            
    finally:
        print("-" * 40 + "\nNode pipeline execution finished.\n")


# ---------------------------------------------------------
#                        EDGES
# ---------------------------------------------------------

EDGE_PIPELINE = [
    ("DEVELOPS_COMPETENCE", tf.DevelopsTransformer),
    ("PRACTICES_SKILL",     tf.PracticesTransformer),
    ("APPLIES_KNOWLEDGE",   tf.AppliesTransformer),
    ("ATTEMPTED",           tf.AttemptedTransformer),
    ("REQUIRES_SKILL",      tf.RequiresSTransformer),
    ("REQUIRES_KNOWLEDGE",  tf.RequiresKTransformer),
    ("GROUPS",              tf.GroupsTransformer),
    ("PROVIDES",            tf.ProvidesTransformer),
    ("OFFERS",              tf.OffersTransformer),
    ("INCLUDES",            tf.IncludesTransformer),
    ("TACKLED",             tf.TackledTransformer),
    ("REVIEWED",            tf.ReviewedTransformer),
    ("CONSULTED",           tf.ConsultedTransformer),
    ("STUDIED",             tf.StudiedTransformer),
    ("FINISHED",            tf.FinishedTransformer),
    ("CUES",                tf.CuesTransformer),
    ("REFERENCES",          tf.ReferencesTransformer),
    ("TRAINS",              tf.TrainsTransformer)
    ]






def edges_pipeline(db, data):
    """
    Loads edges into Neo4j
    """
    print(f"\n\nStarting edge pipeline for {len(EDGE_PIPELINE)} edge types...\n" + "-" * 40)
    try:
        for edge_label, TransformerClass in EDGE_PIPELINE:
            
            current_edge = edge_label
            try:
                transformer = TransformerClass(data)  # For updated transformers
            except TypeError:
                transformer = TransformerClass()       # For old transformers
            validated_data = transformer.execute()
            load_edges_to_neo4j(db.driver, edge_label, validated_data)
    except Exception as e:
        print(f"\nFATAL ERROR during {current_edge} processing: {e}")
    
    finally:
        print("-" * 40 + "\nEdge pipeline execution finished.\n")      
 



def main():
    db = GraphDB()
    data = DataStore()
   
    if db.driver is not None:
        try:
            # db.set_constraints()
            nodes_pipeline(db)
            edges_pipeline(db, data)
            
            # Print the model!
            # print(DEVELOPS_COMPETENCE.model_json_schema())

            
        finally:
            db.close()

if __name__=="__main__":
    main()
