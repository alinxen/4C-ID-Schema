import pandas as pd
import phpserialize

from src.config import (
    EXCLUDED_USER_IDS,
    GRADE_GRADES_CSV_PATH, 
    COMPLETED_CSV_PATH, 
    COURSE_MODULE_CSV_PATH, 
    TASK_CSV_PATH, 
    COURSE_CSV_PATH, 
    LOGFILE_CSV_PATH, 
    XAPI_CSV_PATH, 
    HVP_CSV_PATH
    )

# =====================================================================
# SHARED UTILITY FUNCTIONS (Used by both Attempted and Finished)
# =====================================================================

def get_hotspot_task_ids(tasks_df):
    """Identifies all tasks that are of the type 'Find Multiple Hotspots'."""
    hotspot_df = tasks_df[tasks_df['task_type'] == "Find Multiple Hotspots"]
    
    return hotspot_df['grade_item_id'].astype(int).tolist()

def parse_graded_events(logfile_df):
    """Filters user_graded events and extracts the PHP objectid and finalgrade."""
    graded_events = logfile_df[logfile_df['eventname'] == r'\core\event\user_graded'].copy()
    
    # Parse the php-string in the column 'other' to get information about the event
    parsed_php = [
    phpserialize.loads(val.replace('""', '"').encode('utf-8'), decode_strings=True) 
    if isinstance(val, str) else {} 
    for val in graded_events['other']
    ]
    
    expanded_df = pd.DataFrame(parsed_php, index=graded_events.index)
    graded_events['grade_item_id'] = pd.to_numeric(expanded_df['itemid'], errors='coerce')
    graded_events['result']   = pd.to_numeric(expanded_df['finalgrade'], errors='coerce')
    
    return (graded_events
                     .dropna(subset=['grade_item_id', 'result', 'userid', 'timecreated'])
                     .astype({'grade_item_id': int, 'userid': str}))

