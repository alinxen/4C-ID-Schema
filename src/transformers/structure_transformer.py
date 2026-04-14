import pandas as pd
from src.schema import GROUPS, PROVIDES, OFFERS, INCLUDES, CUES, REFERENCES, TRAINS
from src.config import COURSE_CSV_PATH


class GroupsTransformer():
    def execute(self):
        df = pd.read_csv(COURSE_CSV_PATH, usecols=['task_id', 'task_class_id'])
        df['groups_id'] = [f"g_{i}" for i in range(1, len(df) + 1)]
        validated_data = [
            GROUPS(**row).model_dump() 
            for row in df.to_dict(orient='records')
        ]
        return validated_data  
    
class ProvidesTransformer():
    def execute(self):
        df = pd.read_csv(COURSE_CSV_PATH, usecols=['si_id', 'task_class_id'])
        df['provides_id'] = [f"p_{i}" for i in range(1, len(df) + 1)]
        validated_data = [
            PROVIDES(**row).model_dump() 
            for row in df.to_dict(orient='records')
        ]
        return validated_data  
    
class OffersTransformer():
    def execute(self):
        df = pd.read_csv(COURSE_CSV_PATH, usecols=['pi_id', 'task_class_id'])
        df['offers_id'] = [f"o_{i}" for i in range(1, len(df) + 1)]
        validated_data = [
            OFFERS(**row).model_dump() 
            for row in df.to_dict(orient='records')
        ]
        return validated_data  
    
class IncludesTransformer():
    def execute(self):
        df = pd.read_csv(COURSE_CSV_PATH, usecols=['task_class_id', 'practice_id'])
        df = df.dropna(subset=['practice_id']).reset_index(drop=True)
        df['includes_id'] = [f"i_{i}" for i in range(1, len(df) + 1)]
        validated_data = [
            INCLUDES(**row).model_dump() 
            for row in df.to_dict(orient='records')
        ]
        return validated_data  
    
class CuesTransformer():
    def execute(self):
        df = pd.read_csv(COURSE_CSV_PATH, usecols=['task_id', 'pi_id'])
        df = df.dropna(subset=['pi_id']).reset_index(drop=True)
        df['cues_id'] = [f"cue_{i}" for i in range(1, len(df) + 1)]
        validated_data = [
            CUES(**row).model_dump() 
            for row in df.to_dict(orient='records')
        ]
        return validated_data  
    
class ReferencesTransformer():
    def execute(self):
        df = pd.read_csv(COURSE_CSV_PATH, usecols=['task_id', 'si_id'])
        df = df.dropna(subset=['si_id']).reset_index(drop=True)
        df['references_id'] = [f"ref_{i}" for i in range(1, len(df) + 1)]
        validated_data = [
            REFERENCES(**row).model_dump() 
            for row in df.to_dict(orient='records')
        ]
        return validated_data  
    
class TrainsTransformer():
    def execute(self):
        df = pd.read_csv(COURSE_CSV_PATH, usecols=['practice_id', 'pi_id'])
        df = df.dropna(subset=['practice_id']).reset_index(drop=True)
        df['trains_id'] = [f"tra_{i}" for i in range(1, len(df) + 1)]
        
        validated_data = [
            TRAINS(**row).model_dump() 
            for row in df.to_dict(orient='records')
        ]
        
        return validated_data  
    
    