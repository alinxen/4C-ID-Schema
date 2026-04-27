from pydantic import ValidationError
import src.schema as schema
import logging



class PydanticValidator:

    def _get_schema(self, model_name):
        """Fetch the Pydantic model"""
        model = getattr(schema, model_name, None)
        
        if model is None:
            raise ValueError(f"Schema '{model_name}' not found in graph_schema.py")
            
        return model


    def validate_dataframe(self, dataframe, model_name):
        """
        Validates a DataFrame against a Pydantic schema.
        Expects the DataFrame columns to match the schema's field names.
        """
        # Convert DataFrame to a list of dictionaries
        records = dataframe.to_dict(orient='records')
        validated_data = []
        
        # Fetch Model
        model = self._get_schema(model_name)
        
        try:
            # Iterate and validate 
            for index, record in enumerate(records):
                model_instance = model(**record)
                validated_data.append(model_instance.model_dump())
                
        except ValidationError as e:
            # BUG FIXED: Using 'model.__name__' instead of 'schema.__name__'
            logging.error(f"Validation failed for schema '{model.__name__}' at row {index}.")
            logging.error(f"Problematic Data: {record}")
            raise e 
            
        return validated_data