def calculate_true_hotspot_scores(hotspot_df):
    """Groups hotspot clicks into attempts that start whenever the score resets to 0.0."""

    #hotspot_df['timecreated'] = pd.to_datetime(hotspot_df['timecreated'])
    hotspot_df = hotspot_df.sort_values(by=['userid', 'grade_item_id', 'timecreated'])
    
    # 2. The magic step: Create an attempt ID that increases by 1 every time result == 0.0
    # Grouping by user and object ensures the attempt ID resets for different users/exercises
    hotspot_df['attempt_id'] = hotspot_df.groupby(['userid', 'grade_item_id'])['result'].transform(
        lambda x: (x == 0.0).cumsum()
    )
    
    # 3. Group by our new dynamically generated attempt_id and grab the max grade
    hs_processed = (
        hotspot_df.groupby(['userid', 'grade_item_id', 'attempt_id'])
        .agg(
            attempt_start_time=('timecreated', 'min'), # When they clicked the first 0
            attempt_end_time=('timecreated', 'max'),   # When they hit their final score
            number_clicks=('grade_item_id', 'size'),        # Total clicks in this attempt
            final_grade=('result', 'max')              # The highest score reached
        )
        .reset_index()
    )

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
        "logfile": (LOGFILE_CSV_PATH, ['userid', 'eventname', 'other', 'timecreated','objecttable' ,'objectid']),
        "xapi": (XAPI_CSV_PATH, ['user_id', 'content_id', 'correct_responses_pattern', 'response', 'id']),
        "tasks": (TASK_CSV_PATH, ['grade_item_id', 'task_type', 'content_id', 'task_id']),
    }
            
    def _fetch_data(self, extracted_data):
        logfile = extracted_data["logfile"].copy()
        
        # Convert Unix timestamp to readable datetime and adjust timezone
        logfile['timecreated'] = pd.to_datetime(logfile['timecreated'], unit='s', utc=True)
        logfile['timecreated'] = logfile['timecreated'].dt.tz_convert('Europe/Berlin')
        logfile['timecreated'] = logfile['timecreated'].dt.tz_localize(None)
        
        # Filter out admins
        logfile = logfile[~logfile['userid'].isin(EXCLUDED_USER_IDS)].copy()

        return logfile, extracted_data["xapi"].copy(), extracted_data["tasks"].copy()

    def _process_standard_attempts(self, standard_df, xapi_df, tasks_df):
        
        # Identify the latest attempt in the standard grades dataframe
        standard_df['is_latest'] = (standard_df.groupby(['userid', 'grade_item_id'])['timecreated'].transform('max') == standard_df['timecreated'])
        standard_df['userid'] = standard_df['userid'].astype(int)
        
        # Map the correct grade_item_id onto the xAPI dataframe
        id_mapping = tasks_df[['content_id', 'grade_item_id']].dropna().drop_duplicates()
        xapi = xapi_df.rename(columns={'user_id': 'userid'})
        xapi['userid'] = xapi['userid'].fillna(0).astype(int)
        xapi = pd.merge(xapi, id_mapping, on='content_id', how='inner')
        
        xapi = xapi.sort_values('id').groupby(['userid', 'grade_item_id']).tail(1)
        
        # Merge standard attempts with the mapped xAPI data
        attempts = pd.merge(
            standard_df, 
            xapi[['userid', 'grade_item_id', 'correct_responses_pattern', 'response']], 
            on=['userid', 'grade_item_id'], 
            how='left'
        )
        
        # 5. Clean up non-latest attempts and fill NaNs
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
        # Moodle sometimes forgets to record the corresponding grade at the same timestamp as the attempt,
        # so we could scan 40s before and after the attempt to find the grade. For now, we've decided
        # to omit this step
        return pd.DataFrame()         
        
        
        

    def execute(self, extracted_data):
        
        logfile_df, xapi_df, tasks_df = self._fetch_data(extracted_data)
                
        # Extract objectid and results from the 'other' column
        graded_events = parse_graded_events(logfile_df)
                
        # Find attempts without recorded grades
        #recovered_events = self._recover_ungraded_attempts(logfile_df, graded_events)
        
        # Hotspots
        hotspot_ids = get_hotspot_task_ids(extracted_data["tasks"])
        hotspot_attempts = graded_events[graded_events['grade_item_id'].isin(hotspot_ids)]
        hotspot_attempts  = self._process_hotspot_attempts(hotspot_attempts)
        
        # Standard Attempts
        standard_attempts = graded_events[~graded_events['grade_item_id'].isin(hotspot_ids)]
        standard_attempts = self._process_standard_attempts(standard_attempts, xapi_df, tasks_df)
        
        # Summarize Attempts
        all_attempts = pd.concat([standard_attempts, hotspot_attempts], ignore_index=True)
        
        all_attempts['score'] = all_attempts['result'].astype(float).round(1)
        all_attempts['passed'] = all_attempts['score'] >= 8.0
        all_attempts['timestamp_str'] = all_attempts['timecreated'].apply(lambda x: x.isoformat())
        
        # Map the hvp items to the learning tasks 
        task_id_mapping = tasks_df.set_index('grade_item_id')['task_id'].to_dict()
        all_attempts['task_mapped'] = all_attempts['grade_item_id'].fillna(0).astype(int).map(lambda x: task_id_mapping.get(x, "LT"))
               
        # Clear out recovered responses if applicable
        if 'is_recovered' in all_attempts.columns:
            all_attempts.loc[all_attempts['is_recovered'] == True, 'response'] = ""

        # 2. Format output into the final list of dictionaries
        attempted_records = []
        for row in all_attempts.itertuples():
                        
            # Ensure text fields are string and handle potential NaNs safely
            student_resp = str(row.response) if pd.notna(row.response) else ""
            correct_resp = str(row.correct_responses_pattern) if pd.notna(row.correct_responses_pattern) else ""
            
            attempted_records.append({
                "attempted_id": f"r_at_{row.userid}_{row.grade_item_id}",
                "timestamp": row.timestamp_str,
                "score": row.score,
                "passed": row.passed,
                "student_response": student_resp,
                "correct_response": correct_resp,
                "target_id": row.task_mapped,
                "source_id": row.userid
            })
            

            
        return pd.DataFrame(attempted_records)