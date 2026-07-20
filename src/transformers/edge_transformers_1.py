from typing import Dict, Any
import pandas as pd

from src.config import ( 
    FRAMEWORK_CSV_PATH,
    SKILLS_CSV_PATH,
    KNOWLEDGE_CSV_PATH,
    COURSE_CSV_PATH,
    COMPETENCE_CSV_PATH,
    TASK_CSV_PATH
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





class GroupsTransformer(EdgeTransformer):
    DATA = {
        "groups": (COURSE_CSV_PATH, ['task_id', 'task_class_id'])
    }
  
    def execute(self, extracted_data):
        df = extracted_data["groups"].copy()
        df['groups_id'] = [f"g_{i}" for i in range(1, len(df) + 1)]
        return df 


class ProvidesTransformer(EdgeTransformer):
    DATA = {
        "provides": (COURSE_CSV_PATH, ['si_id', 'task_class_id'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = extracted_data["provides"].copy()
        df['provides_id'] = [f"p_{i}" for i in range(1, len(df) + 1)]
        return df


class OffersTransformer(EdgeTransformer):
    DATA = {
        "offers": (COURSE_CSV_PATH, ['pi_id', 'task_class_id'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = extracted_data["offers"].copy()
        df['offers_id'] = [f"o_{i}" for i in range(1, len(df) + 1)]
        return df


class IncludesTransformer(EdgeTransformer):
    DATA = {
        "includes": (COURSE_CSV_PATH, ['task_class_id', 'practice_id'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = extracted_data["includes"].copy()
        df = df.dropna(subset=['practice_id']).reset_index(drop=True)
        df['includes_id'] = [f"i_{i}" for i in range(1, len(df) + 1)]
        return df


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
    
    

    

class DevelopsTransformer():
    DATA = {
        "competence":
            (COMPETENCE_CSV_PATH, ['task_title', 'competence_id', 'competence_title']),
        "tasks":
            (TASK_CSV_PATH, ['id', 'name'])
    }

    def execute(self, extracted_data):
        tasks = (
            extracted_data["tasks"]
            .copy()
            .rename(columns={'id': 'original_id', 'name': 'task_title'})
            .assign(task_id=lambda df: df['task_title'].str[:2].str.upper())
        )
        
        # Load competence data
        competence = extracted_data["competence"].copy()
        
        # Merge
        # Note: Ensure task_title is unique in tasks to avoid row duplication
        merged_df = competence.merge(tasks, on='task_title', how='left')
        
        merged_df['develops_id'] = [f"dev_{i}" for i in range(1, len(merged_df) + 1)]

        return merged_df


class PracticesTransformer():
    # Define the data requirements for the extractor
    DATA = {
        "skill": (COMPETENCE_CSV_PATH, ['task_title', 'task_to_skill', 'skill_id']),
        "tasks": (TASK_CSV_PATH, ['id', 'name'])
    }

    def execute(self, extracted_data):
        # Process Tasks (Create the lookup table)
        tasks = (
            extracted_data["tasks"]
            .copy()
            .rename(columns={'id': 'original_id', 'name': 'task_title'})
            .assign(task_id=lambda df: df['task_title'].str[:2].str.upper())
        )

        # Process Competence & Merge
        df = (
            extracted_data["skill"]
            .copy()
            .rename(columns={'task_to_skill': 'cognitive_dimension'})
            .dropna(subset=['skill_id', 'cognitive_dimension'])
            # Inner merge ensures we only keep rows that have a matching task_id
            .merge(tasks, on='task_title', how='inner')
        )

        # Add unique identifier
        # Using a vectorized approach for speed
        df['practices_id'] = "prac_" + (df.index + 1).astype(str)

        return df


class AppliesTransformer():
    # Define the data requirements for the extractor
    DATA = {
        "knowledge": (COMPETENCE_CSV_PATH, ['task_title', 'needs_knowledge', 'knowledge_id']),
        "tasks": (TASK_CSV_PATH, ['id', 'name'])
    }

    def execute(self, extracted_data):
        # Process Tasks (Create the lookup table)
        tasks = (
            extracted_data["tasks"]
            .copy()
            .rename(columns={'id': 'original_id', 'name': 'task_title'})
            .assign(task_id=lambda df: df['task_title'].str[:2].str.upper())
        )

        # Process Knowledge & Merge
        df = (
            extracted_data["knowledge"]
            .copy()
            .rename(columns={'needs_knowledge': 'knowledge_dimension'})
            .dropna(subset=['knowledge_id', 'knowledge_dimension'])
            # Inner merge ensures we only keep rows that have a matching task_id
            .merge(tasks, on='task_title', how='inner')
        )

        # Add unique identifier
        # Using a vectorized approach for speed
        df['applies_id'] = "apl_" + (df.index + 1).astype(str)

        return df
