import pandas as pd
import numpy as np
from src.config import LOGFILE_CSV_PATH, TASK_CSV_PATH, COURSE_CSV_PATH, PAGES_CSV_PATH, COMPLETED_CSV_PATH, COURSE_MODULE_CSV_PATH

# =====================================================================
# SHARED UTILITY FUNCTIONS (Used by Studied, Tackled, Reviewed, Consulted)
# =====================================================================

def get_sessionized_data(extracted_data):
    """
    Core vectorization engine. Reads logs, identifies session boundaries, 
    applies the 2-minute fallback, and returns BOTH the bounding session 
    data AND the individual logs tagged with their specific session_id.
    """
    df = extracted_data["logfile"].copy()
    df = df[['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']].copy()
    
    if df['timecreated'].dtype != 'datetime64[ns]':
        df['timecreated'] = pd.to_datetime(df['timecreated'] + 3600, unit='s')
        
    df['userid'] = pd.to_numeric(df['userid'], errors='coerce')
    df = df[df['userid'] >= 3].copy()
    df = df.sort_values(by=['userid', 'timecreated']).reset_index(drop=True)

    # 1. Block sessions by login
    df['is_login'] = df['action'] == 'loggedin'
    df['session_group'] = df.groupby('userid')['is_login'].cumsum()
    df = df[df['session_group'] > 0].copy() # Drop actions before first login
    
    # 2. Bound sessions by logout
    df['is_logout'] = df['action'] == 'loggedout'
    df['logout_cumsum'] = df.groupby(['userid', 'session_group'])['is_logout'].cumsum()
    
    valid_mask = (df['logout_cumsum'] == 0) | ((df['logout_cumsum'] == 1) & df['is_logout'])
    sessionized_logs = df[valid_mask].copy()

    # 3. Calculate Session Start and End Times
    session_bounds = sessionized_logs.groupby(['userid', 'session_group']).agg(
        session_start=('timecreated', 'first'),
        last_action=('timecreated', 'last'),
        has_logout=('is_logout', 'max')
    ).reset_index()

    session_bounds['session_end'] = np.where(
        session_bounds['has_logout'],
        session_bounds['last_action'],
        session_bounds['last_action'] + pd.Timedelta(minutes=2)
    )

    # 4. Generate the universal session_id
    session_bounds['session_id'] = "session_" + session_bounds['userid'].astype(int).astype(str) + "_" + session_bounds['session_start'].dt.strftime('%Y-%m-%dT%H:%M:%S')

    # 5. Attach the session details back to every individual log event
    cols_to_merge = ['userid', 'session_group', 'session_start', 'session_end', 'session_id']
    sessionized_logs = pd.merge(sessionized_logs, session_bounds[cols_to_merge], on=['userid', 'session_group'], how='left')

    return sessionized_logs, session_bounds


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
        _, session_bounds = get_sessionized_data(extracted_data)
        
        if session_bounds.empty:
            return pd.DataFrame()

        df = session_bounds.copy()
        df['student_id'] = df['userid'].astype(int).astype(str)
        df['start_time'] = df['session_start'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        df['end_time']   = df['session_end'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        df['duration']   = ((df['session_end'] - df['session_start']).dt.total_seconds() / 60.0).astype(str)
        
        df['studied_id'] = "studied_" + df['student_id'] + "_" + df['start_time']

        cols = ['studied_id', 'student_id', 'session_id', 'start_time', 'end_time', 'duration']
        return df[cols].copy().astype(str)

# =====================================================================
# TACKLED TRANSFORMER
# =====================================================================

class TackledTransformer:
    DATA = {
        "logfile": (LOGFILE_CSV_PATH, ['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']),
        "tasks": (TASK_CSV_PATH, ['id', 'name'])
    }

    def execute(self, extracted_data):
        sessionized_logs, _ = get_sessionized_data(extracted_data)
        views = calculate_view_durations(sessionized_logs)
        if views.empty: return pd.DataFrame()

        # Filter for Learning Tasks
        tasks = views[views['eventname'] == r'\mod_hvp\event\course_module_viewed'].copy()
        if tasks.empty: return pd.DataFrame()

        # FIX: Safe ID string mapping 
        tasks_map_df = extracted_data["tasks"].copy()
        tasks_map_df['id_clean'] = pd.to_numeric(tasks_map_df['id'], errors='coerce').astype('Int64').astype(str)
        task_prefix_map = tasks_map_df.set_index('id_clean')['name'].astype(str).str[:2].to_dict()
        
        tasks['objectid_clean'] = pd.to_numeric(tasks['objectid'], errors='coerce').astype('Int64').astype(str)
        tasks['task_id'] = tasks['objectid_clean'].map(task_prefix_map).fillna("LT")
        
        # Schema formatting
        tasks['student_id'] = tasks['userid'].astype(int).astype(str)
        tasks['start_time'] = tasks['timecreated'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        tasks['end_time']   = tasks['end_time'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        tasks['tackled_id'] = "tackled_" + tasks['student_id'] + "_" + tasks['task_id'] + "_" + tasks['start_time']
        tasks['time_spent'] = ((pd.to_datetime(tasks['end_time']) - pd.to_datetime(tasks['start_time'])).dt.total_seconds() / 60.0).astype(str)

        cols = ['tackled_id', 'session_id', 'task_id', 'start_time', 'end_time', 'time_spent']
        return tasks[cols].copy().astype(str)

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