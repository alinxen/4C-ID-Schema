import pandas as pd
from datetime import timedelta


from src.config import ( 
    COMPETENCE_CSV_PATH, 
    USER_CSV_PATH, 
    COURSE_CSV_PATH,
    TASK_CSV_PATH,
    HVP_CSV_PATH,
    PAGES_CSV_PATH,
    LOGFILE_CSV_PATH
    )


class NodeTransformer:
    """
    Base class for all node transformers to enforce consistentcy
    """
    DATA = {}

    def execute(self, extracted_data):
        """
        Default behavior for single-source transformers:
        Just return the data
        """
        
        return next(iter(extracted_data.values())).copy()
    
###############################################################################

class SkillTransformer(NodeTransformer):
    DATA = {"skills": 
                (COMPETENCE_CSV_PATH, ['skill_id', 'skill_title', 'skill_group_id', 'skill_group_title'])
                }


class KnowledgeTransformer(NodeTransformer):
    DATA = {"knowledge": 
                (COMPETENCE_CSV_PATH, ['knowledge_id', 'knowledge_title', 'knowledge_group_id', 'knowledge_group_title'])
                }


class CompetenceTransformer(NodeTransformer):
    DATA = {"competence": 
                (COMPETENCE_CSV_PATH, ['competence_id', 'competence_title', 'competence_group_id', 'competence_group'])
                }


class TaskClassTransformer(NodeTransformer):
    DATA = {"taskclass":
                (COURSE_CSV_PATH, ['task_class_id','task_class'])
                }
    
                
class PracticeTransformer(NodeTransformer):
    DATA = {"practice":
                (COURSE_CSV_PATH, ['practice_title','practice_id'])
                }
    
    def execute(self, extracted_data):
        df = extracted_data["practice"].copy()
        # Drop rows where the ID is missing
        df = df.dropna(subset=['practice_id'])
        return df
        
        
        
class StudentTransformer(NodeTransformer):
    """
    Loads all user information from m_user.csv and filters to only allow
    students (student_id >=3)
    """
    DATA = {"user": 
                (USER_CSV_PATH, ['id', 'username', 'firstname','lastname','email'])
                }
    
    def execute(self, extracted_data):
        df = extracted_data["user"].copy()
        df = df.rename(columns={'id':'student_id'})
        df = df[df['student_id'] >= 3]
        df['student_id'] = df['student_id'].astype(str)
        return df



class TaskTransformer(NodeTransformer):
    """
    Liest Lernaufgaben und HVP-Bibliotheken ein, führt sie zusammen,
    bereinigt fehlende Werte und validiert sie über ein Pydantic-Schema.
    """
    DATA = {
            "tasks": (TASK_CSV_PATH, ['id', 'course', 'name', 'main_library_id']),
            "hvp":   (HVP_CSV_PATH, ['id', 'title'])
    }
        
    def execute(self, extracted_data):
        
        tasks = extracted_data["tasks"].copy()
        tasks = tasks.rename(columns={'id': 'task_id','course': 'course_id', 'name':'task_title'})
        tasks = tasks.assign(
            # Change id to the first two letters of the task name 
            task_id = lambda df: df['task_title'].str[:2].str.upper()
            )

        hvp = extracted_data["hvp"].copy()
        hvp = hvp.rename(columns={'id': 'main_library_id','title':'task_type'})


        # Beide Tabellen anhand der 'main_library_id' verknüpfen 
        merged_tasks = tasks.merge(hvp, on="main_library_id", how="left")
        # NaN-Werte in None-Werte umwandeln, da Pydantic sonst abstürzt
        merged_tasks = merged_tasks.where(pd.notna(merged_tasks), None)
        
        return merged_tasks
    



class SupportiveTransformer(NodeTransformer):
    """
    Extracts supportive information from Moodle pages and maps them 
    to the internal SI IDs defined in the course blueprint.
    """

    DATA = {
        "pages":   (PAGES_CSV_PATH,  ['id', 'course', 'name']),
        "mapping": (COURSE_CSV_PATH, ['si_id', 'supportive_title'])
    }
                 
    def execute(self, extracted_data):

        pages = extracted_data["pages"].copy()
        pages = pages.rename(columns={'id': 'moodle_id', 'course': 'course_id', 'name': 'si_title'})
        pages['moodle_id'] = pages['moodle_id'].astype(str)
        
        mapping = extracted_data["mapping"].copy()
        
        # Drop empty rows and ensure ID is string
        mapping = mapping.dropna(subset=['supportive_title', 'si_id'])
        title_to_id_map = mapping.set_index('supportive_title')['si_id'].astype(str).to_dict()
        
        # Filter for Supportive Information (SI) entries only
        pages_supportive = pages[pages['si_title'].str.startswith("(SI)", na=False)].copy()
        
        # Perform the ID Mapping
        # We try to find the internal ID based on the title.
        # If not found, we fall back to the original Moodle ID.
        pages_supportive['si_id'] = (
            pages_supportive['si_title']
            .map(title_to_id_map)
            .fillna(pages_supportive['moodle_id'].astype(str))
        )
        
        pages_supportive.reset_index(drop=True, inplace=True)
        
        return pages_supportive
    
    
