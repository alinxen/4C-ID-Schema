from typing import Dict, Any

import pandas as pd

from src.config import ( 
    EXCLUDED_USER_IDS,
    COMPETENCE_CSV_PATH,
    SKILLS_CSV_PATH,
    KNOWLEDGE_CSV_PATH,
    COURSE_CSV_PATH,
    HVP_CSV_PATH,
    LOGFILE_CSV_PATH,
    PAGES_CSV_PATH,
    TASK_CSV_PATH,
    CLASSES_CSV_PATH
)


# ---------------------------------------------------------
#                    BASE CLASS
# ---------------------------------------------------------

class NodeTransformer:
    """
    Base class for all node transformers to enforce consistency.
    """
    DATA = {}

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Default behavior for single-source transformers: Just return the data.
        """
        return next(iter(extracted_data.values())).copy()

# ---------------------------------------------------------
#                  Node Transformers
# ---------------------------------------------------------

class CompetenceTransformer(NodeTransformer):
    """Transforms and maps competence definitions."""
    DATA = {
        "competence": (COMPETENCE_CSV_PATH,['competence_id', 'competence_title', 'competence_description', 'competence_group_id','competence_group'])
    }
     
class SkillTransformer(NodeTransformer):
    """Transforms and maps skill definitions."""
    DATA = {
        "skills": (SKILLS_CSV_PATH, ['skill_id', 'skill_title', 'skill_description', 'skill_group_id', 'skill_group_title'])
    }

class KnowledgeTransformer(NodeTransformer):
    """Transforms and maps knowledge definitions."""
    DATA = {
        "knowledge": (KNOWLEDGE_CSV_PATH, ['knowledge_id', 'knowledge_title', 'knowledge_description', 'knowledge_group_id', 'knowledge_group_title'])
    }

class TaskTransformer(NodeTransformer):
    """
    Reads learning tasks and HVP libraries, merges them, handles 
    missing values, and formats them for Pydantic validation.
    """
    DATA = {
        "tasks": (TASK_CSV_PATH, ['module_id','task_id','task_title','task_type','max_points','task_description']), 
        "hvp":   (HVP_CSV_PATH, ['name', 'main_library_id'])
    }
        

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        tasks = extracted_data["tasks"].copy()

        hvp = extracted_data["hvp"].copy()
        hvp = hvp.rename(columns={'name': 'task_title'})
        
        merged_tasks = tasks.merge(hvp, on="task_title", how="left")
        merged_tasks = merged_tasks.dropna(subset=['task_id', 'task_title'])
        return merged_tasks

class StudentTransformer(NodeTransformer):
    """
    Loads all user information from user CSV
    """
    DATA = {
        "user": (LOGFILE_CSV_PATH, ['userid', 'crud', 'edulevel','timecreated'])
    }
    
    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = extracted_data["user"].copy()
        df = df.rename(columns={'userid': 'student_id'})
        
        # Filter out teachers and admins
        df = df[~df['student_id'].isin(EXCLUDED_USER_IDS)]

        # Aggregate crud and edulevels per student
        df_aggregated = df.groupby('student_id', as_index=False).agg(
            crud=('crud', lambda x: ''.join(sorted(x.dropna().astype(str).unique(), key=lambda v: {'c': 1, 'r': 2, 'u': 3, 'd': 4}.get(v, 5)))),
            edulevels=('edulevel', lambda x: '-'.join(sorted(x.dropna().astype(str).unique()))),
            first_active=('timecreated', 'min'),
            total_events=('student_id', 'count')
        )
        
        # Convert Unix timestamp to readable datetime and adjust timezone
        df_aggregated['first_active'] = pd.to_datetime(df_aggregated['first_active'], unit='s', utc=True)
        df_aggregated['first_active'] = df_aggregated['first_active'].dt.tz_convert('Europe/Berlin')
        df_aggregated['first_active'] = df_aggregated['first_active'].dt.tz_localize(None)
        return df_aggregated

class LearningSessionTransformer(NodeTransformer):
    """
    Reads the raw logfile, calculates sessions for all students,
    and returns a clean list of validated Pydantic dictionaries.
    """
    DATA = {
        "logfile": (LOGFILE_CSV_PATH,  ['userid', 'timecreated', 'action'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        """Extract and validate data."""
        df_raw = extracted_data["logfile"].copy()
        df_clean = self._prepare_data(df_raw)
        learning_sessions = self._process_user_sessions(df_clean)
        return pd.DataFrame(learning_sessions)

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adjust timezone, sort chronologically, and remove system/admin accounts."""
        
        # Convert Unix timestamp to readable datetime and adjust timezone
        df['timecreated'] = pd.to_datetime(df['timecreated'], unit='s', utc=True)
        df['timecreated'] = df['timecreated'].dt.tz_convert('Europe/Berlin')
        df['timecreated'] = df['timecreated'].dt.tz_localize(None)
        
        df = df.sort_values(by=['userid', 'timecreated']).reset_index(drop=True)
               
        # Filter out teachers and admins
        df = df[~df['userid'].isin(EXCLUDED_USER_IDS)]
        
        return df

    def _process_user_sessions(self, df: pd.DataFrame) -> list:
        """
        Groups events into sessions based on a 30-minute inactivity threshold 
        using vectorized Pandas operations.
        """
        # Calculate time gaps and session boundaries
        df['time_gap'] = df.groupby('userid')['timecreated'].diff()
        is_new_session = df['time_gap'] > pd.Timedelta(minutes=30)
        is_first_event = df['time_gap'].isna()
        df['session_idx'] = (is_new_session | is_first_event).cumsum()
        
        # Group by user and the new session index to get exact start and end boundaries
        sessions_df = df.groupby(['userid', 'session_idx']).agg(
            start_time=('timecreated', 'min'),
            end_time=('timecreated', 'max'),
            total_actions=('action', 'count')
        ).reset_index()
        
        # Drop sessions where the student only clicked once
        sessions_df = sessions_df[sessions_df['start_time'] != sessions_df['end_time']].copy()
        
        # Alternative: Handle "single-click" sessions (where start == end) by adding a 2-minute buffer
        #single_event_mask = sessions_df['start_time'] == sessions_df['end_time']
        #sessions_df.loc[single_event_mask, 'end_time'] += pd.Timedelta(minutes=2)
        #sessions_df['session_duration'] = (sessions_df['end_time'] - sessions_df['start_time']).dt.total_seconds().astype(int)
        
        # Format output into the final list of dictionaries
        learning_sessions = []
        for row in sessions_df.itertuples():
            learning_sessions.append({
                "session_id": f"session_{row.session_idx}",
                "student_id": row.userid,
                "start_time": row.start_time, 
                "end_time":   row.end_time,
                "total_actions": row.total_actions
            })
            
        return learning_sessions
    
