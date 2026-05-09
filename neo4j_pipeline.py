from src.database import GraphDB
from src.loaders.graph_loader          import GraphLoader
from src.extractors.data_extractor     import DataExtractor
from src.validators.pydantic_validator import PydanticValidator
import traceback

import src.transformers as tf




# -------------------------------------------------------
#                     NODES
# -------------------------------------------------------

NODE_PIPELINE = [
    ("COMPETENCE",             tf.CompetenceTransformer),
    ("KNOWLEDGE",              tf.KnowledgeTransformer),
    ("LEARNING_SESSION",       tf.LearningSessionTransformer),
    ("LEARNING_TASK",          tf.TaskTransformer),
    ("PART_TASK_PRACTICE",     tf.PracticeTransformer),
    ("PROCEDURAL_INFORMATION", tf.ProceduralTransformer),
    ("SKILL",                  tf.SkillTransformer),
    ("STUDENT",                tf.StudentTransformer),
    ("SUPPORTIVE_INFORMATION", tf.SupportiveTransformer),
    ("TASK_CLASS",             tf.TaskClassTransformer)
]

# ---------------------------------------------------------
#                        EDGES
# ---------------------------------------------------------

EDGE_PIPELINE = [
    ("APPLIES_KNOWLEDGE",   tf.AppliesTransformer),
    ("ATTEMPTED",           tf.AttemptedTransformer),
    ("CONSULTED",           tf.ConsultedTransformer),
    ("CUES",                tf.CuesTransformer),
    ("DEVELOPS_COMPETENCE", tf.DevelopsTransformer),
    ("FINISHED",            tf.FinishedTransformer),
    ("GROUPS",              tf.GroupsTransformer),
    ("INCLUDES",            tf.IncludesTransformer),
    ("OFFERS",              tf.OffersTransformer),
    ("PRACTICES_SKILL",     tf.PracticesTransformer),
    ("PROVIDES",            tf.ProvidesTransformer),
    ("REFERENCES",          tf.ReferencesTransformer),
    ("REQUIRES_KNOWLEDGE",  tf.RequiresKTransformer),
    ("REQUIRES_SKILL",      tf.RequiresSTransformer),
    ("REVIEWED",            tf.ReviewedTransformer),
    ("STUDIED",             tf.StudiedTransformer),
    ("TACKLED",             tf.TackledTransformer),
    ("TRAINS",              tf.TrainsTransformer)
]

# ---------------------------------------------------------
#                        PIPELINE
# ---------------------------------------------------------

def etvl_pipeline(db, entity_type, PIPELINE):
    """
    Converts raw data from CSV files using Transformers into Pydantic validated
    data and uploads nodes to Neo4j
    """
    report = []
    
    for label, TransformerClass in PIPELINE:
        try:
            extractor        = DataExtractor(TransformerClass.DATA)
            extracted_data   = extractor.extract()
                                 
            transformer      = TransformerClass()
            transformed_data = transformer.execute(extracted_data)
                                 
            validator        = PydanticValidator(label)
            validated_data   = validator.validate(transformed_data)
                                 
            loader           = GraphLoader(db.driver)
            results          = loader.load(entity_type, label, validated_data)
                
            report.append(results)
    
        except Exception as e:
            print(f"\nERROR while processing {label}: {e}") 
            error_details = traceback.format_exc()
            print(f"\nFULL ERROR TRACEBACK for {label}:\n{error_details}")
            report.append([label, "failed", "N/A"])
            continue
   
    return report



def main():
    db = GraphDB()
    #data = DataStore()
   
    if db.driver is not None:
        try:
            # ---------------------------------------------------------
            #                        NODES
            # ---------------------------------------------------------
            print(f"\nStarting node pipeline for {len(NODE_PIPELINE)} node types...\n" + "-" * 40)
            results = etvl_pipeline(db, "node" , NODE_PIPELINE)
            
            print(f"\n{'NODES':<30} | {'NEW':<8} | {'TOTAL':<8}")
            print(f"{'-'*55}")
            
            for row in results:
                # row[0] is Label, row[1] is New, row[2] is Total
                print(f"{row[0]:<30} | {row[1]:<8} | {row[2]:<8}")
            
            print(f"{'='*55}\n")
            print("-" * 40 + "\nNode pipeline execution finished.\n")
            
            
            # ---------------------------------------------------------
            #                        EDGES
            # ---------------------------------------------------------
            print(f"\n\nStarting edge pipeline for {len(EDGE_PIPELINE)} edge types...\n" + "-" * 40)
            results = etvl_pipeline(db, "edge", EDGE_PIPELINE)
            
            
            print(f"\n{'EDGES':<30} | {'NEW':<8} | {'TOTAL':<8}")
            print(f"{'-'*55}")
            
            for row in results:
                # row[0] is Label, row[1] is New, row[2] is Total
                print(f"{row[0]:<30} | {row[1]:<8} | {row[2]:<8}")
            
            print(f"{'='*55}\n")
            print("-" * 40 + "\nEdge pipeline execution finished.\n")                


            
        finally:
            db.close()

if __name__=="__main__":
    main()
