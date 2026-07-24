from pydantic import BaseModel, Field
from typing import ClassVar


# -------------------------------------------------
# NODES of the 4C/ID-SCHEMA
# -------------------------------------------------

class COMPETENCE(BaseModel):
    label                   : ClassVar[str] = "Competence"
    competence_id           : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    competence_title        : str 
    competence_description  : str
    competence_group_id     : str 
    competence_group        : str    

class SKILL(BaseModel):
    label                   : ClassVar[str] = "Skill"
    skill_id                : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    skill_title             : str 
    skill_description       : str
    skill_group_id          : str 
    skill_group_title       : str

class KNOWLEDGE(BaseModel):
    label                   : ClassVar[str] = "Knowledge"
    knowledge_id            : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    knowledge_title         : str 
    knowledge_description   : str
    knowledge_group_id      : str 
    knowledge_group_title   : str
    
    
    
class LEARNING_TASK(BaseModel):
    label                   : ClassVar[str] = "Learning_Task"
    task_id                 : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    task_title              : str
    task_type               : str
    module_id               : int
    max_points              : int
    task_description        : str
    main_library_id         : int



##########################################################################




class TASK_CLASS(BaseModel):
    label                   : ClassVar[str] = "Task_Class"
    task_class_id           : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    task_class              : str     
    

    
class SUPPORTIVE_INFORMATION(BaseModel):
    label                   : ClassVar[str] = "Supportive_Information"
    si_id                   : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    course_id               : int 
    si_title                : str
    
class PROCEDURAL_INFORMATION(BaseModel):
    label                   : ClassVar[str] = "Procedural_Information"
    pi_id                   : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    course_id               : int 
    pi_title                : str

class PART_TASK_PRACTICE(BaseModel):
    label                   : ClassVar[str] = "Part_Task_Practice"
    practice_id             : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    practice_title          : str     
    
class LEARNING_SESSION(BaseModel):
    label                   : ClassVar[str] = "Learning_Session"
    session_id              : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    start_time              : str
    end_time                : str
    student_id              : str
    
class STUDENT(BaseModel):
    label                   : ClassVar[str] = "Student"
    student_id              : str  = Field(..., json_schema_extra={"is_unique_neo4j": True})
    username                : str 
    firstname               : str 
    lastname                : str 
    email                   : str 
        
# -------------------------------------------------
# EDGES of the 4C/ID-SCHEMA
# -------------------------------------------------    

class REQUIRES_SKILL(BaseModel):
    label                   : ClassVar[str] = "REQUIRES_S"
    source_label            : ClassVar[str] = "Competence"
    target_label            : ClassVar[str] = "Skill"
    requires_s_id           : str
    skill_priority          : int
    competence_id           : str = Field(..., validation_alias="source_id")
    skill_id                : str = Field(..., validation_alias="target_id")
    
class REQUIRES_KNOWLEDGE(BaseModel):
    label                   : ClassVar[str] = "REQUIRES_K"
    source_label            : ClassVar[str] = "Competence"
    target_label            : ClassVar[str] = "Knowledge"
    requires_k_id           : str 
    knowledge_priority      : int
    competence_id           : str = Field(..., validation_alias="source_id")
    knowledge_id            : str = Field(..., validation_alias="target_id")   
    
class DEVELOPS_COMPETENCE(BaseModel):
    label                   : ClassVar[str] = "DEVELOPS"
    source_label            : ClassVar[str] = "Learning_Task"
    target_label            : ClassVar[str] = "Competence"
    develops_id             : str
    task_id                 : str = Field(..., validation_alias="source_id")
    competence_id           : str = Field(..., validation_alias="target_id") 
    
class PRACTICES_SKILL(BaseModel):
    label                   : ClassVar[str] = "PRACTICES"
    source_label            : ClassVar[str] = "Learning_Task"
    target_label            : ClassVar[str] = "Skill"
    practices_id            : str
    task_id                 : str = Field(..., validation_alias="source_id")
    skill_id                : str = Field(..., validation_alias="target_id")
    cognitive_process       : str
    
class APPLIES_KNOWLEDGE(BaseModel):
    label                   : ClassVar[str] = "APPLIES"
    source_label            : ClassVar[str] = "Learning_Task"
    target_label            : ClassVar[str] = "Knowledge"
    applies_id              : str
    task_id                 : str = Field(..., validation_alias="source_id")
    knowledge_id            : str = Field(..., validation_alias="target_id")
    knowledge_dimension     : str    
    
    
###############################################################################
    
    
    






    

    
class ATTEMPTED(BaseModel):
    label                   : ClassVar[str] = "ATTEMPTED"
    label_id                : ClassVar[str] = "attempted_id"
    source_label            : ClassVar[str] = "Student"
    source_id_field         : ClassVar[str] = "student_id"
    target_label            : ClassVar[str] = "Learning_Task"
    target_id_field         : ClassVar[str] = "task_id"
    attempted_id            : str
    timestamp               : str
    score                   : float
    passed                  : bool
    student_response        : str 
    correct_response        : str
    task_id                 : str
    student_id              : str
    
 
    
class GROUPS(BaseModel):
    label                   : ClassVar[str] = "GROUPS"
    label_id                : ClassVar[str] = "groups_id"
    source_label            : ClassVar[str] = "Task_Class"
    source_id_field         : ClassVar[str] = "task_class_id"
    target_label            : ClassVar[str] = "Learning_Task"
    target_id_field         : ClassVar[str] = "task_id"
    groups_id               : str
    task_class_id           : str
    task_id                 : str        
    
