import pandas as pd
import json

from src.config import GRADE_GRADES_CSV_PATH, COMPLETED_CSV_PATH, COURSE_MODULE_CSV_PATH, TASK_CSV_PATH, COURSE_CSV_PATH, LOGFILE_CSV_PATH, XAPI_CSV_PATH, HVP_CSV_PATH

# =====================================================================
# SHARED UTILITY FUNCTIONS (Used by both Attempted and Finished)
# =====================================================================

def get_hotspot_task_ids(tasks_df, libs_df):
    """Identifies all tasks that are of the type 'Find Multiple Hotspots'."""
    target_lib_ids = libs_df[libs_df['title'] == "Find Multiple Hotspots"]['id']
    hotspot_tasks = tasks_df[tasks_df['main_library_id'].isin(target_lib_ids)]
    return hotspot_tasks['id'].tolist()

def parse_graded_events(logfile_df):
    """Filters user_graded events and extracts the JSON objectid and finalgrade."""
    graded_events = logfile_df[logfile_df['eventname'] == r'\core\event\user_graded'].copy()
    if graded_events.empty:
        return graded_events

    parsed_json = [json.loads(val) if isinstance(val, str) else {} for val in graded_events['other']]
    expanded_df = pd.DataFrame(parsed_json, index=graded_events.index)
    
    graded_events['objectid'] = pd.to_numeric(expanded_df['itemid'], errors='coerce') - 2
    graded_events['result']   = pd.to_numeric(expanded_df['finalgrade'], errors='coerce')
    
    graded_events = (graded_events
                     .dropna(subset=['objectid', 'result', 'userid', 'timecreated'])
                     .astype({'objectid': int, 'userid': str}))
    return graded_events