class TaskClassTransformer(NodeTransformer):
    """Extracts task class definitions from the course data."""
    DATA = {
        "taskclass": (CLASSES_CSV_PATH, ['section_id','task_class_bool','id','name','description'])
    }

    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = extracted_data["taskclass"].copy()
        filtered_df = df[df['task_class_bool'].astype(int) == 1]

        task_classes = []
        for row in filtered_df.itertuples(index=False):
            task_classes.append({
                "section_id": int(row.section_id),
                "task_class_id": row.id,
                "task_class": row.name,
                "class_description": row.description
            })
            
        return pd.DataFrame(task_classes)






















###########################################################################




                

class PracticeTransformer(NodeTransformer):
    """Extracts practice entries, dropping any with missing IDs."""
    DATA = {
        "practice": (COURSE_CSV_PATH, ['practice_title', 'practice_id'])
    }
    
    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        df = extracted_data["practice"].copy()
        df = df.dropna(subset=['practice_id'])
        return df
        
        




    

class SupportiveTransformer(NodeTransformer):
    """
    Extracts supportive information from Moodle pages and maps them 
    to the internal SI IDs defined in the course blueprint.
    """
    DATA = {
        "pages":   (PAGES_CSV_PATH,  ['id', 'course', 'name']),
        "mapping": (COURSE_CSV_PATH, ['si_id', 'supportive_title'])
    }
                 
    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        pages = extracted_data["pages"].copy()
        pages = pages.rename(columns={'id': 'moodle_id', 'course': 'course_id', 'name': 'si_title'})
        pages['moodle_id'] = pages['moodle_id'].astype(str)
        
        mapping = extracted_data["mapping"].copy()
        
        # Drop empty rows and ensure ID is string
        mapping = mapping.dropna(subset=['supportive_title', 'si_id'])
        title_to_id_map = mapping.set_index('supportive_title')['si_id'].astype(str).to_dict()
        
        # Filter for Supportive Information (SI) entries only
        pages_supportive = pages[pages['si_title'].str.startswith("(SI)", na=False)].copy()
        
        # Perform ID Mapping (fallback to original Moodle ID if not found)
        pages_supportive['si_id'] = (
            pages_supportive['si_title']
            .map(title_to_id_map)
            .fillna(pages_supportive['moodle_id'].astype(str))
        )
        
        pages_supportive.reset_index(drop=True, inplace=True)
        return pages_supportive
    
    
class ProceduralTransformer(NodeTransformer):
    """
    Extracts procedural information from Moodle pages and maps them 
    to the internal PI IDs defined in the course blueprint.
    """
    DATA = {
        "pages":   (PAGES_CSV_PATH,  ['id', 'course', 'name']),
        "mapping": (COURSE_CSV_PATH, ['pi_id', 'procedural_title'])
    }
    
    def execute(self, extracted_data: Dict[str, Any]) -> pd.DataFrame:
        pages = extracted_data["pages"].copy()
        pages = pages.rename(columns={'id': 'moodle_id', 'course': 'course_id', 'name': 'pi_title'})
        pages['moodle_id'] = pages['moodle_id'].astype(str)
        
        mapping = extracted_data["mapping"].copy()
        
        # Drop empty rows and ensure ID is string
        mapping = mapping.dropna(subset=['procedural_title', 'pi_id'])
        title_to_id_map = mapping.set_index('procedural_title')['pi_id'].astype(str).to_dict()
        
        # Filter for Procedural Information (PI) entries only
        pages_procedural = pages[pages['pi_title'].str.startswith("(PI)", na=False)].copy()
        
        # Perform ID Mapping (fallback to original Moodle ID if not found)
        pages_procedural['pi_id'] = (
            pages_procedural['pi_title']
            .map(title_to_id_map)
            .fillna(pages_procedural['moodle_id'].astype(str))
        )
        
        pages_procedural.reset_index(drop=True, inplace=True)
        return pages_procedural

 
