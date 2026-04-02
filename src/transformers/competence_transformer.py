import pandas as pd
from src.config import COMPETENCE_CSV_PATH
from src.schema import SKILL, KNOWLEDGE, COMPETENCE


class SkillTransformer():
    """
    Reads csv and returns a list of validated Skill dictionaries.
    """
    def execute(self):
        df = pd.read_csv(COMPETENCE_CSV_PATH)
        validated_skills = []
        for _, row in df.iterrows():
            # Pydantic validates the row here!
            skill = SKILL(**row.to_dict()) 
            validated_skills.append(skill.model_dump())
        return validated_skills



class KnowledgeTransformer():
    """
    Reads csv and returns a list of validated Knowledge dictionaries.
    """
    def execute(self):
        df = pd.read_csv(COMPETENCE_CSV_PATH)
        validated_know = []
        for _, row in df.iterrows():
            know = KNOWLEDGE(**row.to_dict()) 
            validated_know.append(know.model_dump()) 
        return validated_know



class CompetenceTransformer():
    """
    Reads csv and returns a list of validated Knowledge dictionaries.
    """   
    def execute(self):
        df = pd.read_csv(COMPETENCE_CSV_PATH)
        validated_competence = []
        for _, row in df.iterrows():
            know = COMPETENCE(**row.to_dict()) 
            validated_competence.append(know.model_dump())
        return validated_competence
        





