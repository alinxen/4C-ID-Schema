import pandas as pd
import json
from src.config import LOGFILE_CSV_PATH, XAPI_CSV_PATH, TASK_CSV_PATH, HVP_CSV_PATH, COURSE_CSV_PATH
from src.validators.pydantic_validator import PydanticValidator




class AttemptedTransformer():

    def __init__(self, data_store):
        self.data = data_store
    
    
    def _fetch_data(self):
        """Fetches data and applies initial time corrections to raw data logs."""
        logfile = self.data.get_csv(
            LOGFILE_CSV_PATH,
            columns=['userid', 'eventname', 'other', 'timecreated'])
        
        # Apply +1 hour timezone offset
        logfile['timecreated'] = pd.to_datetime(logfile['timecreated'] + 3600, unit='s')
        
        xapi = self.data.get_csv(
            XAPI_CSV_PATH,
            columns=['user_id', 'content_id', 'correct_responses_pattern', 'response'])
           
        return logfile, xapi
    
        
    def _extract_hotspot_task_ids(self):
        """
        Identifies all tasks that are of the type 'Find Multiple Hotspots'
        by matching the HVP tasks with the HVP libraries.
        """
        tasks = self.data.get_csv(TASK_CSV_PATH, columns=['id', 'main_library_id'])
        libs  = self.data.get_csv(HVP_CSV_PATH,  columns=['id', 'title'])
        
        target_lib_ids = libs[libs['title'] == "Find Multiple Hotspots"]['id']
        hotspot_tasks = tasks[tasks['main_library_id'].isin(target_lib_ids)]
        
        return hotspot_tasks['id'].tolist()
    

    def _parse_graded_events(self, logfile_df):
        """Filters user_graded events."""
        graded_events = logfile_df[logfile_df['eventname'] == r'\core\event\user_graded'].copy()
        
        if graded_events.empty:
            return graded_events

        # Parse JSON strings into a list of dictionaries
        parsed_json = [
            json.loads(val) if isinstance(val, str) else {} 
            for val in graded_events['other']
        ]
        
        expanded_df = pd.DataFrame(parsed_json, index=graded_events.index)
        graded_events['objectid'] = pd.to_numeric(expanded_df['itemid'], errors='coerce') - 2
        graded_events['result']   = pd.to_numeric(expanded_df['finalgrade'], errors='coerce')
        graded_events = (graded_events
                         .dropna(subset=['objectid', 'result', 'userid', 'timecreated'])
                         .astype({'objectid': int, 'userid': str}))
        return graded_events


    def _process_standard_attempts(self, standard_df, xapi_df):
        """Merges xAPI data onto standard learning tasks, keeping only the latest response."""
        
        if standard_df.empty:
            return pd.DataFrame()

        # Attach 'is_latest' directly as a column so it survives the merge
        standard_df['is_latest'] = (
            standard_df.groupby(['userid', 'objectid'])['timecreated'].transform('max') 
            == standard_df['timecreated']
        )
        
        # Standardize xAPI columns to match the standard logfile for merging
        xapi = (
            xapi_df
            .rename(columns={'content_id': 'objectid', 'user_id': 'userid'})
            .astype({'userid': str})
        )
        
        # Initially attaches the xAPI response text to ALL attempts by that user 
        # for that objectid, which we will clean up in the next step
        attempts = pd.merge(
            standard_df, 
            xapi[['userid', 'objectid', 'correct_responses_pattern', 'response']], 
            on=['userid', 'objectid'], 
            how='left'
        )
        
        # Only the latest attempt gets the xAPI text
        # We null out the response columns for any row where 'is_latest' is False
        attempts.loc[~attempts['is_latest'], ['correct_responses_pattern', 'response']] = None
        attempts.fillna({'correct_responses_pattern': "", 'response': ""}, inplace=True)
        
        # Drop the helper column to keep the DataFrame clean
        attempts.drop(columns=['is_latest'], inplace=True)
        
        return attempts
       

    def _process_hotspot_attempts(self, hotspot_df):
        """Aggregates hotspot clicks into 10-minute blocks and calculates custom scores."""
        if hotspot_df.empty:
            return pd.DataFrame()
            
        # This maps {objectid : required_clicks}
        # In the future, we will load this from a database!
        scoring_rules = {
            3: 4,
            21: 16
        }

        # Group clicks into 10-minute blocks
        first_click   = hotspot_df.groupby(['userid', 'objectid'])['timecreated'].transform('first')
        attempt_block = ((hotspot_df['timecreated'] - first_click) // pd.Timedelta('10min')).astype(int)
        
        # Aggregate blocks
        hs_processed = (
            hotspot_df.assign(attempt_block=attempt_block)
            .groupby(['userid', 'objectid', 'attempt_block'])
            .agg(timecreated=('timecreated', 'max'), number_clicks=('objectid', 'size'))
            .reset_index()
        )
        
        # Dynamic Vectorized Scoring
        hs_processed['result'] = 0.0  # Default score is 0
        
        # Map the required clicks to a temporary column based on the objectid
        hs_processed['required_clicks'] = hs_processed['objectid'].map(scoring_rules)
        
        # Create a single mask: "Does this object have a rule?" AND "Did they click enough times?"
        valid_mask = (
            hs_processed['required_clicks'].notna() & 
            (hs_processed['number_clicks'] >= hs_processed['required_clicks'])
        )
        
        # Apply the universal math formula all at once
        hs_processed.loc[valid_mask, 'result'] = (
            hs_processed.loc[valid_mask, 'required_clicks'] / 
            hs_processed.loc[valid_mask, 'number_clicks']
        ) * 10

        # Clean up temporary columns and add schema requirements
        hs_processed.drop(columns=['required_clicks'], inplace=True)
        hs_processed['response'] = ""
        hs_processed['correct_responses_pattern'] = ""

        return hs_processed
    
    
    def _create_task_map(self):
        """
        Creates a dictionary mapping Moodle integer IDs to internal Task IDs 
        """
        moodle_tasks = self.data.get_csv(TASK_CSV_PATH, columns=['id', 'name'])
        blueprint    = self.data.get_csv(COURSE_CSV_PATH, columns=['task_id', 'task'])
        merged = moodle_tasks.merge(blueprint, left_on='name', right_on='task', how='inner')
        task_prefix_map = merged.set_index('id')['task_id'].to_dict()
        
        return task_prefix_map
    
    
    

    def execute(self):
        """
        Extracts ALL graded learning task attempts (both successes and struggles).
        Handles JSON parsing, the Hotspot workarounds, and xAPI response merging in pure Pandas.
        """
        
        # Fetch Data from CSV-files and IDs of the tasks "Multiple Hotspots"
        logfile_df, xapi_df = self._fetch_data()
        hotspot_ids = self._extract_hotspot_task_ids()
        
        # Extract graded events from logfile
        graded_events = self._parse_graded_events(logfile_df)
        
        # Separate Standard Tasks and Hotspot Tasks
        is_hotspot        = graded_events['objectid'].isin(hotspot_ids)
        standard_attempts = graded_events[~is_hotspot].copy()
        hotspot_attempts  = graded_events[is_hotspot].copy()
        
        # Add information from xAPI to standard tasks and process hotspots
        standard_attempts = self._process_standard_attempts(standard_attempts, xapi_df)
        hotspot_attempts  = self._process_hotspot_attempts(hotspot_attempts)

        # Combine results
        all_attempts = pd.concat([standard_attempts, hotspot_attempts], ignore_index=True)
        
        # Create mappping for task ID
        task_prefix_map = self._create_task_map()
        
        # Map fields to the ATTEMPTED schema expectations
        all_attempts['score'] = all_attempts['result'].astype(float).round(1)
        all_attempts['passed'] = all_attempts['score'] >= 8.0
        all_attempts['student_response'] = all_attempts['response'].astype(str)
        all_attempts['correct_response'] = all_attempts['correct_responses_pattern'].astype(str)
        all_attempts['task_id'] = all_attempts['objectid'].astype(int).map(lambda x: task_prefix_map.get(x, "LT"))
        all_attempts['student_id'] = all_attempts['userid'].astype(str)
        all_attempts['timestamp'] = all_attempts['timecreated'].apply(lambda x: x.isoformat())
        
        # Construct the ID
        all_attempts['attempted_id'] = (
            "r_at_" + 
            all_attempts['student_id'] + "_" + 
            all_attempts['task_id'] + "_" + 
            all_attempts['timestamp']
        )
        
        # Drop extra columns to keep the dictionary clean, matching ONLY the schema
        columns_to_keep = [
            'attempted_id', 'timestamp', 'score', 'passed', 
            'student_response', 'correct_response', 'task_id', 'student_id'
        ]
        final_df = all_attempts[columns_to_keep]
        
        # Validate
        validator = PydanticValidator()
        validated_data = validator.validate_dataframe(final_df, "ATTEMPTED")
        
        return validated_data
        