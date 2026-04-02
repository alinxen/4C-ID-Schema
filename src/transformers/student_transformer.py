import pandas as pd
from datetime import timedelta
from src.schema import LEARNING_SESSION, STUDENT
from src.config import LOGFILE_CSV_PATH, USER_CSV_PATH



class StudentTransformer():
    """
    Reads csv and returns a list of validated Skill dictionaries.
    """
    def execute(self):
        df = (pd.read_csv(USER_CSV_PATH,  usecols=['id', 'username', 'firstname','lastname','email'])
                 .rename(columns={'id':'student_id'})
                 )
        # Drop admin and system
        df = df[df['student_id'] >= 3]
        df['student_id'] = df['student_id'].astype(str)
        
        validated_user = []
        for _, row in df.iterrows():
            # Pydantic validates the row here!
            user = STUDENT(**row.to_dict()) 
            validated_user.append(user.model_dump())
        return validated_user



class LearningSessionTransformer:
    """
    Reads the raw logfile, calculates sessions for all students,
    and returns a clean list of validated Pydantic model dictionaries ready for DB insertion.
    """

    def execute(self):
        """Extract and validate data"""
        df_raw            = pd.read_csv(LOGFILE_CSV_PATH)
        df_clean          = self._prepare_data(df_raw)
        learning_sessions = self._process_user_sessions(df_clean)
        
        return learning_sessions


    def _prepare_data(self, df):
        """Adjust timezone, sort chronologically, and remove system/admin accounts"""
        df['timecreated'] = pd.to_datetime(df['timecreated'] + 3600, unit='s')
        df = df.sort_values(by=['userid', 'timecreated']).reset_index(drop=True)
        df = df[df['userid'] >= 3]
        
        return df


    def _process_user_sessions(self, df: pd.DataFrame):
        """Iterates through all users and applies the session state machine logic"""
        learning_sessions = []

        for user_id, user_logs in df.groupby('userid'):
            current_login_time = None
            last_action_time   = None

            for row in user_logs.itertuples():
                if row.action == 'loggedin':
                    # Close dangling previous session if needed
                    if current_login_time is not None:
                        inferred_logout = last_action_time + timedelta(minutes=2)
                        self._append_session(learning_sessions, user_id, current_login_time, inferred_logout)
                    
                    current_login_time = row.timecreated

                elif row.action == 'loggedout':
                    # Close session normally
                    if current_login_time is not None:
                        self._append_session(learning_sessions, user_id, current_login_time, row.timecreated)
                        current_login_time = None  # Reset state

                # Continuously update the last action time
                last_action_time = row.timecreated

            # Handle a dangling login at the very end of the user's log history
            if current_login_time is not None:
                inferred_logout = last_action_time + timedelta(minutes=2)
                self._append_session(learning_sessions, user_id, current_login_time, inferred_logout)

        return learning_sessions


    def _append_session(self, sessions_list, user_id: int, start_time: pd.Timestamp, end_time: pd.Timestamp):
        """Helper to format IDs, validate the Pydantic model, and append to the list as a dict."""
        
        start_time_str = start_time.isoformat()
        end_time_str = end_time.isoformat()
        
        session = LEARNING_SESSION(
            session_id=f"session_{user_id}_{start_time}",
            start_time=start_time_str,
            end_time=end_time_str,
            student_id=user_id,
            rds_ID=f"r_ds_{user_id}_{start_time}"
        )
        
        sessions_list.append(session.model_dump())




















