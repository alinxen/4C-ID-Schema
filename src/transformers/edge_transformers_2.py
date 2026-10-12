import pandas as pd
import phpserialize

from src.config import (
    EXCLUDED_USER_IDS,
    GRADE_GRADES_CSV_PATH, 
    COMPLETED_CSV_PATH, 
    TASK_CSV_PATH, 
    LOGFILE_CSV_PATH, 
    XAPI_CSV_PATH,
    PTP_CSV_PATH
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
        "tasks": (TASK_CSV_PATH, ['module_id', 'content_id','task_id','grade_item_id','task_type']),
        "logfile": (LOGFILE_CSV_PATH, ['userid', 'eventname', 'other', 'timecreated', 'objectid'])
    }
        
    def execute(self, extracted_data):
        
        # Extracts entries from m_grade_grades (Final grade for learning tasks)
        df_attempts = self._get_attempt_completions(extracted_data)
        # Extracts entries from m_course_modules_completion (Button in learning tasks)
        df_buttons  = self._get_button_completions(extracted_data)
        
        # Combine DataFrames and only keep "button" if no "attempt" was registered first
        df_combined = pd.concat([df_attempts, df_buttons], ignore_index=True)
        df_combined = df_combined.sort_values('type')
        df_combined = df_combined.drop_duplicates(subset=['userid', 'task_id'], keep='first')

        # Fix hotspots using the shared utilities
        df_combined = self._fix_hotspot_scores(df_combined, extracted_data)
        
        # Remove admins
        df = df_combined.copy()
        df = df[~df['userid'].isin(EXCLUDED_USER_IDS)]

        
        # Send away
        attempted_records = []
        for row in df.itertuples():

            attempted_records.append({
                "finished_id": f"r_fin_{row.Index}_{row.userid}_{row.task_id}",
                "source_id": row.userid,
                "completion_type": row.type,
                "target_id": row.task_id,
                "completion_time":row.completion_time,
                "score": row.score
            })

            
        return pd.DataFrame(attempted_records)
    
    def _get_attempt_completions(self, extracted_data):
        grades_raw = extracted_data["grades"].copy()
        tasks     = extracted_data["tasks"].copy()
        
        
        filtered = grades_raw.dropna(subset=['timemodified', 'rawgrade']).copy()
        grades = filtered.merge(tasks, how='inner', left_on='itemid', right_on='grade_item_id')
        grades['type'] = 'attempt'
        grades['score'] = grades['finalgrade'].round(1)
        # Convert Unix timestamp to readable datetime and adjust timezone 
        grades['completion_time'] = (
        pd.to_datetime(grades['timemodified'], unit='s', utc=True)
           .dt.tz_convert('Europe/Berlin')
           .dt.strftime('%Y-%m-%dT%H:%M:%S')
        )
        return grades[['userid', 'task_id', 'completion_time', 'type', 'score']]

    def _get_button_completions(self, extracted_data):
        completions = extracted_data["completions"].copy()
        modules     = extracted_data["tasks"].copy()
        
        completions = completions[completions['completionstate'] == 1]
        df_button = completions.merge(modules, how='inner', left_on='coursemoduleid', right_on='module_id')
        df_button['type'] = 'button'
        df_button['score'] = None
        df_button['completion_time'] = (
        pd.to_datetime(df_button['timemodified'], unit='s', utc=True)
           .dt.tz_convert('Europe/Berlin')
           .dt.strftime('%Y-%m-%dT%H:%M:%S')
        )
        return df_button[['userid', 'task_id', 'completion_time', 'type', 'score']]

    def _fix_hotspot_scores(self, df_combined, extracted_data):
        """Fetches the logfile, calculates true scores, and overwrites."""
        logfile = extracted_data["logfile"].copy()
        tasks     = extracted_data["tasks"].copy()
        
        logfile['timecreated'] = pd.to_datetime(logfile['timecreated'], unit='s', utc=True)
        logfile['timecreated'] = logfile['timecreated'].dt.tz_convert('Europe/Berlin')
        logfile['timecreated'] = logfile['timecreated'].dt.tz_localize(None)
        
        # Use Shared Functions
        graded_events    = parse_graded_events(logfile)
        hotspot_ids      = get_hotspot_task_ids(extracted_data["tasks"])
        hotspot_attempts = graded_events[graded_events['grade_item_id'].isin(hotspot_ids)].copy()
        true_hotspot_df  = calculate_true_hotspot_scores(hotspot_attempts)
        
        # Get latest score
        latest_attempts = true_hotspot_df.sort_values('attempt_end_time').groupby(['userid', 'grade_item_id']).last().reset_index()
        latest_attempts = latest_attempts.merge(tasks, how='inner', left_on='grade_item_id', right_on='grade_item_id')
        
        # Merge onto df_combined
        merged = pd.merge(
            df_combined, 
            latest_attempts[['userid', 'task_id', 'final_grade']], 
            on=['userid', 'task_id'], 
            how='left'
        )
                       
        return merged[['userid', 'task_id', 'completion_time', 'type', 'score']]


















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
        standard_df['userid'] = standard_df['userid'].astype(str)
        
        # Map the correct grade_item_id onto the xAPI dataframe
        id_mapping = tasks_df[['content_id', 'grade_item_id']].dropna().drop_duplicates()
        xapi = xapi_df.rename(columns={'user_id': 'userid'})
        xapi['userid'] = xapi['userid'].fillna(0).astype(str)
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
        
        all_attempts = all_attempts.merge(
            tasks_df[['grade_item_id', 'task_id']], 
            on='grade_item_id', 
            how='inner',#inner'
            indicator=True
        )
        
        all_attempts.to_csv('all_attempts.csv')
        
        all_attempts['score'] = all_attempts['result'].astype(float).round(1)
        all_attempts['passed'] = all_attempts['score'] >= 8.0
        all_attempts['timestamp_str'] = all_attempts['timecreated'].apply(lambda x: x.isoformat())
        
               
        # Clear out recovered responses if applicable
        if 'is_recovered' in all_attempts.columns:
            all_attempts.loc[all_attempts['is_recovered'] == True, 'response'] = ""
            
        # Remove admins
        all_attempts = all_attempts[~all_attempts['userid'].isin(EXCLUDED_USER_IDS)]

        # Format output into the final list of dictionaries
        attempted_records = []
        for row in all_attempts.itertuples():
                        
            # Ensure text fields are string and handle potential NaNs safely
            student_resp = str(row.response) if pd.notna(row.response) else ""
            correct_resp = str(row.correct_responses_pattern) if pd.notna(row.correct_responses_pattern) else ""
            
            attempted_records.append({
                "attempted_id": f"attempted_{row.Index}",
                "timestamp": row.timestamp_str,
                "score": row.score,
                "passed": row.passed,
                "student_response": student_resp,
                "correct_response": correct_resp,
                "target_id": row.task_id,
                "source_id": row.userid
            })
            

            
        return pd.DataFrame(attempted_records)
    
    
    
