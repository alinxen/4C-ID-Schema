import pandas as pd

class CSVExtractor:
    
    def __init__(self, filepath, columns = None):
        self.filepath = filepath
        self.columns  = columns

    def extract(self):
        """
        Extracts the CSV. If columns are specified, only those are loaded.
        """
        try:
            df = pd.read_csv(self.filepath, usecols=self.columns)
            return df
        
        except FileNotFoundError:
            print(f"Error: Could not find file at {self.filepath}")
            raise
            
        except ValueError as e:
            print(f"Error filtering columns in {self.filepath}: {e}")
            raise