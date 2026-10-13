import pandas as pd
import numpy as np
from src.config import ( 
    EXCLUDED_USER_IDS,
    LOGFILE_CSV_PATH,
    TASK_CSV_PATH, 
    COURSE_CSV_PATH,
    PAGES_CSV_PATH,
    COMPLETED_CSV_PATH, 
    COURSE_MODULE_CSV_PATH
    )

# =====================================================================
# SHARED UTILITY FUNCTIONS (Used by Studied, Tackled, Reviewed, Consulted)
# =====================================================================

def get_sessionized_data(extracted_data):
    """
    Reads the raw logfile, calculates sessions for all students.
    """
    logfile = extracted_data["logfile"].copy()
    logfile = logfile[['userid', 'timecreated', 'action']]   #[['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']].copy()
    
    # Adjust timezone, sort chronologically, and remove system/admin accounts.
    logfile['timecreated'] = pd.to_datetime(logfile['timecreated'], unit='s', utc=True)
    logfile['timecreated'] = logfile['timecreated'].dt.tz_convert('Europe/Berlin')
    logfile['timecreated'] = logfile['timecreated'].dt.tz_localize(None)
    logfile = logfile[~logfile['userid'].isin(EXCLUDED_USER_IDS)]
    logfile = logfile.sort_values(by=['userid', 'timecreated']).reset_index(drop=True).copy()

    # Group events into sessions based on a 30-minute inactivity threshold 

    logfile['time_gap'] = logfile.groupby('userid')['timecreated'].diff()
    is_new_session = logfile['time_gap'] > pd.Timedelta(minutes=30)
    is_first_event = logfile['time_gap'].isna()
    logfile['session_idx'] = (is_new_session | is_first_event).cumsum()
    
    # Group by user and the new session index to get exact start and end boundaries
    sessions_df = logfile.groupby(['userid', 'session_idx']).agg(
       start_time=('timecreated', 'min'),
       end_time=('timecreated', 'max'),
       total_actions=('action', 'count')
      ).reset_index()
    
    # Drop sessions where the student only clicked once
    sessions_df = sessions_df[sessions_df['start_time'] != sessions_df['end_time']].copy().reset_index(drop=True)

    learning_sessions = []
    for row in sessions_df.itertuples():
        learning_sessions.append({
            "session_id": f"session_{row.userid}_{row.start_time}",
            "student_id": row.userid,
            "start_time": row.start_time, 
            "end_time":   row.end_time,
            "total_actions": row.total_actions
        })




    return pd.DataFrame(learning_sessions)










































def get_completion_timestamps(extracted_data):
    """Builds a dictionary of {(userid, instance_id): 'completion_time_str'} for PI/SI pages."""
    try:
        completions = extracted_data["completions"].copy()
        modules = extracted_data["modules"].copy()
        
        completions = completions[completions['completionstate'] == 1]
        df_merged = completions.merge(modules, how='inner', left_on='coursemoduleid', right_on='id')
        
        # mod_page
        completed_pages = df_merged[df_merged['module'] == 17].copy()
        if completed_pages.empty:
            return {}
            
        completed_pages['timemodified'] = pd.to_datetime(completed_pages['timemodified'], unit='s')
        # Use a space between date and time to match your original legacy format exactly
        completed_pages['completion_time_str'] = completed_pages['timemodified'].dt.strftime('%Y-%m-%dT%H:%M:%S') 
        
        # FIX: Force Int64 to drop the '.0' float artifact before stringifying
        completed_pages['instance_str'] = pd.to_numeric(completed_pages['instance'], errors='coerce').astype('Int64').astype(str)
        completed_pages['userid_str']   = pd.to_numeric(completed_pages['userid'], errors='coerce').astype('Int64').astype(str)
        
        return completed_pages.set_index(['userid_str', 'instance_str'])['completion_time_str'].to_dict()
    except Exception as e:
        print(f"Completion Mapping Warning: {e}")
        return {}


def calculate_view_durations(sessionized_logs):
    """Filters for 'viewed' actions and correctly calculates the end_time of the view."""
    views = sessionized_logs[sessionized_logs['action'] == 'viewed'].copy()
    if views.empty:
        return views
        
    # The end time of a view is the start time of the NEXT view in the SAME session
    views['end_time'] = views.groupby('session_id')['timecreated'].shift(-1)
    
    # If it's the last view in the session, the end time is the session's end time
    views['end_time'] = views['end_time'].fillna(views['session_end'])
    
    return views

# =====================================================================
# STUDIED TRANSFORMER
# =====================================================================