class PROVIDES(BaseModel):
    label                   : ClassVar[str] = "PROVIDES"
    label_id                : ClassVar[str] = "provides_id"
    source_label            : ClassVar[str] = "Task_Class"
    source_id_field         : ClassVar[str] = "task_class_id"
    target_label            : ClassVar[str] = "Supportive_Information"
    target_id_field         : ClassVar[str] = "si_id"
    provides_id             : str
    task_class_id           : str
    si_id                   : str        

class OFFERS(BaseModel):
    label                   : ClassVar[str] = "OFFERS"
    label_id                : ClassVar[str] = "offers_id"
    source_label            : ClassVar[str] = "Task_Class"
    source_id_field         : ClassVar[str] = "task_class_id"
    target_label            : ClassVar[str] = "Procedural_Information"
    target_id_field         : ClassVar[str] = "pi_id"
    offers_id               : str
    task_class_id           : str
    pi_id                   : str    

class INCLUDES(BaseModel):
    label                   : ClassVar[str] = "INCLUDES"
    label_id                : ClassVar[str] = "includes_id"
    source_label            : ClassVar[str] = "Task_Class"
    source_id_field         : ClassVar[str] = "task_class_id"
    target_label            : ClassVar[str] = "Part_Task_Practice"
    target_id_field         : ClassVar[str] = "practice_id"
    includes_id             : str
    task_class_id           : str
    practice_id             : str    

class TACKLED(BaseModel):
    label                   : ClassVar[str] = "TACKLED"
    label_id                : ClassVar[str] = "tackled_id"
    source_label            : ClassVar[str] = "Learning_Session"
    source_id_field         : ClassVar[str] = "session_id"
    target_label            : ClassVar[str] = "Learning_Task"
    target_id_field         : ClassVar[str] = "task_id"
    tackled_id              : str
    session_id              : str
    task_id                 : str     
    start_time              : str
    end_time                : str
    time_spent              : str
    
class REVIEWED(BaseModel):
    label                   : ClassVar[str] = "REVIEWED"
    label_id                : ClassVar[str] = "reviewed_id"
    source_label            : ClassVar[str] = "Learning_Session"
    source_id_field         : ClassVar[str] = "session_id"
    target_label            : ClassVar[str] = "Supportive_Information"
    target_id_field         : ClassVar[str] = "si_id"
    reviewed_id             : str
    session_id              : str
    si_id                   : str     
    start_time              : str
    end_time                : str
    time_spent              : str
    completion_time         : str
    
class CONSULTED(BaseModel):
    label                   : ClassVar[str] = "CONSULTED"
    label_id                : ClassVar[str] = "consulted_id"
    source_label            : ClassVar[str] = "Learning_Session"
    source_id_field         : ClassVar[str] = "session_id"
    target_label            : ClassVar[str] = "Procedural_Information"
    target_id_field         : ClassVar[str] = "pi_id"
    consulted_id            : str
    session_id              : str
    pi_id                   : str     
    start_time              : str
    end_time                : str
    time_spent              : str
    completion_time         : str
    
class STUDIED(BaseModel):
    label                   : ClassVar[str] = "STUDIED"
    label_id                : ClassVar[str] = "studied_id"
    source_label            : ClassVar[str] = "Student"
    source_id_field         : ClassVar[str] = "student_id"
    target_label            : ClassVar[str] = "Learning_Session"
    target_id_field         : ClassVar[str] = "session_id"
    studied_id              : str
    student_id              : str
    session_id              : str     
    start_time              : str
    end_time                : str
    duration                : str
    
class FINISHED(BaseModel):
    label                   : ClassVar[str] = "FINISHED"
    label_id                : ClassVar[str] = "finished_id"
    source_label            : ClassVar[str] = "Student"
    source_id_field         : ClassVar[str] = "student_id"
    target_label            : ClassVar[str] = "Learning_Task"
    target_id_field         : ClassVar[str] = "task_id"
    finished_id             : str
    student_id              : str
    task_id                 : str     
    completion_time         : str
    completion_type         : str
    score                   : str
 
class CUES(BaseModel):
    label                   : ClassVar[str] = "CUES"
    label_id                : ClassVar[str] = "cues_id"
    source_label            : ClassVar[str] = "Learning_Task"
    source_id_field         : ClassVar[str] = "task_id"
    target_label            : ClassVar[str] = "Procedural_Information"
    target_id_field         : ClassVar[str] = "pi_id"
    cues_id                 : str
    task_id                 : str
    pi_id                   : str
    
class REFERENCES(BaseModel):
    label                   : ClassVar[str] = "REFERENCES"
    label_id                : ClassVar[str] = "references_id"
    source_label            : ClassVar[str] = "Learning_Task"
    source_id_field         : ClassVar[str] = "task_id"
    target_label            : ClassVar[str] = "Supportive_Information"
    target_id_field         : ClassVar[str] = "si_id"
    references_id           : str
    task_id                 : str
    si_id                   : str
    
class TRAINS(BaseModel):
    label                   : ClassVar[str] = "TRAINS"
    label_id                : ClassVar[str] = "trains_id"
    source_label            : ClassVar[str] = "Part_Task_Practice"
    source_id_field         : ClassVar[str] = "practice_id"
    target_label            : ClassVar[str] = "Procedural_Information"
    target_id_field         : ClassVar[str] = "pi_id"
    trains_id               : str
    pi_id                   : str
    practice_id             : str
 
    