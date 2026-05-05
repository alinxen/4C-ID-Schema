import pandas as pd
from src.config import GRADE_GRADES_CSV_PATH, COMPLETED_CSV_PATH, COURSE_MODULE_CSV_PATH, TASK_CSV_PATH, COURSE_CSV_PATH

class FinishedTransformer:
    """
    Processes grades and manual completions to generate FINISHED relationships
    connecting Students to Learning Tasks.
    """
    
    DATA = {
        "grades": (GRADE_GRADES_CSV_PATH, ['userid', 'itemid', 'rawgrade', 'finalgrade', 'timemodified']),
        "completions": (COMPLETED_CSV_PATH, ['userid', 'coursemoduleid', 'completionstate', 'timemodified']),
        "modules": (COURSE_MODULE_CSV_PATH, ['id', 'module', 'instance']),
        "moodle_tasks": (TASK_CSV_PATH, ['id', 'name']),
        "blueprint": (COURSE_CSV_PATH, ['task_id', 'task'])
    }

    def execute(self, extracted_data, attempted_df=None):
        # 1. Get completions via graded attempts
        df_attempts = self._get_attempt_completions(extracted_data)
        
        # 2. Get completions via manual 'Mark as done' button
        df_buttons = self._get_button_completions(extracted_data)
        
        # 3. Combine and resolve duplicates (Prioritize Attempts over Buttons)
        df_combined = self._combine_completions(df_attempts, df_buttons)
        
        if df_combined.empty:
            return self._process_finished_relations(df_combined)

        # 4. MAP TO NEW BLUEPRINT IDs (crucial to do this before merging Hotspots)
        task_map = self._create_task_map(extracted_data)
        # Convert raw instance ID to new blueprint task_id
        df_combined['task_id_raw'] = df_combined['task_id'].astype(int)
        df_combined['task_id'] = df_combined['task_id_raw'].map(lambda x: task_map.get(x, "LT"))

        # 5. FIX HOTSPOTS: Now that IDs match Attempted, overwrite broken Moodle grades
        if attempted_df is not None:
            df_combined = self._fix_hotspot_scores(df_combined, attempted_df)
            
        # 6. Generate relationships as a strict DataFrame
        finished_df = self._process_finished_relations(df_combined)
        
        return finished_df

    def _create_task_map(self, extracted_data):
        """Creates a dictionary mapping Moodle integer IDs to internal Task IDs."""
        moodle_tasks = extracted_data["moodle_tasks"].copy()
        blueprint = extracted_data["blueprint"].copy()
        merged = moodle_tasks.merge(blueprint, left_on='name', right_on='task', how='inner')
        return merged.set_index('id')['task_id'].to_dict()

    def _get_attempt_completions(self, extracted_data):
        """Extracts completed learning tasks based on graded attempts."""
        try:
            grades = extracted_data["grades"].copy()
            # Filter out entries where the user hasn't made an attempt yet
            grades = grades.dropna(subset=['timemodified', 'rawgrade']).copy()
            
            # LEGACY LOGIC: itemids in m_grade_grades are offset by 2 from the actual HVP IDs
            grades['task_id'] = (grades['itemid'] - 2).astype(int).astype(str)
            grades['type'] = 'attempt'
            grades['score'] = grades['finalgrade'].round(1)
            
            grades['completion_time'] = pd.to_datetime(grades['timemodified'], unit='s').dt.strftime('%Y-%m-%dT%H:%M:%S')
            
            return grades[['userid', 'task_id', 'completion_time', 'type', 'score']]
        except FileNotFoundError:
            print(f"Warning: Attempt file not found at {GRADE_GRADES_CSV_PATH}")
            return pd.DataFrame()

    def _get_button_completions(self, extracted_data):
        """Extracts completed learning tasks based on the 'Mark as done' button."""
        try:
            completions = extracted_data["completions"].copy()
            modules = extracted_data["modules"].copy()
            
            # Filter for successful completions
            completions = completions[completions['completionstate'] == 1]
            
            # Merge to filter only for HVP elements (module 12)
            df_merged = completions.merge(modules, how='inner', left_on='coursemoduleid', right_on='id')
            df_tasks = df_merged[df_merged['module'] == 12].copy()
            
            # For HVP modules, the 'instance' column holds the exact HVP task ID
            df_tasks['task_id'] = df_tasks['instance'].astype(int).astype(str)
            df_tasks['type'] = 'button'
            df_tasks['score'] = None
            
            df_tasks['completion_time'] = pd.to_datetime(df_tasks['timemodified'], unit='s').dt.strftime('%Y-%m-%dT%H:%M:%S')
            
            return df_tasks[['userid', 'task_id', 'completion_time', 'type', 'score']]
        except FileNotFoundError:
            print("Warning: Completion files not found.")
            return pd.DataFrame()

    def _combine_completions(self, df_attempts, df_buttons):
        """Combines both sources and ensures only one edge exists per user-task."""
        df_combined = pd.concat([df_attempts, df_buttons], ignore_index=True)
        if df_combined.empty:
            return df_combined
        
        # Sorting alphabetically by 'type' guarantees 'attempt' comes before 'button'.
        df_combined = df_combined.sort_values('type')
        df_combined = df_combined.drop_duplicates(subset=['userid', 'task_id'], keep='first')
        
        return df_combined

    def _fix_hotspot_scores(self, df_combined, attempted_df):
        """Overwrites broken Moodle hotspot scores with our mathematically correct Attempted scores."""
        # Get the latest calculated score for every user-task combo
        latest_attempts = attempted_df.sort_values('timestamp').groupby(['student_id', 'task_id']).last().reset_index()
        
        # Merge calculated scores onto Moodle grades using the mapped task_id
        merged = pd.merge(
            df_combined, 
            latest_attempts[['student_id', 'task_id', 'score']], 
            left_on=['userid', 'task_id'], 
            right_on=['student_id', 'task_id'],
            how='left',
            suffixes=('', '_calculated')
        )
        
        # Overwrite if a calculated score exists
        merged['score'] = merged['score_calculated'].fillna(merged['score'])
        
        # Clean up temporary merge columns
        if 'student_id' in merged.columns:
            merged = merged.drop(columns=['student_id'])
        return merged.drop(columns=['score_calculated'])

    def _process_finished_relations(self, df):
        """Vectorized mapping to the target schema DataFrame."""
        if df.empty:
            return pd.DataFrame(columns=[
                'finished_id', 'student_id', 'task_id', 
                'completion_time', 'completion_type', 'score'
            ])

        # Filter out guest and admin accounts (IDs 1 and 2)
        df['userid'] = pd.to_numeric(df['userid'], errors='coerce')
        df = df[~df['userid'].isin([1, 2])].copy()

        # Map to standard schema names
        df['student_id'] = df['userid'].astype(int).astype(str)
        df['completion_type'] = df['type'].astype(str)

        # Construct the unique ID matching your new structure: finished_{userid}_{task_id}
        df['finished_id'] = "finished_" + df['student_id'] + "_" + df['task_id']

        # Clean scores for Pydantic (empty string if no score)
        def clean_score(val):
            if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '<na>', '']:
                return ""
            return str(val)

        df['score'] = df['score'].apply(clean_score)

        columns_to_keep = [
            'finished_id', 'student_id', 'task_id', 
            'completion_time', 'completion_type', 'score'
        ]
        
        final_df = df[columns_to_keep].copy()
        final_df = final_df.astype(str)
        
        return final_df