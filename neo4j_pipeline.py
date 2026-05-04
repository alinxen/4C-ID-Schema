from src.database import GraphDB
from src.loaders.graph_loader          import GraphLoader
from src.extractors.data_extractor     import DataExtractor
from src.validators.pydantic_validator import PydanticValidator


import src.transformers as tf




# -------------------------------------------------------
#                     NODES
# -------------------------------------------------------

NODE_PIPELINE = [
    ("SKILL",                   tf.SkillTransformer),
    ("STUDENT",                 tf.StudentTransformer),
    ("KNOWLEDGE",               tf.KnowledgeTransformer),
    ("TASK_CLASS",              tf.TaskClassTransformer),
    ("COMPETENCE",              tf.CompetenceTransformer), 
    ("LEARNING_TASK",           tf.TaskTransformer),
    ("LEARNING_SESSION",        tf.LearningSessionTransformer),
    ("PART_TASK_PRACTICE",      tf.PracticeTransformer),
    ("SUPPORTIVE_INFORMATION",  tf.SupportiveTransformer),
    ("PROCEDURAL_INFORMATION",  tf.ProceduralTransformer)
]

# ---------------------------------------------------------
#                        EDGES
# ---------------------------------------------------------

EDGE_PIPELINE = [
    ("CUES",                tf.CuesTransformer),
    ("TRAINS",              tf.TrainsTransformer),
    ("OFFERS",              tf.OffersTransformer),
    ("GROUPS",              tf.GroupsTransformer),
    ("PROVIDES",            tf.ProvidesTransformer),
    ("INCLUDES",            tf.IncludesTransformer),
    ("ATTEMPTED",           tf.AttemptedTransformer),
    ("REFERENCES",          tf.ReferencesTransformer),
    ("REQUIRES_SKILL",      tf.RequiresSTransformer),
    ("PRACTICES_SKILL",     tf.PracticesTransformer),
    ("APPLIES_KNOWLEDGE",   tf.AppliesTransformer),
    ("REQUIRES_KNOWLEDGE",  tf.RequiresKTransformer),
    ("DEVELOPS_COMPETENCE", tf.DevelopsTransformer),

  #  ("TACKLED",             tf.TackledTransformer),
   # ("STUDIED",             tf.StudiedTransformer),
   # ("FINISHED",            tf.FinishedTransformer),
   # ("REVIEWED",            tf.ReviewedTransformer),
   # ("CONSULTED",           tf.ConsultedTransformer),
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
            
            print(f"\n{'NODES':<30} | {'NEW':<8} | {'EXISTING':<8}")
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
            
            
            print(f"\n{'EDGES':<30} | {'NEW':<8} | {'EXISTING':<8}")
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