def calculate_true_hotspot_scores(hotspot_df):
    """Aggregates hotspot clicks into 10-minute blocks and calculates custom scores."""
    if hotspot_df.empty:
        return pd.DataFrame()
        
    scoring_rules = {3: 4, 21: 16}

    first_click   = hotspot_df.groupby(['userid', 'objectid'])['timecreated'].transform('first')
    attempt_block = ((hotspot_df['timecreated'] - first_click) // pd.Timedelta('10min')).astype(int)
    
    hs_processed = (
        hotspot_df.assign(attempt_block=attempt_block)
        .groupby(['userid', 'objectid', 'attempt_block'])
        .agg(timecreated=('timecreated', 'max'), number_clicks=('objectid', 'size'))
        .reset_index()
    )
    
    hs_processed['result'] = 0.0
    hs_processed['required_clicks'] = hs_processed['objectid'].map(scoring_rules)
    
    valid_mask = hs_processed['required_clicks'].notna() & (hs_processed['number_clicks'] >= hs_processed['required_clicks'])
    hs_processed.loc[valid_mask, 'result'] = (hs_processed.loc[valid_mask, 'required_clicks'] / hs_processed.loc[valid_mask, 'number_clicks']) * 10
    
    hs_processed.drop(columns=['required_clicks'], inplace=True)
    return hs_processed


# =====================================================================
# FINISHED TRANSFORMER
# =====================================================================

class FinishedTransformer:
    """
    Processes grades and manual completions to generate FINISHED relationships.
    Completely independent; recalculates true Hotspot scores autonomously.
    """
    
    DATA = {
        "grades": (GRADE_GRADES_CSV_PATH, ['userid', 'itemid', 'rawgrade', 'finalgrade', 'timemodified']),
        "completions": (COMPLETED_CSV_PATH, ['userid', 'coursemoduleid', 'completionstate', 'timemodified']),
        "modules": (COURSE_MODULE_CSV_PATH, ['id', 'module', 'instance']),
        "moodle_tasks": (TASK_CSV_PATH, ['id', 'name']),
        "blueprint": (COURSE_CSV_PATH, ['task_id', 'task']),
        # Added these so Finished can autonomously calculate Hotspots:
        "logfile": (LOGFILE_CSV_PATH, ['userid', 'eventname', 'other', 'timecreated', 'objectid']),
        "libs": (HVP_CSV_PATH,  ['id', 'title']),
        "tasks": (TASK_CSV_PATH, ['id', 'main_library_id'])
    }

    # Notice attempted_df is gone. It is now 100% independent!
    def execute(self, extracted_data):
        df_attempts = self._get_attempt_completions(extracted_data)
        df_buttons = self._get_button_completions(extracted_data)
        df_combined = self._combine_completions(df_attempts, df_buttons)
        
        if df_combined.empty:
            return self._process_finished_relations(df_combined)

        task_map = self._create_task_map(extracted_data)
        df_combined['task_id_raw'] = df_combined['task_id'].astype(int)
        df_combined['task_id'] = df_combined['task_id_raw'].map(lambda x: task_map.get(x, "LT"))

        # Autonomously fix hotspots using the shared utilities
        df_combined = self._fix_hotspot_scores(df_combined, extracted_data, task_map)
            
        finished_df = self._process_finished_relations(df_combined)
        return finished_df

    def _create_task_map(self, extracted_data):
        moodle_tasks = extracted_data["moodle_tasks"].copy()
        blueprint = extracted_data["blueprint"].copy()
        merged = moodle_tasks.merge(blueprint, left_on='name', right_on='task', how='inner')
        return merged.set_index('id')['task_id'].to_dict()

    def _get_attempt_completions(self, extracted_data):
        try:
            grades = extracted_data["grades"].copy()
            grades = grades.dropna(subset=['timemodified', 'rawgrade']).copy()
            grades['task_id'] = (grades['itemid'] - 2).astype(int).astype(str)
            grades['type'] = 'attempt'
            grades['score'] = grades['finalgrade'].round(1)
            grades['completion_time'] = pd.to_datetime(grades['timemodified'], unit='s').dt.strftime('%Y-%m-%dT%H:%M:%S')
            return grades[['userid', 'task_id', 'completion_time', 'type', 'score']]
        except FileNotFoundError:
            return pd.DataFrame()

    def _get_button_completions(self, extracted_data):
        try:
            completions = extracted_data["completions"].copy()
            modules = extracted_data["modules"].copy()
            completions = completions[completions['completionstate'] == 1]
            df_merged = completions.merge(modules, how='inner', left_on='coursemoduleid', right_on='id')
            df_tasks = df_merged[df_merged['module'] == 12].copy()
            df_tasks['task_id'] = df_tasks['instance'].astype(int).astype(str)
            df_tasks['type'] = 'button'
            df_tasks['score'] = None
            df_tasks['completion_time'] = pd.to_datetime(df_tasks['timemodified'], unit='s').dt.strftime('%Y-%m-%dT%H:%M:%S')
            return df_tasks[['userid', 'task_id', 'completion_time', 'type', 'score']]
        except FileNotFoundError:
            return pd.DataFrame()

    def _combine_completions(self, df_attempts, df_buttons):
        df_combined = pd.concat([df_attempts, df_buttons], ignore_index=True)
        if df_combined.empty:
            return df_combined
        df_combined = df_combined.sort_values('type')
        df_combined = df_combined.drop_duplicates(subset=['userid', 'task_id'], keep='first')
        return df_combined

    def _fix_hotspot_scores(self, df_combined, extracted_data, task_map):
        """Autonomously fetches the logfile, calculates true scores, and overwrites."""
        logfile = extracted_data["logfile"].copy()
        logfile['timecreated'] = pd.to_datetime(logfile['timecreated'] + 3600, unit='s')
        logfile['userid'] = pd.to_numeric(logfile['userid'], errors='coerce')
        logfile = logfile[~logfile['userid'].isin([1, 2])].copy()
        
        # Cast to string for safe grouping
        logfile['userid'] = logfile['userid'].astype(str)

        # Use Shared Utilities
        hotspot_ids = get_hotspot_task_ids(extracted_data["tasks"], extracted_data["libs"])
        graded_events = parse_graded_events(logfile)
        hotspot_attempts = graded_events[graded_events['objectid'].isin(hotspot_ids)].copy()
        
        true_hotspot_df = calculate_true_hotspot_scores(hotspot_attempts)
        
        if true_hotspot_df.empty:
            return df_combined

        # Get latest score
        latest_attempts = true_hotspot_df.sort_values('timecreated').groupby(['userid', 'objectid']).last().reset_index()
        latest_attempts['task_id'] = latest_attempts['objectid'].astype(int).map(lambda x: task_map.get(x, "LT"))
        
        # THE FIX: Force both keys to string explicitly to prevent merge crashes
        df_combined['userid'] = df_combined['userid'].astype(str)
        latest_attempts['userid'] = latest_attempts['userid'].astype(str)
        
        # Merge onto df_combined
        merged = pd.merge(
            df_combined, 
            latest_attempts[['userid', 'task_id', 'result']], 
            on=['userid', 'task_id'], 
            how='left'
        )
        
        merged['score'] = merged['result'].fillna(merged['score'])
        return merged.drop(columns=['result'])

    def _process_finished_relations(self, df):
        if df.empty:
            return pd.DataFrame(columns=['finished_id', 'student_id', 'task_id', 'completion_time', 'completion_type', 'score'])

        df['userid'] = pd.to_numeric(df['userid'], errors='coerce')
        df = df[~df['userid'].isin([1, 2])].copy()

        df['student_id'] = df['userid'].astype(int).astype(str)
        df['completion_type'] = df['type'].astype(str)
        df['finished_id'] = "finished_" + df['student_id'] + "_" + df['task_id']

        def clean_score(val):
            if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '<na>', '']:
                return ""
            return str(val)

        df['score'] = df['score'].apply(clean_score)

        columns_to_keep = ['finished_id', 'student_id', 'task_id', 'completion_time', 'completion_type', 'score']
        final_df = df[columns_to_keep].copy()
        return final_df.astype(str)


