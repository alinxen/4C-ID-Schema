import pandas as pd

class DataExtractor:
    
    def __init__(self, required_data):
        self.required_data = required_data

    def extract(self):
        """
        Iterates through requirements and returns a dictionary of DataFrames.
        { filepath: DataFrame }
        """
        extracted_data = {}
        
        for alias, (filepath, columns) in self.required_data.items():
            try:
              
                extracted_data[alias] = pd.read_csv(filepath, usecols=columns)
                
            except FileNotFoundError:
                print(f"{alias}: Error: Could not find file at {filepath}")
                raise
            except ValueError as e:
                print(f"{alias}: Error filtering columns in {filepath}: {e}")
                raise
            except Exception as e:
                print(f"{alias}: Unexpected error loading {filepath}: {e}")
                raise
                
        return extracted_data