class StudiedTransformer:
    DATA = {
        "logfile": (LOGFILE_CSV_PATH, ['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated'])
    }

    def execute(self, extracted_data):
        # Utilizes shared logic to independently calculate sessions
        learning_sessions = get_sessionized_data(extracted_data)
        learning_sessions['duration']   = ((learning_sessions['end_time'] - learning_sessions['start_time']).dt.total_seconds() / 60.0)
        
        studied = []
        for row in learning_sessions.itertuples():
            studied.append({
                "studied_id": f"studied_{row.student_id}_{row.start_time}",
                "source_id": row.student_id,
                "start_time": row.start_time, 
                "end_time":   row.end_time,
                "duration": row.duration,
                "target_id": row.session_id
            })



        return pd.DataFrame(studied)
        
# =====================================================================
# TACKLED TRANSFORMER
# =====================================================================

class TackledTransformer:
    DATA = {
        "logfile": (LOGFILE_CSV_PATH, ['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']),
        #"tasks": (TASK_CSV_PATH, ['id', 'name'])
    }

    def execute(self, extracted_data):
        
        
        return pd.DataFrame()
        # sessionized_logs, _ = get_sessionized_data(extracted_data)
        # views = calculate_view_durations(sessionized_logs)
        # if views.empty: return pd.DataFrame()

        # # Filter for Learning Tasks
        # tasks = views[views['eventname'] == r'\mod_hvp\event\course_module_viewed'].copy()
        # if tasks.empty: return pd.DataFrame()

        # # FIX: Safe ID string mapping 
        # tasks_map_df = extracted_data["tasks"].copy()
        # tasks_map_df['id_clean'] = pd.to_numeric(tasks_map_df['id'], errors='coerce').astype('Int64').astype(str)
        # task_prefix_map = tasks_map_df.set_index('id_clean')['name'].astype(str).str[:2].to_dict()
        
        # tasks['objectid_clean'] = pd.to_numeric(tasks['objectid'], errors='coerce').astype('Int64').astype(str)
        # tasks['task_id'] = tasks['objectid_clean'].map(task_prefix_map).fillna("LT")
        
        # # Schema formatting
        # tasks['student_id'] = tasks['userid'].astype(int).astype(str)
        # tasks['start_time'] = tasks['timecreated'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        # tasks['end_time']   = tasks['end_time'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        # tasks['tackled_id'] = "tackled_" + tasks['student_id'] + "_" + tasks['task_id'] + "_" + tasks['start_time']
        # tasks['time_spent'] = ((pd.to_datetime(tasks['end_time']) - pd.to_datetime(tasks['start_time'])).dt.total_seconds() / 60.0).astype(str)

        # cols = ['tackled_id', 'session_id', 'task_id', 'start_time', 'end_time', 'time_spent']
        # return tasks[cols].copy().astype(str)

  
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    



# =====================================================================
# REVIEWED TRANSFORMER (Supportive Information)
# =====================================================================