# =====================================================================
# ATTEMPTED TRANSFORMER
# =====================================================================

class AttemptedTransformer():
    DATA = {
        "logfile": (LOGFILE_CSV_PATH, ['userid', 'eventname', 'other', 'timecreated', 'objectid']),
        "xapi": (XAPI_CSV_PATH, ['user_id', 'content_id', 'correct_responses_pattern', 'response']),
        "tasks": (TASK_CSV_PATH, ['id', 'main_library_id']),
        "libs": (HVP_CSV_PATH,  ['id', 'title']),
        "moodle_tasks": (TASK_CSV_PATH, ['id', 'name']),
        "blueprint": (COURSE_CSV_PATH, ['task_id', 'task'])
    }
            
    def _fetch_data(self, extracted_data):
        logfile = extracted_data["logfile"].copy()
        logfile['timecreated'] = pd.to_datetime(logfile['timecreated'] + 3600, unit='s')
        logfile['userid'] = pd.to_numeric(logfile['userid'], errors='coerce')
        logfile = logfile[~logfile['userid'].isin([1, 2])].copy()
        logfile['userid'] = logfile['userid'].astype(str)
        return logfile, extracted_data["xapi"].copy()

    def _process_standard_attempts(self, standard_df, xapi_df):
        if standard_df.empty: return pd.DataFrame()
        standard_df['is_latest'] = (standard_df.groupby(['userid', 'objectid'])['timecreated'].transform('max') == standard_df['timecreated'])
        xapi = xapi_df.rename(columns={'content_id': 'objectid', 'user_id': 'userid'}).astype({'userid': str})
        attempts = pd.merge(standard_df, xapi[['userid', 'objectid', 'correct_responses_pattern', 'response']], on=['userid', 'objectid'], how='left')
        attempts.loc[~attempts['is_latest'], ['correct_responses_pattern', 'response']] = None
        attempts.fillna({'correct_responses_pattern': "", 'response': ""}, inplace=True)
        attempts.drop(columns=['is_latest'], inplace=True)
        return attempts
        
    def _process_hotspot_attempts(self, hotspot_df):
        # Uses the shared utility function!
        hs_processed = calculate_true_hotspot_scores(hotspot_df)
        if not hs_processed.empty:
            hs_processed['response'] = ""
            hs_processed['correct_responses_pattern'] = ""
        return hs_processed

    def _create_task_map(self, extracted_data):
        moodle_tasks = extracted_data["moodle_tasks"].copy()
        blueprint = extracted_data["blueprint"].copy()
        merged = moodle_tasks.merge(blueprint, left_on='name', right_on='task', how='inner')
        return merged.set_index('id')['task_id'].to_dict()

    def _recover_ungraded_attempts(self, logfile_df, graded_events):
        logfile_df = logfile_df.sort_values('timecreated')
        submissions = logfile_df[logfile_df['eventname'] == r'\mod_hvp\event\attempt_submitted'].copy()
        grades = graded_events.copy()
        if submissions.empty or grades.empty: return pd.DataFrame()

        matched_forward = pd.merge_asof(submissions, grades[['timecreated', 'eventname']], on='timecreated', direction='forward', tolerance=pd.Timedelta(seconds=40), suffixes=('', '_fwd'))
        matched_backward = pd.merge_asof(submissions, grades[['timecreated', 'eventname']], on='timecreated', direction='backward', tolerance=pd.Timedelta(seconds=40), suffixes=('', '_bwd'))
        unpaired_mask = matched_forward['eventname_fwd'].isna() & matched_backward['eventname_bwd'].isna()
        unpaired_submissions = matched_forward[unpaired_mask].drop(columns=['eventname_fwd']).copy()
        
        if unpaired_submissions.empty: return pd.DataFrame()
            
        views = logfile_df[logfile_df['eventname'] == r'\mod_hvp\event\course_module_viewed'].copy()
        views['objectid'] = pd.to_numeric(views['objectid'], errors='coerce')
        recovered = pd.merge_asof(unpaired_submissions.drop(columns=['objectid']), views[['userid', 'timecreated', 'objectid']], on='timecreated', by='userid', direction='backward')
        recovered = recovered.dropna(subset=['objectid'])
        
        latest_grades = grades.sort_values('timecreated').groupby(['userid', 'objectid']).last().reset_index()
        return pd.merge(recovered, latest_grades[['userid', 'objectid', 'result']], on=['userid', 'objectid'], how='inner')

    def execute(self, extracted_data):
        logfile_df, xapi_df = self._fetch_data(extracted_data)
        
        # Uses the shared utility functions!
        hotspot_ids = get_hotspot_task_ids(extracted_data["tasks"], extracted_data["libs"])
        graded_events = parse_graded_events(logfile_df)
        
        recovered_events = self._recover_ungraded_attempts(logfile_df, graded_events)
        
        if not recovered_events.empty:
            recovered_events = recovered_events[~recovered_events['objectid'].isin(hotspot_ids)].copy()
            recovered_events['is_recovered'] = True 
            graded_events = pd.concat([graded_events, recovered_events], ignore_index=True)
            graded_events['is_recovered'] = graded_events['is_recovered'].fillna(False)
            
        is_hotspot = graded_events['objectid'].isin(hotspot_ids)
        standard_attempts = graded_events[~is_hotspot].copy()
        hotspot_attempts  = graded_events[is_hotspot].copy()
        
        standard_attempts = self._process_standard_attempts(standard_attempts, xapi_df)
        hotspot_attempts  = self._process_hotspot_attempts(hotspot_attempts)

        all_attempts = pd.concat([standard_attempts, hotspot_attempts], ignore_index=True)
        task_prefix_map = self._create_task_map(extracted_data)
        
        all_attempts['score'] = all_attempts['result'].astype(float).round(1)
        all_attempts['passed'] = all_attempts['score'] >= 8.0
        all_attempts['student_response'] = all_attempts['response'].astype(str)
        all_attempts['correct_response'] = all_attempts['correct_responses_pattern'].astype(str)
        all_attempts['task_id'] = all_attempts['objectid'].astype(int).map(lambda x: task_prefix_map.get(x, "LT"))
        all_attempts['student_id'] = all_attempts['userid'].astype(str)
        all_attempts['timestamp'] = all_attempts['timecreated'].apply(lambda x: x.isoformat())
        
        all_attempts['attempted_id'] = "r_at_" + all_attempts['student_id'] + "_" + all_attempts['task_id'] + "_" + all_attempts['timestamp']
        
        if 'is_recovered' in all_attempts.columns:
            all_attempts.loc[all_attempts['is_recovered'] == True, 'student_response'] = ""
        
        columns_to_keep = ['attempted_id', 'timestamp', 'score', 'passed', 'student_response', 'correct_response', 'task_id', 'student_id']
        return all_attempts[columns_to_keep]