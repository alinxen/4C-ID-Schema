import pandas as pd
from src.config import TASK_CSV_PATH, HVP_CSV_PATH, PAGES_CSV_PATH, COURSE_CSV_PATH
from src.schema import LEARNING_TASK, SUPPORTIVE_INFORMATION, PROCEDURAL_INFORMATION, TASK_CLASS, PART_TASK_PRACTICE


class TaskTransformer():
    """
    Liest Lernaufgaben und HVP-Bibliotheken ein, führt sie zusammen,
    bereinigt fehlende Werte und validiert sie über ein Pydantic-Schema.
    """
    def execute(self):
        # Learning Tasks einlesen
        tasks = (
            pd.read_csv(TASK_CSV_PATH, usecols=['id', 'course', 'name', 'main_library_id'], dtype={'id': str})
            .rename(columns={'id': 'task_id','course': 'course_id', 'name':'task_title'})
            .assign(task_id=lambda df: df['task_title'].str[:2].str.upper())
        )
        # HVP-Namen einlesen 
        hvp = (
            pd.read_csv(HVP_CSV_PATH, usecols=['id', 'title'])
            .rename(columns={'id': 'main_library_id','title':'task_type'})
        )
        # Beide Tabellen anhand der 'task_id' verknüpfen 
        merged_tasks = tasks.merge(hvp, on="main_library_id", how="left")
        # NaN-Werte in None-Werte umwandeln, da Pydantic sonst abstürzt
        merged_tasks = merged_tasks.where(pd.notna(merged_tasks), None)
        # Mit Pydantic validieren
        validated_tasks = [
            LEARNING_TASK(**row).model_dump() 
            for row in merged_tasks.to_dict(orient='records')
        ]
        return validated_tasks
    
class SupportiveTransformer():
    
    def execute(self):
        pages = (pd.read_csv(PAGES_CSV_PATH, usecols=['id', 'course', 'name'], dtype={'id': str})
                 .rename(columns={'id':'si_id', 'course': 'course_id', 'name':'si_title'}))
                 
        # Ensure si_id is read as a string here as well to avoid type conflicts
        mapping = pd.read_csv(COURSE_CSV_PATH, usecols=['si_id','supportive_title'], dtype={'si_id': str})
        
        # 1. Create a fast dictionary mapping: { 'supportive_title': 'si_id' }
        title_to_id_map = mapping.set_index('supportive_title')['si_id'].to_dict()
        
        
        # Filter for supportive info and reset index
        # Use .copy() to avoid SettingWithCopyWarning down the line
        pages_supportive = pages[pages['si_title'].str.startswith("(SI)", na=False)].copy()
        pages_supportive['si_id'] = pages_supportive['si_title'].map(title_to_id_map).fillna(pages['si_id'])

        pages_supportive.reset_index(drop=True, inplace=True)
        
        # 3. Serialize through Pydantic
        validated_supportive = [
            SUPPORTIVE_INFORMATION(**row).model_dump() 
            for row in pages_supportive.to_dict(orient='records')
        ]
        
        return validated_supportive
    
class ProceduralTransformer():

    def execute(self):
        pages = (pd.read_csv(PAGES_CSV_PATH, usecols=['id', 'course', 'name'], dtype={'id': str})
                 .rename(columns={'id':'pi_id', 'course': 'course_id', 'name':'pi_title'}))
                 
        # 1. FIXED: Ensure usecols, dtype, and the map all reference the same ID column ('pi_id')
        mapping = pd.read_csv(COURSE_CSV_PATH, usecols=['pi_id','procedural_title'], dtype={'pi_id': str})
        
        
        # Create a fast dictionary mapping: { 'procedural_title': 'pi_id' }
        title_to_id_map = mapping.set_index('procedural_title')['pi_id'].to_dict()
        
        # Filter for procedural info and copy
        pages_procedural = pages[pages['pi_title'].str.startswith("(PI)", na=False)].copy()
        
        # 2. FIXED: Map the IDs and fillna using the local pages_procedural dataframe
        pages_procedural['pi_id'] = pages_procedural['pi_title'].map(title_to_id_map).fillna(pages_procedural['pi_id'])

        pages_procedural.reset_index(drop=True, inplace=True)
        
        # 3. Serialize through Pydantic
        validated_procedural = [
            PROCEDURAL_INFORMATION(**row).model_dump() 
            for row in pages_procedural.to_dict(orient='records')
        ]

        return validated_procedural
 
    
 
    
class TaskClassTransformer():
    
    def execute(self):
        df = pd.read_csv(COURSE_CSV_PATH, usecols=['task_class_id','task_class'])
        validated_class = [
            TASK_CLASS(**row).model_dump() 
            for row in df.to_dict(orient='records')
        ]
        return validated_class
    
    
    
    
class PracticeTransformer():
    
    def execute(self):
        df = pd.read_csv(COURSE_CSV_PATH, usecols=['practice_title','practice_id'])
        df = df.dropna(subset=['practice_title']).reset_index(drop=True)
        validated_practice = [
            PART_TASK_PRACTICE(**row).model_dump() 
            for row in df.to_dict(orient='records')
        ]
        return validated_practice    
    
    
    
    