class ReviewedTransformer:
    DATA = {
        "logfile": (LOGFILE_CSV_PATH, ['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']),
        "pages": (PAGES_CSV_PATH, ['id', 'name']),
        "blueprint": (COURSE_CSV_PATH, ['si_id', 'supportive_title']),
        "completions": (COMPLETED_CSV_PATH, ['userid', 'coursemoduleid', 'completionstate', 'timemodified']),
        "modules": (COURSE_MODULE_CSV_PATH, ['id', 'module', 'instance'])
    }

    def execute(self, extracted_data):
        sessionized_logs, _ = get_sessionized_data(extracted_data)
        views = calculate_view_durations(sessionized_logs)
        if views.empty: return pd.DataFrame()
        
        # Filter for mod_page
        pages = views[views['eventname'] == r'\mod_page\event\course_module_viewed'].copy()
        if pages.empty: return pd.DataFrame()

        # Build SI Map securely
        pages_df = extracted_data["pages"].copy()
        pages_df = pages_df[pages_df['name'].str.startswith("(SI)", na=False)].copy()
        
        blueprint = extracted_data["blueprint"].copy()
        title_to_id = blueprint.set_index('supportive_title')['si_id'].to_dict()
        
        pages_df['mapped_id'] = pages_df['name'].map(title_to_id).fillna("SI_" + pages_df['id'].astype(str))
        pages_df['id_clean']  = pd.to_numeric(pages_df['id'], errors='coerce').astype('Int64').astype(str)
        si_map = pages_df.set_index('id_clean')['mapped_id'].to_dict()

        # Apply mapping and filter
        # FIX: Safe Int64 parsing drops the float artifact (e.g. 45.0 -> 45)
        pages['objectid_clean'] = pd.to_numeric(pages['objectid'], errors='coerce').astype('Int64').astype(str)
        pages['si_id'] = pages['objectid_clean'].map(si_map)
        pages = pages[pages['si_id'].notna()].copy() 
        if pages.empty: return pd.DataFrame()

        # Build Schema
        completed_dict = get_completion_timestamps(extracted_data)
        pages['student_id'] = pages['userid'].astype(int).astype(str)
        pages['start_time'] = pages['timecreated'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        pages['end_time']   = pages['end_time'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        pages['time_spent'] = ((pd.to_datetime(pages['end_time']) - pd.to_datetime(pages['start_time'])).dt.total_seconds() / 60.0).astype(str)
        
        # Fetch completion times securely via multi-index mapping
        pages['userid_str'] = pd.to_numeric(pages['userid'], errors='coerce').astype('Int64').astype(str)
        pages['completion_time'] = pages.set_index(['userid_str', 'objectid_clean']).index.map(completed_dict)
        pages['completion_time'] = pages['completion_time'].fillna("")
        
        pages['reviewed_id'] = "reviewed_" + pages['student_id'] + "_" + pages['si_id'] + "_" + pages['start_time']

        cols = ['reviewed_id', 'session_id', 'si_id', 'start_time', 'end_time', 'time_spent', 'completion_time']
        return pages[cols].copy().astype(str)

# =====================================================================
# CONSULTED TRANSFORMER (Procedural Information)
# =====================================================================

class ConsultedTransformer:
    DATA = {
        "logfile": (LOGFILE_CSV_PATH, ['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']),
        "pages": (PAGES_CSV_PATH, ['id', 'name']),
        "blueprint": (COURSE_CSV_PATH, ['pi_id', 'procedural_title']),
        "completions": (COMPLETED_CSV_PATH, ['userid', 'coursemoduleid', 'completionstate', 'timemodified']),
        "modules": (COURSE_MODULE_CSV_PATH, ['id', 'module', 'instance'])
    }

    def execute(self, extracted_data):
        sessionized_logs, _ = get_sessionized_data(extracted_data)
        views = calculate_view_durations(sessionized_logs)
        if views.empty: return pd.DataFrame()
        
        # Filter for mod_page
        pages = views[views['eventname'] == r'\mod_page\event\course_module_viewed'].copy()
        if pages.empty: return pd.DataFrame()

        # Build PI Map securely
        pages_df = extracted_data["pages"].copy()
        pages_df = pages_df[pages_df['name'].str.startswith("(PI)", na=False)].copy()
        
        blueprint = extracted_data["blueprint"].copy()
        title_to_id = blueprint.set_index('procedural_title')['pi_id'].to_dict()
        
        pages_df['mapped_id'] = pages_df['name'].map(title_to_id).fillna("PI_" + pages_df['id'].astype(str))
        pages_df['id_clean']  = pd.to_numeric(pages_df['id'], errors='coerce').astype('Int64').astype(str)
        pi_map = pages_df.set_index('id_clean')['mapped_id'].to_dict()
        
        # Apply mapping and filter
        # FIX: Safe Int64 parsing drops the float artifact (e.g. 45.0 -> 45)
        pages['objectid_clean'] = pd.to_numeric(pages['objectid'], errors='coerce').astype('Int64').astype(str)
        pages['pi_id'] = pages['objectid_clean'].map(pi_map)
        pages = pages[pages['pi_id'].notna()].copy() 
        if pages.empty: return pd.DataFrame()

        # Build Schema
        completed_dict = get_completion_timestamps(extracted_data)
        pages['student_id'] = pages['userid'].astype(int).astype(str)
        pages['start_time'] = pages['timecreated'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        pages['end_time']   = pages['end_time'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        pages['time_spent'] = ((pd.to_datetime(pages['end_time']) - pd.to_datetime(pages['start_time'])).dt.total_seconds() / 60.0).astype(str)
        
        # Fetch completion times securely via multi-index mapping
        pages['userid_str'] = pd.to_numeric(pages['userid'], errors='coerce').astype('Int64').astype(str)
        pages['completion_time'] = pages.set_index(['userid_str', 'objectid_clean']).index.map(completed_dict)
        pages['completion_time'] = pages['completion_time'].fillna("")
        
        pages['consulted_id'] = "consulted_" + pages['student_id'] + "_" + pages['pi_id'] + "_" + pages['start_time']

        cols = ['consulted_id', 'session_id', 'pi_id', 'start_time', 'end_time', 'time_spent', 'completion_time']
        return pages[cols].copy().astype(str)