class ProceduralTransformer(NodeTransformer):

    DATA = {
        "pages":   (PAGES_CSV_PATH,  ['id', 'course', 'name']),
        "mapping": (COURSE_CSV_PATH, ['pi_id', 'procedural_title'])
    }
    
    def execute(self, extracted_data):

        pages = extracted_data["pages"].copy()
        pages = pages.rename(columns={'id': 'moodle_id', 'course': 'course_id', 'name': 'pi_title'})
        pages['moodle_id'] = pages['moodle_id'].astype(str)
        
        mapping = extracted_data["mapping"].copy()
        
        # Drop empty rows and ensure ID is string
        mapping = mapping.dropna(subset=['procedural_title', 'pi_id'])
        title_to_id_map = mapping.set_index('procedural_title')['pi_id'].astype(str).to_dict()
        
        # Filter for Supportive Information (PI) entries only
        pages_procedural = pages[pages['pi_title'].str.startswith("(PI)", na=False)].copy()
        
        # Perform the ID Mapping
        # We try to find the internal ID based on the title.
        # If not found, we fall back to the original Moodle ID.
        pages_procedural['pi_id'] = (
            pages_procedural['pi_title']
            .map(title_to_id_map)
            .fillna(pages_procedural['moodle_id'].astype(str))
        )
        
        pages_procedural.reset_index(drop=True, inplace=True)
        
        return pages_procedural

 
    
class LearningSessionTransformer(NodeTransformer):
         """
         Reads the raw logfile, calculates sessions for all students,
         and returns a clean list of validated Pydantic model dictionaries ready for DB insertion.
         """
         DATA = {"logfile": (LOGFILE_CSV_PATH,  ['userid', 'timecreated', 'action'])}
    
         def execute(self, extracted_data):
             """Extract and validate data"""
             df_raw            = extracted_data["logfile"].copy()
             df_clean          = self._prepare_data(df_raw)
             learning_sessions = self._process_user_sessions(df_clean)
             
             return pd.DataFrame(learning_sessions)
    
    
         def _prepare_data(self, df):
             """Adjust timezone, sort chronologically, and remove system/admin accounts"""
             df['timecreated'] = pd.to_datetime(df['timecreated'] + 3600, unit='s')
             df = df.sort_values(by=['userid', 'timecreated']).reset_index(drop=True)
             df = df[df['userid'] >= 3]
             
             return df
    
    
         def _process_user_sessions(self, df: pd.DataFrame):
             """Iterates through all users and applies the session state machine logic"""
             learning_sessions = []
    
             for user_id, user_logs in df.groupby('userid'):
                 current_login_time = None
                 last_action_time   = None
    
                 for row in user_logs.itertuples():
                     if row.action == 'loggedin':
                         # Close dangling previous session if needed
                         if current_login_time is not None:
                             inferred_logout = last_action_time + timedelta(minutes=2)
                             self._append_session(learning_sessions, user_id, current_login_time, inferred_logout)
                         
                         current_login_time = row.timecreated
    
                     elif row.action == 'loggedout':
                         # Close session normally
                         if current_login_time is not None:
                             self._append_session(learning_sessions, user_id, current_login_time, row.timecreated)
                             current_login_time = None  # Reset state
    
                     # Continuously update the last action time
                     last_action_time = row.timecreated
    
                 # Handle a dangling login at the very end of the user's log history
                 if current_login_time is not None:
                     inferred_logout = last_action_time + timedelta(minutes=2)
                     self._append_session(learning_sessions, user_id, current_login_time, inferred_logout)
    
             return learning_sessions
    
         def _append_session(self, sessions_list, user_id, start_time, end_time):
            """Collects raw session data into a list of dictionaries."""
            
            start_time_str = start_time.isoformat()
            end_time_str = end_time.isoformat()
            
            sessions_list.append({
                "session_id": f"session_{user_id}_{start_time}",
                "student_id": str(user_id),
                "start_time": start_time_str, 
                "end_time":   end_time_str,
                "rds_ID":     f"r_ds_{user_id}_{start_time}"
            })

    
    
    
    
        
    
        
        
        
        
