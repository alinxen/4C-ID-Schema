from src.extractors.csv_extractor import CSVExtractor

class DataStore:
    """
    A centralized registry that extracts and caches DataFrames so they 
    are only loaded into memory once per pipeline run.
    """
    def __init__(self):
        self._cache = {}

    def get_csv(self, filepath, columns):
        # Create a unique cache key based on the filepath and requested columns
        col_key = tuple(columns) if columns else "ALL"
        cache_key = f"{filepath}_{col_key}"

        if cache_key not in self._cache:
            extractor = CSVExtractor(filepath, columns=columns)
            self._cache[cache_key] = extractor.extract()
            
        # Return a copy so transformers don't mutate the cached base data
        return self._cache[cache_key].copy()