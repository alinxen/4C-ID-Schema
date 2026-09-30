from typing import Dict, Any
import pandas as pd

from src.config import ( 
    FRAMEWORK_CSV_PATH,
    TARGET_CSV_PATH,
    SKILLS_CSV_PATH,
    KNOWLEDGE_CSV_PATH,
    COURSE_CSV_PATH,
    COMPETENCE_CSV_PATH,
    TASK_CSV_PATH,
    CLASSES_CSV_PATH,
    PTP_CSV_PATH,
    INFORMATION_CSV_PATH
)

# ---------------------------------------------------------
#                 BASE CLASS
# ---------------------------------------------------------

class EdgeTransformer:
    """
    Base class for all edge transformers to enforce consistency.
    """
    DATA = {}

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Default behavior for single-source transformers: Just return the data.
        """
        return next(iter(extracted_data.values())).copy()

# ---------------------------------------------------------
#                Edge/Node Transformers
# ---------------------------------------------------------

class RequiresSTransformer():
    DATA = {
        "connections": (FRAMEWORK_CSV_PATH, ['source_id', 'target_id', 'connection_type']),
        "skills_info": (SKILLS_CSV_PATH, ['skill_id', 'skill_priority'])
    }
    
    def execute(self, extracted_data):
        df_connections = extracted_data["connections"].copy()
        df_skills = extracted_data["skills_info"].copy()
        df = df_connections[df_connections['connection_type'] == 'competence-skill']
        df = df.drop(columns=['connection_type'])
        df = df.merge(
            df_skills[['skill_id', 'skill_priority']], 
            how='left', 
            left_on='target_id',   # The column in your connections frame
            right_on='skill_id'    # The column in your skills frame
        )
        df = df.drop(columns=['skill_id'])
        df = df.reset_index(drop=True)
        df['requires_s_id'] = [f"req_s_{i}" for i in range(1, len(df) + 1)]
        return df
    
class RequiresKTransformer():
    DATA = {
        "connections": (FRAMEWORK_CSV_PATH, ['source_id', 'target_id', 'connection_type']),
        "knowledge_info": (KNOWLEDGE_CSV_PATH, ['knowledge_id', 'knowledge_priority'])
    }
    
    def execute(self, extracted_data):
        df_connections = extracted_data["connections"].copy()
        df_knowledge = extracted_data["knowledge_info"].copy()
        df = df_connections[df_connections['connection_type'] == 'competence-knowledge']
        df = df.drop(columns=['connection_type'])
        df = df.merge(
            df_knowledge[['knowledge_id', 'knowledge_priority']], 
            how='left', 
            left_on='target_id',   # The column in your connections frame
            right_on='knowledge_id'    # The column in your skills frame
        )
        df = df.drop(columns=['knowledge_id'])
        df = df.reset_index(drop=True)
        df['requires_k_id'] = [f"req_k_{i}" for i in range(1, len(df) + 1)]
        return df


class DevelopsTransformer():
    DATA = {
        "target":
            (TARGET_CSV_PATH, ['task_id', 'competence_id']),
    }

    def execute(self, extracted_data):
        # Load competence data
        develops = (extracted_data["target"]
                    .copy()
                    .rename(columns={'task_id': 'source_id', 'competence_id': 'target_id'})
                    )

        develops['develops_id'] = [f"dev_{i}" for i in range(1, len(develops) + 1)]
        return develops


class PracticesTransformer():
    DATA = {
        "target":
            (TARGET_CSV_PATH, ['task_id', 'skill_id','cognitive_process']),
    }

    def execute(self, extracted_data):
        # Load competence data
        df = (extracted_data["target"]
                    .copy()
                    .rename(columns={'task_id': 'source_id', 'skill_id': 'target_id'})
                    )

        df['practices_id'] = "prac_" + (df.index + 1).astype(str)
        return df


class AppliesTransformer():
    DATA = {
        "target":
            (TARGET_CSV_PATH, ['task_id', 'knowledge_id','knowledge_dimension']),
    }

    def execute(self, extracted_data):
        # Load competence data
        df = (extracted_data["target"]
                    .copy()
                    .rename(columns={'task_id': 'source_id', 'knowledge_id': 'target_id'})
                    )

        df['applies_id'] = "apl_" + (df.index + 1).astype(str)
        return df

class GroupsTransformer(EdgeTransformer):
    DATA = {
        "groups": (CLASSES_CSV_PATH, ['task_class_bool', 'id','task_sequence'])
    }
  
    def execute(self, extracted_data):
        df = extracted_data["groups"].copy()
        filtered_df = df[df['task_class_bool'].astype(int) == 1].copy()
        filtered_df = filtered_df.dropna(subset=['task_sequence'])
        filtered_df['target_id'] = filtered_df['task_sequence'].str.split(',')
        edges_df = filtered_df.explode('target_id')
        edges_df['target_id'] = edges_df['target_id'].str.strip()
        edges_df = edges_df.rename(columns={'id': 'source_id'})
        result_df = edges_df[['source_id', 'target_id','task_sequence']].reset_index(drop=True)
        result_df['groups_id'] = [f"g_{i}" for i in range(1, len(result_df) + 1)]
        return result_df
    
class IncludesTransformer(EdgeTransformer):
    DATA = {
        "includes": (PTP_CSV_PATH, ['task_class_id', 'practice_id'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = (extracted_data["includes"]
              .copy()
              .rename(columns={'task_class_id': 'source_id', 'practice_id': 'target_id'})
              )
        df = df.dropna(subset=['target_id']).reset_index(drop=True)
        df['includes_id'] = [f"i_{i}" for i in range(1, len(df) + 1)]
        return df
    
class ProvidesTransformer(EdgeTransformer):
    DATA = {
        "provides": (INFORMATION_CSV_PATH, ['id', 'task_class_id','type'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = (extracted_data["provides"]
              .copy()
              .rename(columns={'task_class_id': 'source_id', 'id': 'target_id'})
              )
        df = df[df['type'] == 'longpage']
        df = df.dropna(subset=['target_id']).reset_index(drop=True)
        df['source_id'] = df['source_id'].str.split(',')
        df = df.explode('source_id')
        df['source_id'] = df['source_id'].str.strip()
        df = df.dropna(subset=['source_id']).reset_index(drop=True)
        df['provides_id'] = [f"p_{i}" for i in range(1, len(df) + 1)]
        return df


class OffersTransformer(EdgeTransformer):
    DATA = {
        "offers": (INFORMATION_CSV_PATH, ['id', 'task_class_id','type'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = (extracted_data["offers"]
              .copy()
              .rename(columns={'task_class_id': 'source_id', 'id': 'target_id'})
              )
        df = df[df['type'] == 'page']
        df = df.dropna(subset=['target_id']).reset_index(drop=True)
        df['offers_id'] = [f"o_{i}" for i in range(1, len(df) + 1)]
        return df
    
#################################################










class CuesTransformer(EdgeTransformer):
    DATA = {
        "cues": (COURSE_CSV_PATH, ['task_id', 'pi_id'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = extracted_data["cues"].copy()
        df = df.dropna(subset=['pi_id']).reset_index(drop=True)
        df['cues_id'] = [f"cue_{i}" for i in range(1, len(df) + 1)]
        return df


class ReferencesTransformer(EdgeTransformer):
    DATA = {
        "references": (COURSE_CSV_PATH, ['task_id', 'si_id'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = extracted_data["references"].copy()
        df = df.dropna(subset=['si_id']).reset_index(drop=True)
        df['references_id'] = [f"ref_{i}" for i in range(1, len(df) + 1)]
        return df


class TrainsTransformer(EdgeTransformer):
    DATA = {
        "trains": (COURSE_CSV_PATH, ['practice_id', 'pi_id'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = extracted_data["trains"].copy()
        df = df.dropna(subset=['practice_id']).reset_index(drop=True)
        df['trains_id'] = [f"tra_{i}" for i in range(1, len(df) + 1)]
        return df
    
    

    

