import pandas as pd
import numpy as np
from src.config import ( 
    EXCLUDED_USER_IDS,
    LOGFILE_CSV_PATH,
    TASK_CSV_PATH, 
    COURSE_CSV_PATH,
    PAGES_CSV_PATH,
    COMPLETED_CSV_PATH, 
    COURSE_MODULE_CSV_PATH,
    INFORMATION_CSV_PATH
    )

# =====================================================================
# SHARED UTILITY FUNCTIONS (Used by Studied, Tackled, Reviewed, Consulted)
# =====================================================================

def get_sessionized_data(extracted_data):
    """
    Reads the raw logfile, calculates sessions for all students.
    """
    logfile = extracted_data["logfile"].copy()
    
    
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
    
    # Generate session_id
    sessions_df['session_id'] = "session_" + sessions_df['userid'] + "_" + sessions_df['start_time'].astype(str)
    
    # Drop sessions where the student only clicked once
    sessions_df = sessions_df[sessions_df['start_time'] != sessions_df['end_time']].copy().reset_index(drop=True)

    # Merge the session_id and end_time back onto the raw logfile
    session_mapping = sessions_df[['userid', 'session_idx', 'session_id', 'end_time']].rename(columns={'end_time': 'session_end_time'})
    logfile_session = logfile.merge(session_mapping, on=['userid', 'session_idx'], how='inner')

    # List of sessions
    learning_sessions = []
    for row in sessions_df.itertuples():
        learning_sessions.append({
            "session_id": f"session_{row.userid}_{row.start_time}",
            "student_id": row.userid,
            "start_time": row.start_time, 
            "end_time":   row.end_time,
            "total_actions": row.total_actions
        })
    return logfile_session, pd.DataFrame(learning_sessions)


def calculate_view_durations(sessionized_logs):
    """Filters for 'viewed' actions and drops the first event to remove massive time gaps."""
    views = sessionized_logs[sessionized_logs['action'] == 'viewed'].copy()
    
    # NEW: Filter out missing time gaps and gaps over 30 minutes
    views = views.dropna(subset=['time_gap'])
    views = views[views['time_gap'] <= pd.Timedelta(minutes=30)]
    
    # Sort
    views = views.sort_values(by=['userid', 'timecreated'])
    
    # The end time of a view is the start time of the NEXT view in the SAME session
    views['end_time'] = views.groupby('session_id')['timecreated'].shift(-1)
    
    # If it's the last view in the session, the end time is the session's end time
    views['end_time'] = views['end_time'].fillna(views['session_end_time'])
    
    return views














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




# =====================================================================
# STUDIED TRANSFORMER
# =====================================================================

class StudiedTransformer:
    DATA = {
        "logfile": (LOGFILE_CSV_PATH, ['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated','other'])
    }

    def execute(self, extracted_data):
        # Utilizes shared logic to independently calculate sessions
        _,learning_sessions = get_sessionized_data(extracted_data)
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
        "logfile": (LOGFILE_CSV_PATH, ['userid', 'timecreated', 'action', 'eventname','other','id', 'objectid']),
        "tasks":   (TASK_CSV_PATH, ['content_id', 'task_title','task_id'])
    }

    def execute(self, extracted_data):
        
        logfile_sessions,sessions = get_sessionized_data(extracted_data)
        views = calculate_view_durations(logfile_sessions)
        
        # Filter for Learning Tasks
        tasks = views[views['eventname'] == r'\mod_hvp\event\course_module_viewed'].copy()
        tasks_info = extracted_data["tasks"].copy()
        combined_tasks = tasks.merge(
            tasks_info, 
            how='inner', 
            left_on='objectid', 
            right_on='content_id'
        )
        
        combined_tasks['duration']   = ((combined_tasks['end_time'] - combined_tasks['timecreated']).dt.total_seconds() / 60.0)
        
        tackled = []
        for row in combined_tasks.itertuples():
            tackled.append({
                "tackled_id": f"tackled_{row.userid}_{row.timecreated}",
                "source_id": row.session_id,
                "student_id": row.userid,
                "start_time": row.timecreated, 
                "end_time":   row.end_time,
                "duration": row.duration,
                "target_id": row.task_id
            })
            
        return pd.DataFrame(tackled)

# =====================================================================
# CONSULTED TRANSFORMER (Procedural Information)
# =====================================================================

class ConsultedTransformer:
    DATA = {
        "logfile": (LOGFILE_CSV_PATH, ['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']),
        "pages": (INFORMATION_CSV_PATH, ['page_id', 'title', 'id','type'])
    }

    def execute(self, extracted_data):
        sessionized_logs, _ = get_sessionized_data(extracted_data)
        views = calculate_view_durations(sessionized_logs)
        

        # Filter for mod_page
        pages = views[views['eventname'] == r'\mod_page\event\course_module_viewed'].copy()
        pages_info = extracted_data["pages"].copy()
        pages_info = pages_info[pages_info['type'] == 'page']
        pages_info = pages_info.rename(columns={'id': 'pi_id'})

        pages_pi = pages.merge(
            pages_info, 
            how='inner', 
            left_on='objectid', 
            right_on='page_id'
        )
        
        pages_pi['duration']   = ((pages_pi['end_time'] - pages_pi['timecreated']).dt.total_seconds() / 60.0)
        
        consulted = []
        for row in pages_pi.itertuples():
            consulted.append({
                "consulted_id": f"consulted_{row.userid}_{row.timecreated}",
                "source_id": row.session_id,
                "student_id": row.userid,
                "start_time": row.timecreated, 
                "end_time":   row.end_time,
                "duration": row.duration,
                "target_id": row.pi_id
            })
            
        return pd.DataFrame(consulted)


# =====================================================================
# REVIEWED TRANSFORMER (Supportive Information)
# =====================================================================

class ReviewedTransformer:
    DATA = {
        "logfile": (LOGFILE_CSV_PATH, ['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']),
        "pages": (INFORMATION_CSV_PATH, ['page_id', 'title', 'id','type'])
    }

    def execute(self, extracted_data):
        sessionized_logs, _ = get_sessionized_data(extracted_data)
        views = calculate_view_durations(sessionized_logs)
        
        # Filter for mod_page
        pages = views[views['eventname'] == r'\mod_longpage\event\course_module_viewed'].copy()
        pages_info = extracted_data["pages"].copy()
        pages_info = pages_info[pages_info['type'] == 'longpage']
        pages_info = pages_info.rename(columns={'id': 'si_id'})
                
        pages_si = pages.merge(
            pages_info, 
            how='inner', 
            left_on='objectid', 
            right_on='page_id'
        )

        pages_si['duration']   = ((pages_si['end_time'] - pages_si['timecreated']).dt.total_seconds() / 60.0)
        
        reviewed = []
        for row in pages_si.itertuples():
            reviewed.append({
                "reviewed_id": f"reviewed_{row.userid}_{row.timecreated}",
                "source_id": row.session_id,
                "student_id": row.userid,
                "start_time": row.timecreated, 
                "end_time":   row.end_time,
                "duration": row.duration,
                "target_id": row.si_id
            })
            
        return pd.DataFrame(reviewed)
