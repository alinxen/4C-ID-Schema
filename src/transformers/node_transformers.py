from src.config import COMPETENCE_CSV_PATH


class NodeTransformer:
    """
    Base class for all node transformers to enforce consistentcy
    """
    DATA = {}

    def execute(self, extracted_data):
        """
        Default behavior for single-source transformers:
        Just return the data
        """
        
        return next(iter(extracted_data.values())).copy()
    
###############################################################################

class SkillTransformer(NodeTransformer):
    """
    Transforms raw competence data into a structure suitable for SKILL nodes.
    """
    DATA = {
        "skills": (COMPETENCE_CSV_PATH, ['skill_id', 'skill_title', 'skill_group_id', 'skill_group_title']) }