# =====================================================================
# COMPLETED TRANSFORMER
# =====================================================================

class CompletedTransformer:
    """
    Processes grades and manual completions to generate COMPLETED relationships
    specifically for Part Task Practice activities.
    """
    
    DATA = {
        "grades": (GRADE_GRADES_CSV_PATH, ['userid', 'itemid', 'rawgrade', 'finalgrade', 'timemodified']),
        "completions": (COMPLETED_CSV_PATH, ['userid', 'coursemoduleid', 'completionstate', 'timemodified']),
        "practices": (PTP_CSV_PATH, ['module_id', 'grade_item_id', 'practice_id'])
    }
        
    def execute(self, extracted_data):
        
        # Extracts entries from m_grade_grades (Final grade for practice tasks)
        df_attempts = self._get_attempt_completions(extracted_data)
        # Extracts entries from m_course_modules_completion (Button in practice tasks)
        df_buttons  = self._get_button_completions(extracted_data)
        
        # Combine DataFrames and only keep "button" if no "attempt" was registered first
        df_combined = pd.concat([df_attempts, df_buttons], ignore_index=True)
        df_combined = df_combined.sort_values('type')
        df_combined = df_combined.drop_duplicates(subset=['userid', 'practice_id'], keep='first')
        
        # Remove admins
        df = df_combined[~df_combined['userid'].isin(EXCLUDED_USER_IDS)].copy()
        
        # Format output into the final list of dictionaries
        completed_records = []
        for row in df.itertuples():
            completed_records.append({
                "completed_id": f"r_comp_{row.Index}_{row.userid}_{row.practice_id}",
                "source_id": row.userid,
                "completion_type": row.type,
                "target_id": row.practice_id,
                "completion_time": row.completion_time,
                "score": row.score
            })
            
        return pd.DataFrame(completed_records)
    
    def _get_attempt_completions(self, extracted_data):
        grades_raw = extracted_data["grades"].copy()
        practices  = extracted_data["practices"].copy()
        
        filtered = grades_raw.dropna(subset=['timemodified', 'rawgrade']).copy()
        grades = filtered.merge(practices, how='inner', left_on='itemid', right_on='grade_item_id')
        grades['type'] = 'attempt'
        grades['score'] = grades['finalgrade'].round(1)
        
        # Convert Unix timestamp to readable datetime and adjust timezone 
        grades['completion_time'] = (
            pd.to_datetime(grades['timemodified'], unit='s', utc=True)
            .dt.tz_convert('Europe/Berlin')
            .dt.strftime('%Y-%m-%dT%H:%M:%S')
        )
        return grades[['userid', 'practice_id', 'completion_time', 'type', 'score']]

    def _get_button_completions(self, extracted_data):
        completions = extracted_data["completions"].copy()
        practices   = extracted_data["practices"].copy()
        
        # Only keep actual manual completions
        completions = completions[completions['completionstate'] == 1]
        df_button = completions.merge(practices, how='inner', left_on='coursemoduleid', right_on='module_id')
        df_button['type'] = 'button'
        df_button['score'] = None
        
        df_button['completion_time'] = (
            pd.to_datetime(df_button['timemodified'], unit='s', utc=True)
            .dt.tz_convert('Europe/Berlin')
            .dt.strftime('%Y-%m-%dT%H:%M:%S')
        )
        return df_button[['userid', 'practice_id', 'completion_time', 'type', 'score']]

