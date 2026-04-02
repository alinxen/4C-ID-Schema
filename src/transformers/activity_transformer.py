import pandas as pd
import json
from src.schema import ATTEMPTED
from src.config import LOGFILE_CSV_PATH, XAPI_CSV_PATH, TASK_CSV_PATH, HVP_CSV_PATH


def extract_hotspot_task_ids():
    """
    Identifies all tasks that are of the type 'Find Multiple Hotspots'
    by merging the HVP tasks table with the HVP libraries table.
    
    Returns a clean list of task IDs.
    """
    
    tasks_df = pd.read_csv(TASK_CSV_PATH)
    libraries_df =pd.read_csv(HVP_CSV_PATH)
    
    if tasks_df.empty or libraries_df.empty:
        return []

    # 1. Isolate the necessary columns
    tasks = tasks_df[['id', 'main_library_id']].copy()
    
    libs = libraries_df[['id', 'title']].copy()
    libs = libs.rename(columns={'id': 'main_library_id'})

    # 2. Merge to connect the task ID with the human-readable library title
    merged_df = tasks.merge(libs, how="left", on="main_library_id")

    # 3. Filter for Hotspot tasks
    hotspot_tasks = merged_df[merged_df['title'] == "Find Multiple Hotspots"]
    
    # 4. Convert the pandas Series of IDs into a standard Python list
    hotspot_ids = hotspot_tasks['id'].tolist()

    return hotspot_ids


class AttemptedTransformer():

    def execute(self):
        """
        Extracts ALL graded learning task attempts (both successes and struggles).
        Handles JSON parsing, the Hotspot workarounds, and xAPI response merging in pure Pandas.
        """
        
        logfile_df = pd.read_csv(LOGFILE_CSV_PATH)
        logfile_df['timecreated'] = pd.to_datetime(logfile_df['timecreated'] + 3600, unit='s')
        xapi_df    = pd.read_csv(XAPI_CSV_PATH)
        hotspot_task_ids = extract_hotspot_task_ids()
        
        edges = []
        
        # --- 1. Filter and Parse the Standard Graded Events ---
        graded_events = logfile_df[logfile_df['eventname'] == r'\core\event\user_graded'].copy()
        
        if graded_events.empty:
            return edges

        # Safely extract objectid and result from the JSON 'other' column
        def parse_json_col(val, key, cast_type):
            try:
                return cast_type(json.loads(val).get(key))
            except (TypeError, ValueError, AttributeError):
                return None

        graded_events['objectid'] = graded_events['other'].apply(lambda x: parse_json_col(x, 'itemid', int))
        graded_events['objectid'] = graded_events['objectid'] - 2  # Align to m_hvp scale
        graded_events['result'] = graded_events['other'].apply(lambda x: parse_json_col(x, 'finalgrade', float))
        
        # Drop rows that failed to parse
        graded_events = graded_events.dropna(subset=['objectid', 'result', 'userid', 'timecreated'])
        graded_events['objectid'] = graded_events['objectid'].astype(int)
        graded_events['userid'] = graded_events['userid'].astype(str)

        # --- 2. Separate Standard Tasks and Hotspot Tasks ---
        is_hotspot = graded_events['objectid'].isin(hotspot_task_ids)
        standard_attempts = graded_events[~is_hotspot].copy()
        hotspot_attempts = graded_events[is_hotspot].copy()

        # --- 3. Process Standard Attempts & Join xAPI Data ---
        if not standard_attempts.empty:
            # Find the latest attempt per user per objectid to attach xAPI data
            standard_attempts['is_latest'] = standard_attempts.groupby(['userid', 'objectid'])['timecreated'].transform('max') == standard_attempts['timecreated']
            
            # Clean xAPI data
            xapi = xapi_df.rename(columns={'content_id': 'objectid', 'user_id': 'userid'}).copy()
            xapi['userid'] = xapi['userid'].astype(str)
            
            # Merge xAPI data onto the standard attempts
            standard_attempts = pd.merge(
                standard_attempts, 
                xapi[['userid', 'objectid', 'correct_responses_pattern', 'response']], 
                on=['userid', 'objectid'], 
                how='left'
            )
            
            # xAPI data only belongs to the *latest* attempt, null out the rest
            standard_attempts.loc[~standard_attempts['is_latest'], ['correct_responses_pattern', 'response']] = None
            
            # Replace NaNs with empty strings for Neo4j compatibility
            standard_attempts['correct_responses_pattern'] = standard_attempts['correct_responses_pattern'].fillna("")
            standard_attempts['response'] = standard_attempts['response'].fillna("")

        # --- 4. Process Hotspot Tasks (Workaround Logic) ---
        hs_processed = pd.DataFrame()
        if not hotspot_attempts.empty:
            # Group clicks into 10-minute attempt blocks
            hotspot_attempts['first_click'] = hotspot_attempts.groupby(['userid', 'objectid'])['timecreated'].transform('first')
            hotspot_attempts['time_since'] = hotspot_attempts['timecreated'] - hotspot_attempts['first_click']
            hotspot_attempts['attempt_block'] = (hotspot_attempts['time_since'] // pd.Timedelta('10min')).astype(int)
            
            # Aggregate the blocks
            hs_processed = hotspot_attempts.groupby(['userid', 'objectid', 'attempt_block']).agg(
                latest_timestamp=('timecreated', 'max'),
                number_clicks=('objectid', 'size')
            ).reset_index()
            
            # Calculate scores based on click counts
            def calc_hs_score(row):
                if row['objectid'] == 3 and row['number_clicks'] > 3:
                    return (4 / row['number_clicks']) * 10
                elif row['objectid'] == 21 and row['number_clicks'] > 15:
                    return (16 / row['number_clicks']) * 10
                return 0.0
                
            hs_processed['result'] = hs_processed.apply(calc_hs_score, axis=1)
            hs_processed['timecreated'] = hs_processed['latest_timestamp']
            hs_processed['response'] = ""
            hs_processed['correct_responses_pattern'] = ""

        # --- 5. Combine All Attempts ---
        # Notice we removed the < 8.0 filter here so we keep EVERYTHING!
        all_attempts = pd.concat([standard_attempts, hs_processed], ignore_index=True)
        
        tasks_map_df = pd.read_csv(TASK_CSV_PATH)
        task_prefix_map = tasks_map_df.set_index('id')['name'].astype(str).str[:2].to_dict()
        
        # --- 6. Generate Pydantic Models and Serialize ---
        validated_edges = []
        for _, row in all_attempts.iterrows():
            user_str = str(row['userid'])
            obj_int = int(row['objectid'])
            obj_str = str(row['objectid'])
            timestamp = row['timecreated']
            timestamp_str = timestamp.isoformat()
            score_val = round(float(row['result']), 1)
            
            prefix = task_prefix_map.get(obj_int, "LT")

            # Instantiate the Pydantic model to validate the data
            edge = ATTEMPTED(
                attempted_id=f"r_at_{user_str}_{obj_str}_{timestamp.timestamp()}",
                timestamp=timestamp_str,
                score=score_val,
                passed=(score_val >= 8.0), # Make sure to uncomment 'passed' in your schema!
                student_response=str(row['response']),
                correct_response=str(row['correct_responses_pattern']),
                task_id=f"{prefix}",
                student_id=user_str
            )
            
            # Immediately serialize to a dictionary and append
            validated_edges.append(edge.model_dump())
        return validated_edges