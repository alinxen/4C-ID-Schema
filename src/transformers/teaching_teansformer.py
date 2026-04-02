import pandas as pd
from src.config import COMPETENCE_CSV_PATH, TASK_CSV_PATH
from src.schema import DEVELOPS_COMPETENCE, PRACTICES_SKILL, APPLIES_KNOWLEDGE, REQUIRES_SKILL, REQUIRES_KNOWLEDGE


class DevelopsTransformer():
    
    def execute(self):
        # Load competence data
        df = pd.read_csv(
            COMPETENCE_CSV_PATH, 
            usecols=['task_title', 'competence_id', 'competence_title']
        )
        
        # Load tasks
        tasks = (pd.read_csv(TASK_CSV_PATH, usecols=['id', 'name'], dtype={'id': str})
                 .rename(columns={'id': 'task_id', 'name': 'task_title'})
                 .assign(task_id=lambda df: df['task_title'].str[:2].str.upper()))
        
        # Merge
        df = df.merge(tasks, on='task_title', how='left')
        
        # Add a unique identifier to edge
        df['develops_id'] = [f"dev_{i}" for i in range(1, len(df) + 1)]

        validated_dev = []
        for _, row in df.iterrows():
            dev = DEVELOPS_COMPETENCE(**row.to_dict()) 
            validated_dev.append(dev.model_dump()) 
        
        return validated_dev




class PracticesTransformer():
    
    def execute(self):
        
        # Load skill/task data

        df = pd.read_csv(
            COMPETENCE_CSV_PATH, 
            usecols=['task_title', 'task_to_skill', 'skill_id'],
            dtype={'skill_id': str}
        )
        
        # Rename columns to map directly to the Pydantic model properties
        df = df.rename(columns={'task_to_skill': 'cognitive_dimension'})
        
        # Clean up: Drop rows where there isn't actually a skill mapped
        df = df.dropna(subset=['skill_id', 'cognitive_dimension'])

        # Load tasks: We need this to get the 'task_id'
        tasks = (pd.read_csv(TASK_CSV_PATH, usecols=['id', 'name'], dtype={'id': str})
                 .rename(columns={'id': 'task_id', 'name': 'task_title'})
                 .assign(task_id=lambda df: df['task_title'].str[:2].str.upper()))
        
        # Merge to attach task_id to our edge data
        df = df.merge(tasks, on='task_title', how='inner')
        
        # Add a unique identifier to the edge
        df['practices_id'] = [f"prac_{i}" for i in range(1, len(df) + 1)]

        # Validate through Pydantic
        validated_prac = []
        for _, row in df.iterrows():
            # Convert row to dict and pass it to the model
            prac = PRACTICES_SKILL(**row.to_dict()) 
            validated_prac.append(prac.model_dump()) 
            
        return validated_prac

class AppliesTransformer():
    
    def execute(self):
        
        # Load knowledge/task data

        df = pd.read_csv(
            COMPETENCE_CSV_PATH, 
            usecols=['task_title', 'needs_knowledge', 'knowledge_id'],
            dtype={'knowledge_id': str}
        )
        
        # Rename columns to map directly to the Pydantic model properties
        df = df.rename(columns={'needs_knowledge': 'knowledge_dimension'})
        
        # Clean up: Drop rows where there isn't actually a skill mapped
        df = df.dropna(subset=['knowledge_id', 'knowledge_dimension'])

        # Load tasks: We need this to get the 'task_id'
        tasks = (pd.read_csv(TASK_CSV_PATH, usecols=['id', 'name'], dtype={'id': str})
                 .rename(columns={'id': 'task_id', 'name': 'task_title'})
                 .assign(task_id=lambda df: df['task_title'].str[:2].str.upper()))
        
        # Merge to attach task_id to our edge data
        df = df.merge(tasks, on='task_title', how='inner')
        
        # Add a unique identifier to the edge
        df['applies_id'] = [f"apl_{i}" for i in range(1, len(df) + 1)]

        # Validate through Pydantic
        validated_prac = []
        for _, row in df.iterrows():
            # Convert row to dict and pass it to the model
            prac = APPLIES_KNOWLEDGE(**row.to_dict()) 
            validated_prac.append(prac.model_dump()) 
            
        return validated_prac

class RequiresSTransformer():
    
    def execute(self):
        df = pd.read_csv(
            COMPETENCE_CSV_PATH, 
            usecols=['skill_id', 'competence_id'],
            dtype={'skill_id': str}
        )
        df['requires_s_id'] = [f"req_s_{i}" for i in range(1, len(df) + 1)]
        validated_prac = []
        for _, row in df.iterrows():
            # Convert row to dict and pass it to the model
            prac = REQUIRES_SKILL(**row.to_dict()) 
            validated_prac.append(prac.model_dump()) 
            
        return validated_prac
    
class RequiresKTransformer():
    def execute(self):
        df = pd.read_csv(
            COMPETENCE_CSV_PATH, 
            usecols=['knowledge_id', 'competence_id'],
            dtype={'knowledge_id': str}
        )
        df['requires_k_id'] = [f"req_k_{i}" for i in range(1, len(df) + 1)]
        validated_prac = []
        for _, row in df.iterrows():
            # Convert row to dict and pass it to the model
            prac = REQUIRES_KNOWLEDGE(**row.to_dict()) 
            validated_prac.append(prac.model_dump()) 
            
        return validated_prac