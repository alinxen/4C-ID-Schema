import pandas as pd
from src.schema import TACKLED, REVIEWED, CONSULTED, STUDIED, FINISHED
from src.config import LOGFILE_CSV_PATH, TASK_CSV_PATH, COURSE_CSV_PATH, PAGES_CSV_PATH, COMPLETED_CSV_PATH, COURSE_MODULE_CSV_PATH, GRADE_GRADES_CSV_PATH
from datetime import timedelta



class TackledTransformer:
    """
    Reads the raw logfile, calculates sessions inline, calculates accurate 
    task durations, and returns a clean list of TACKLED relationship dictionaries.
    """

    def execute(self):
        df_raw = pd.read_csv(LOGFILE_CSV_PATH)
        if df_raw.empty:
            return []

        df_clean = self._prepare_data(df_raw)
        tackled_relations = self._process_tackled_relations(df_clean)
        
        return tackled_relations

    def _prepare_data(self, df):
        """Clean data globally, align timezones, and sort chronologically."""
        df = df[['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']]
        df['objectid'] = pd.to_numeric(df['objectid'], errors='coerce').astype('Int64')
        df['timecreated'] = pd.to_datetime(df['timecreated'] + 3600, unit='s')
        
        # Sort exactly as the LearningSessionTransformer does
        df = df.sort_values(by=['userid', 'timecreated']).reset_index(drop=True)
        df = df[df['userid'] >= 3]
        
        return df

    def _process_tackled_relations(self, df: pd.DataFrame):
        validated_data = []
        
        tasks_map_df = pd.read_csv(TASK_CSV_PATH)
        task_prefix_map = tasks_map_df.set_index('id')['name'].astype(str).str[:2].to_dict()
        

        for user_id, user_logs in df.groupby('userid'):
            current_login_time = None
            last_action_time   = None
            user_sessions      = []

            # 1. Rebuild the exact session windows for this user
            for row in user_logs.itertuples():
                if row.action == 'loggedin':
                    if current_login_time is not None:
                        inferred_logout = last_action_time + timedelta(minutes=2)
                        user_sessions.append((current_login_time, inferred_logout))
                    current_login_time = row.timecreated

                elif row.action == 'loggedout':
                    if current_login_time is not None:
                        user_sessions.append((current_login_time, row.timecreated))
                        current_login_time = None

                last_action_time = row.timecreated

            if current_login_time is not None:
                inferred_logout = last_action_time + timedelta(minutes=2)
                user_sessions.append((current_login_time, inferred_logout))

            # 2. Process tasks within those established sessions
            for login, logout in user_sessions:
                session_id = f"session_{user_id}_{login.strftime('%Y-%m-%d %H:%M:%S')}"
                
                # Slice logs for this specific session window
                session_mask = (user_logs['timecreated'] >= login) & (user_logs['timecreated'] <= logout)
                session_logs = user_logs[session_mask]
                
                # Filter for ALL 'viewed' actions to calculate accurate exit times
                views_mask = session_logs['action'] == 'viewed'
                session_views = session_logs[views_mask].copy()
                
                if session_views.empty:
                    continue
                
                # The end time of a view is the start time of the NEXT view
                session_views['end_time'] = session_views['timecreated'].shift(-1)
                
                # The last view in the session ends when the session ends
                col_idx = session_views.columns.get_loc('end_time')
                session_views.iloc[-1, col_idx] = logout
                
                # NOW filter down strictly to Learning Tasks
                task_mask = session_views['eventname'] == r'\mod_hvp\event\course_module_viewed'
                session_tasks = session_views[task_mask]
                
                
                
                # 3. Map to Pydantic schema
                for _, task_row in session_tasks.iterrows():
                    start_str = task_row['timecreated'].strftime('%Y-%m-%d %H:%M:%S')
                    end_str = task_row['end_time'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    obj_int = int(task_row['objectid'])
                    prefix = task_prefix_map.get(obj_int, "LT")
                    record = {
                        "tackled_id": f"tackled_{user_id}_{prefix}_{start_str}",
                        "session_id": session_id,
                        "task_id": f"{prefix}",
                        "start_time": start_str,
                        "end_time": end_str
                    }
                    validated_data.append(TACKLED(**record).model_dump())
  
        return validated_data
    



class ReviewedTransformer:
    """
    Processes supportive information views (mod_page), applies title-to-ID mapping,
    checks completion status, and returns validated REVIEWED relationships for the graph.
    """

    def execute(self):
        # 1. Load files
        df_raw = pd.read_csv(LOGFILE_CSV_PATH)
        if df_raw.empty:
            return []

        # 2. Prepare the mappings
        material_id_map = self._prepare_material_mapping()
        
        # NEW: Prepare completion mapping
        completed_set = self._prepare_completion_mapping()

        # 3. Clean log data
        df_clean = self._prepare_data(df_raw)
        
        # 4. Generate relationships
        # NEW: Pass completed_set into the processor
        reviewed_relations = self._process_reviewed_relations(df_clean, material_id_map, completed_set)
        
        return reviewed_relations

    def _prepare_material_mapping(self):
        """Builds a lookup dictionary: { original_id: mapped_si_id }"""
        pages = pd.read_csv(PAGES_CSV_PATH, usecols=['id', 'name'], dtype={'id': str})
        
        mapping = pd.read_csv(COURSE_CSV_PATH, usecols=['si_id', 'supportive_title'], dtype={'si_id': str})
        title_to_id_map = mapping.set_index('supportive_title')['si_id'].to_dict()
        
        pages = pages[pages['name'].str.startswith("(SI)", na=False)].copy()
        pages['mapped_id'] = pages['name'].map(title_to_id_map).fillna(pages['id'])
        
        
        return pages.set_index('id')['mapped_id'].to_dict()

    def _prepare_completion_mapping(self):
        """
        Builds a dictionary of {(userid, original_page_id): completion_timestamp_string}
        representing when the user explicitly marked materials as completed.
        """
        try:
            completions = pd.read_csv(COMPLETED_CSV_PATH)
            modules = pd.read_csv(COURSE_MODULE_CSV_PATH, usecols=['id', 'module', 'instance'])
            
            # Filter for successful completions (completionstate == 1)
            completions = completions[completions['completionstate'] == 1]
            
            # Merge to get the actual page ID ('instance')
            df_merged = completions.merge(modules, how='inner', left_on='coursemoduleid', right_on='id')
            
            # Filter for mod_page (module == 17)
            completed_pages = df_merged[df_merged['module'] == 17].copy()
            
            # Convert the UNIX timestamp to a formatted string (matching legacy logic)
            completed_pages['timemodified'] = pd.to_datetime(completed_pages['timemodified'], unit='s')
            completed_pages['completion_time_str'] = completed_pages['timemodified'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Ensure the instance ID is a string so it matches our lookup keys later
            completed_pages['instance_str'] = completed_pages['instance'].astype(str)
            
            # Return a dictionary: {(userid, 'instance_id'): 'YYYY-MM-DDTHH:MM:SS'}
            return completed_pages.set_index(['userid', 'instance_str'])['completion_time_str'].to_dict()
            
        except FileNotFoundError:
            print("Completion files not found. Defaulting to no completion timestamps.")
            return {}

    def _prepare_data(self, df):
        """Standard log cleaning and student filtering."""
        df = df[['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']]
        df['objectid'] = df['objectid'].astype(str)
        df['timecreated'] = pd.to_datetime(df['timecreated'] + 3600, unit='s')
        df = df.sort_values(by=['userid', 'timecreated']).reset_index(drop=True)
        return df[df['userid'] >= 3]

    def _process_reviewed_relations(self, df, material_id_map, completed_dict):
        validated_data = []

        for user_id, user_logs in df.groupby('userid'):
            # --- Session State Machine ---
            current_login_time = None
            last_action_time   = None
            user_sessions      = []

            for row in user_logs.itertuples():
                if row.action == 'loggedin':
                    if current_login_time is not None:
                        user_sessions.append((current_login_time, last_action_time + timedelta(minutes=2)))
                    current_login_time = row.timecreated
                elif row.action == 'loggedout':
                    if current_login_time is not None:
                        user_sessions.append((current_login_time, row.timecreated))
                        current_login_time = None
                last_action_time = row.timecreated
            
            if current_login_time is not None:
                user_sessions.append((current_login_time, last_action_time + timedelta(minutes=2)))

            # --- Process Views within Sessions ---
            for login, logout in user_sessions:
                session_id = f"session_{user_id}_{login.strftime('%Y-%m-%d %H:%M:%S')}"
                
                session_mask = (user_logs['timecreated'] >= login) & (user_logs['timecreated'] <= logout)
                session_views = user_logs[session_mask & (user_logs['action'] == 'viewed')].copy()
                
                if session_views.empty:
                    continue
                
                session_views['end_time'] = session_views['timecreated'].shift(-1)
                session_views.iloc[-1, session_views.columns.get_loc('end_time')] = logout
                
                page_mask = session_views['eventname'] == r'\mod_page\event\course_module_viewed'
                session_pages = session_views[page_mask]
                
                for _, page_row in session_pages.iterrows():
                    original_id = str(int(float(page_row['objectid'])))
                    
                    material_id = material_id_map.get(original_id)
                    
                    if not material_id:
                        continue
                    
                    start_str = page_row['timecreated'].strftime('%Y-%m-%d %H:%M:%S')
                    end_str = page_row['end_time'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    time_spent_str = str((page_row['end_time'] - page_row['timecreated']).total_seconds() / 60.0)
                    
                    # NEW: Fetch the completion timestamp (returns None if not completed)
                    completion_time = str(completed_dict.get((user_id, original_id)))
                    
                    record = {
                        "reviewed_id": f"reviewed_{user_id}_{material_id}_{start_str}",
                        "session_id": session_id,
                        "si_id": material_id,
                        "start_time": start_str,
                        "end_time": end_str,
                        "time_spent": time_spent_str,
                        "completion_time": completion_time  
                    }
                    validated_data.append(REVIEWED(**record).model_dump())
        return validated_data
    
    
    

class ConsultedTransformer:
    """
    Processes procedural information views (mod_page), applies PI-title-to-ID mapping,
    checks completion status, and returns validated CONSULTED relationships for the graph.
    """

    def execute(self):
        # 1. Load files
        df_raw = pd.read_csv(LOGFILE_CSV_PATH)
        if df_raw.empty:
            return []

        # 2. Prepare the mappings
        material_id_map = self._prepare_procedural_mapping()
        
        # 3. Prepare completion mapping (Mirrored from ReviewedTransformer)
        completed_dict = self._prepare_completion_mapping()

        # 4. Clean logs
        df_clean = self._prepare_data(df_raw)
        
        # 5. Generate relationships
        consulted_relations = self._process_consulted_relations(df_clean, material_id_map, completed_dict)
        
        return consulted_relations

    def _prepare_procedural_mapping(self):
            """Builds a lookup dictionary: { original_id (instance): mapped_pi_id }"""
            pages = pd.read_csv(PAGES_CSV_PATH, usecols=['id', 'name'], dtype={'id': str})
            
            mapping = pd.read_csv(COURSE_CSV_PATH, usecols=['pi_id', 'procedural_title'], dtype={'pi_id': str})
            title_to_id_map = mapping.set_index('procedural_title')['pi_id'].to_dict()
    
            pages_pi = pages[pages['name'].str.startswith("(PI)", na=False)].copy()
            # Apply the mapping (fallback to IM_id if it's a (PI) page but missing from your custom mapping)
            pages_pi['mapped_id'] = pages_pi['name'].map(title_to_id_map).fillna("IM_" + pages_pi['id'])
    
            # Return dictionary keyed by instance ID
            return pages_pi.set_index('id')['mapped_id'].to_dict()

    def _prepare_completion_mapping(self):
            """
            Builds a dictionary of {(userid, original_page_id): completion_timestamp_string}
            representing when the user explicitly marked materials as completed.
            """
            try:
                completions = pd.read_csv(COMPLETED_CSV_PATH)
                # FIX: Ensure 'instance' is loaded here
                modules = pd.read_csv(COURSE_MODULE_CSV_PATH, usecols=['id', 'module', 'instance'])
                
                # Filter for successful completions (completionstate == 1)
                completions = completions[completions['completionstate'] == 1]
                
                # Merge to get the actual page ID ('instance')
                df_merged = completions.merge(modules, how='inner', left_on='coursemoduleid', right_on='id')
                completed_pages = df_merged[df_merged['module'] == 17].copy()
                
                # Convert the UNIX timestamp to a formatted string
                completed_pages['timemodified'] = pd.to_datetime(completed_pages['timemodified'], unit='s')
                completed_pages['completion_time_str'] = completed_pages['timemodified'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # FIX: Key by instance_str instead of cmid_str
                completed_pages['instance_str'] = completed_pages['instance'].astype(str)
                
                return completed_pages.set_index(['userid', 'instance_str'])['completion_time_str'].to_dict()
                
            except FileNotFoundError:
                print("Completion files not found. Defaulting to no completion timestamps.")
                return {}

    def _prepare_data(self, df):
        """Standard log cleaning."""
        df = df[['id', 'eventname', 'action', 'objectid', 'userid', 'timecreated']]
        df['objectid'] = df['objectid'].astype(str)
        df['timecreated'] = pd.to_datetime(df['timecreated'] + 3600, unit='s')
        df = df.sort_values(by=['userid', 'timecreated']).reset_index(drop=True)
        return df[df['userid'] >= 3]

    def _process_consulted_relations(self, df, material_id_map, completed_dict):
        validated_data = []

        for user_id, user_logs in df.groupby('userid'):
            # --- Session Calculation ---
            current_login_time = None
            last_action_time   = None
            user_sessions      = []

            for row in user_logs.itertuples():
                if row.action == 'loggedin':
                    if current_login_time is not None:
                        user_sessions.append((current_login_time, last_action_time + timedelta(minutes=2)))
                    current_login_time = row.timecreated
                elif row.action == 'loggedout':
                    if current_login_time is not None:
                        user_sessions.append((current_login_time, row.timecreated))
                        current_login_time = None
                last_action_time = row.timecreated
            
            if current_login_time is not None:
                user_sessions.append((current_login_time, last_action_time + timedelta(minutes=2)))

            # --- Relationship Mapping ---
            for login, logout in user_sessions:
                # Use SPACE to match LearningSession nodes
                session_id = f"session_{user_id}_{login.strftime('%Y-%m-%d %H:%M:%S')}"
                
                session_mask = (user_logs['timecreated'] >= login) & (user_logs['timecreated'] <= logout)
                session_views = user_logs[session_mask & (user_logs['action'] == 'viewed')].copy()
                
                if session_views.empty:
                    continue
                
                session_views['end_time'] = session_views['timecreated'].shift(-1)
                session_views.iloc[-1, session_views.columns.get_loc('end_time')] = logout
                
                # Filter for PI (mod_page)
                page_mask = session_views['eventname'] == r'\mod_page\event\course_module_viewed'
                session_pages = session_views[page_mask]
                
                for _, page_row in session_pages.iterrows():
                    original_id = str(int(float(page_row['objectid'])))
                    
                    # Try to fetch mapped PI ID
                    material_id = material_id_map.get(original_id)
                    
                    # If it's missing from the map, it's not a Procedural Information page (skip it)
                    if not material_id:
                        continue
                    
                    start_str = page_row['timecreated'].strftime('%Y-%m-%d %H:%M:%S')
                    end_str = page_row['end_time'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Calculate duration
                    time_spent_str = str((page_row['end_time'] - page_row['timecreated']).total_seconds() / 60.0)
                    
                    # Fetch completion timestamp
                    completion_time = str(completed_dict.get((user_id, original_id)))
                    
                    record = {
                        "consulted_id": f"consulted_{user_id}_{material_id}_{start_str}",
                        "session_id": session_id,
                        "pi_id": material_id,
                        "start_time": start_str,
                        "end_time": end_str,
                        "time_spent": time_spent_str,
                        "completion_time": completion_time
                    }
                    validated_data.append(CONSULTED(**record).model_dump())
        return validated_data
    
    
    

class StudiedTransformer:
    """
    Processes user logs to reconstruct learning sessions and returns 
    validated STUDIED relationships connecting Students to Learning Sessions.
    """

    def execute(self):
        # 1. Load files
        df_raw = pd.read_csv(LOGFILE_CSV_PATH)
        if df_raw.empty:
            return []

        # 2. Clean log data
        df_clean = self._prepare_data(df_raw)
        
        # 3. Generate relationships
        studied_relations = self._process_studied_relations(df_clean)
        
        return studied_relations

    def _prepare_data(self, df):
        """Standard log cleaning and student filtering."""
        # We only need action, userid, and timecreated to build sessions
        df = df[['action', 'userid', 'timecreated']]
        df['timecreated'] = pd.to_datetime(df['timecreated'] + 3600, unit='s')
        df = df.sort_values(by=['userid', 'timecreated']).reset_index(drop=True)
        
        # Filter out guest and admin accounts (IDs 1 and 2)
        return df[df['userid'] >= 3]

    def _process_studied_relations(self, df):
        validated_data = []

        for user_id, user_logs in df.groupby('userid'):
            # --- Session State Machine ---
            current_login_time = None
            last_action_time   = None
            user_sessions      = []

            for row in user_logs.itertuples():
                if row.action == 'loggedin':
                    if current_login_time is not None:
                        # Close previous session that missed a logout
                        user_sessions.append((current_login_time, last_action_time + timedelta(minutes=2)))
                    current_login_time = row.timecreated
                elif row.action == 'loggedout':
                    if current_login_time is not None:
                        # Close session normally
                        user_sessions.append((current_login_time, row.timecreated))
                        current_login_time = None
                last_action_time = row.timecreated
            
            # Close any dangling session at the very end of the user's logs
            if current_login_time is not None:
                user_sessions.append((current_login_time, last_action_time + timedelta(minutes=2)))

            # --- Relationship Mapping ---
            for login, logout in user_sessions:
                start_str = login.strftime('%Y-%m-%d %H:%M:%S')
                end_str = logout.strftime('%Y-%m-%d %H:%M:%S')
                
                # Match the exact session_id format used in Reviewed/Consulted Transformers
                session_id = f"session_{user_id}_{start_str}"
                
                # I calculated the total session duration for you as a string, 
                # just in case you want it on the edge for analytics!
                duration_minutes = str((logout - login).total_seconds() / 60.0)

                record = {
                    "studied_id": f"studied_{user_id}_{start_str}",
                    "student_id": str(user_id),
                    "session_id": session_id,
                    "start_time": start_str,
                    "end_time": end_str,
                    "duration": duration_minutes
                }
                
                # Assuming you have a Pydantic model named STUDIED
                validated_data.append(STUDIED(**record).model_dump())
                validated_data.append(record)
        return validated_data
    
    