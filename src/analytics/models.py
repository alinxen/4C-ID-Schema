from neomodel import (
    StructuredNode, 
    StringProperty, 
    IntegerProperty, 
    FloatProperty, 
    BooleanProperty, 
    RelationshipTo, 
    StructuredRel
)

# =================================================
# 1. RELATIONSHIP MODELS (Edges with Properties)
# =================================================

class PracticesRel(StructuredRel):
    practices_id = StringProperty(unique_index=True)
    cognitive_dimension = StringProperty()

class AppliesRel(StructuredRel):
    applies_id = StringProperty(unique_index=True)
    knowledge_dimension = StringProperty()

class AttemptedRel(StructuredRel):
    attempted_id = StringProperty(unique_index=True)
    timestamp = StringProperty()
    score = FloatProperty()
    passed = BooleanProperty()
    student_response = StringProperty()
    correct_response = StringProperty()

class TackledRel(StructuredRel):
    tackled_id = StringProperty(unique_index=True)
    start_time = StringProperty()
    end_time = StringProperty()

class ReviewedConsultedRel(StructuredRel):
    # Used for both REVIEWED and CONSULTED since properties match
    rel_id = StringProperty(unique_index=True) # Replaces reviewed_id/consulted_id
    start_time = StringProperty()
    end_time = StringProperty()
    time_spent = StringProperty()
    completion_time = StringProperty()

class StudiedRel(StructuredRel):
    studied_id = StringProperty(unique_index=True)
    start_time = StringProperty()
    end_time = StringProperty()
    duration = StringProperty()

class FinishedRel(StructuredRel):
    finished_id = StringProperty(unique_index=True)
    completion_time = StringProperty()
    completion_type = StringProperty()
    score = StringProperty()


# =================================================
# 2. NODE MODELS
# =================================================

class Skill(StructuredNode):
    __label__ = "Skill"
    skill_id = StringProperty(unique_index=True, required=True)
    skill_title = StringProperty()
    skill_group_id = StringProperty()
    skill_group_title = StringProperty()

class Knowledge(StructuredNode):
    __label__ = "Knowledge"
    knowledge_id = StringProperty(unique_index=True, required=True)
    knowledge_title = StringProperty()
    knowledge_group_id = StringProperty()
    knowledge_group_title = StringProperty()

class Competence(StructuredNode):
    __label__ = "Competence"
    competence_id = StringProperty(unique_index=True, required=True)
    competence_title = StringProperty()
    competence_group_id = StringProperty()
    competence_group = StringProperty()
    
    # Relationships
    requires_skills = RelationshipTo('Skill', 'requires_s')
    requires_knowledge = RelationshipTo('Knowledge', 'requires_k')

class SupportiveInformation(StructuredNode):
    __label__ = "Supportive_Information"
    si_id = StringProperty(unique_index=True, required=True)
    course_id = IntegerProperty()
    si_title = StringProperty()

class ProceduralInformation(StructuredNode):
    __label__ = "Procedural_Information"
    pi_id = StringProperty(unique_index=True, required=True)
    course_id = IntegerProperty()
    pi_title = StringProperty()

class PartTaskPractice(StructuredNode):
    __label__ = "Part_Task_Practice"
    practice_id = StringProperty(unique_index=True, required=True)
    practice_title = StringProperty()
    
    # Relationships
    rehearses = RelationshipTo('ProceduralInformation', 'rehearses')

class LearningTask(StructuredNode):
    __label__ = "Learning_Task"
    task_id = StringProperty(unique_index=True, required=True)
    course_id = IntegerProperty()
    task_title = StringProperty()
    task_type = StringProperty()
    
    # Relationships
    develops = RelationshipTo('Competence', 'develops')
    practices = RelationshipTo('Skill', 'practices', model=PracticesRel)
    applies = RelationshipTo('Knowledge', 'applies', model=AppliesRel)
    cues = RelationshipTo('ProceduralInformation', 'cues')
    references = RelationshipTo('SupportiveInformation', 'references')

class TaskClass(StructuredNode):
    __label__ = "Task_Class"
    task_class_id = StringProperty(unique_index=True, required=True)
    task_class = StringProperty()
    
    # Relationships
    groups = RelationshipTo('LearningTask', 'groups')
    provides = RelationshipTo('SupportiveInformation', 'provides')
    offers = RelationshipTo('ProceduralInformation', 'offers')
    includes = RelationshipTo('PartTaskPractice', 'includes')

class LearningSession(StructuredNode):
    __label__ = "Learning_Session"
    session_id = StringProperty(unique_index=True, required=True)
    start_time = StringProperty()
    end_time = StringProperty()
    student_id = IntegerProperty()
    rds_ID = StringProperty()
    
    # Relationships
    tackled = RelationshipTo('LearningTask', 'tackled', model=TackledRel)
    reviewed = RelationshipTo('SupportiveInformation', 'reviewed', model=ReviewedConsultedRel)
    consulted = RelationshipTo('ProceduralInformation', 'consulted', model=ReviewedConsultedRel)

class Student(StructuredNode):
    __label__ = "Student"
    student_id = StringProperty(unique_index=True, required=True)
    username = StringProperty()
    firstname = StringProperty()
    lastname = StringProperty()
    email = StringProperty()
    
    # Relationships
    attempted = RelationshipTo('LearningTask', 'attempted', model=AttemptedRel)
    finished = RelationshipTo('LearningTask', 'finished', model=FinishedRel)
    studied = RelationshipTo('LearningSession', 'studied', model=StudiedRel)