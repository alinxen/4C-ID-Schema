from pydantic import BaseModel, Field
from typing import ClassVar
from datetime import datetime


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

class STUDENT(BaseModel):
    label                   : ClassVar[str] = "Student"
    student_id              : str  = Field(..., json_schema_extra={"is_unique_neo4j": True})
    crud                    : str
    edulevels               : str
    total_events            : int
    first_active            : datetime

class LEARNING_SESSION(BaseModel):
    label                   : ClassVar[str] = "Learning_Session"
    session_id              : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    start_time              : datetime
    end_time                : datetime
    student_id              : str
    total_actions           : int
    
class TASK_CLASS(BaseModel):
    label                   : ClassVar[str] = "Task_Class"
    task_class_id           : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    task_class              : str  
    section_id              : int
    class_description       : str

class PART_TASK_PRACTICE(BaseModel):
    label                   : ClassVar[str] = "Part_Task_Practice"
    practice_id             : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    practice_title          : str  
    module_id               : int
    subtasks                : str
    question_text           : str 
    correct_answer          : str 
    max_points              : int
    
class PROCEDURAL_INFORMATION(BaseModel):
    label                   : ClassVar[str] = "Procedural_Information"
    pi_id                   : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    pi_title                : str    
    module_id               : int
    section_id              : int
    page_id                 : int
    content                 : str
    
    
class SUPPORTIVE_INFORMATION(BaseModel):
    label                   : ClassVar[str] = "Supportive_Information"
    si_id                   : str = Field(..., json_schema_extra={"is_unique_neo4j": True})
    si_title                : str  
    module_id               : int
    section_id              : int
    page_id                 : int
    content                 : str    
        
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
    
class GROUPS(BaseModel):
    label                   : ClassVar[str] = "GROUPS"
    source_label            : ClassVar[str] = "Task_Class"
    target_label            : ClassVar[str] = "Learning_Task"
    groups_id               : str
    task_sequence           : str
    task_class_id           : str = Field(..., validation_alias="source_id")
    task_id                 : str = Field(..., validation_alias="target_id")  

class INCLUDES(BaseModel):
    label                   : ClassVar[str] = "INCLUDES"
    source_label            : ClassVar[str] = "Task_Class"
    target_label            : ClassVar[str] = "Part_Task_Practice"
    includes_id             : str
    task_class_id           : str = Field(..., validation_alias="source_id")
    practice_id             : str = Field(..., validation_alias="target_id") 

class PROVIDES(BaseModel):
    label                   : ClassVar[str] = "PROVIDES"
    source_label            : ClassVar[str] = "Task_Class"
    target_label            : ClassVar[str] = "Supportive_Information"
    provides_id             : str
    task_class_id           : str = Field(..., validation_alias="source_id")
    si_id                   : str = Field(..., validation_alias="target_id")       

class OFFERS(BaseModel):
    label                   : ClassVar[str] = "OFFERS"
    source_label            : ClassVar[str] = "Task_Class"
    target_label            : ClassVar[str] = "Procedural_Information"
    offers_id               : str
    task_class_id           : str = Field(..., validation_alias="source_id")
    pi_id                   : str = Field(..., validation_alias="target_id")    
    
class TRAINS(BaseModel):
    label                   : ClassVar[str] = "TRAINS"
    source_label            : ClassVar[str] = "Part_Task_Practice"
    target_label            : ClassVar[str] = "Procedural_Information"
    trains_id               : str
    pi_id                   : str  = Field(..., validation_alias="target_id") 
    practice_id             : str  = Field(..., validation_alias="source_id")
    
class CUES(BaseModel):
    label                   : ClassVar[str] = "CUES"
    source_label            : ClassVar[str] = "Learning_Task"
    target_label            : ClassVar[str] = "Procedural_Information"
    cues_id                 : str
    task_id                 : str = Field(..., validation_alias="source_id")
    pi_id                   : str = Field(..., validation_alias="target_id")  
    
class REFERENCES(BaseModel):
    label                   : ClassVar[str] = "REFERENCES"
    source_label            : ClassVar[str] = "Learning_Task"
    target_label            : ClassVar[str] = "Supportive_Information"
    references_id           : str
    task_id                 : str = Field(..., validation_alias="source_id")
    si_id                   : str = Field(..., validation_alias="target_id")  
    
    
class FINISHED(BaseModel):
    label                   : ClassVar[str] = "FINISHED"
    source_label            : ClassVar[str] = "Student"
    target_label            : ClassVar[str] = "Learning_Task"
    finished_id             : str
    student_id              : str = Field(..., validation_alias="source_id")
    task_id                 : str = Field(..., validation_alias="target_id")       
    completion_time         : str
    completion_type         : str
    score                   : float
  
    
class ATTEMPTED(BaseModel):
    label                   : ClassVar[str] = "ATTEMPTED"
    source_label            : ClassVar[str] = "Student"
    target_label            : ClassVar[str] = "Learning_Task"
    attempted_id            : str
    timestamp               : str
    score                   : float
    passed                  : bool
    student_response        : str 
    correct_response        : str
    task_id                 : str = Field(..., validation_alias="target_id")
    student_id              : str = Field(..., validation_alias="source_id")
    
    
class COMPLETED(BaseModel):
    label                   : ClassVar[str] = "COMPLETED"
    source_label            : ClassVar[str] = "Student"
    target_label            : ClassVar[str] = "Part_Task_Practice"
    completed_id            : str
    student_id              : str = Field(..., validation_alias="source_id")
    practice_id             : str = Field(..., validation_alias="target_id")       
    completion_time         : str
    completion_type         : str
    score                   : float    
   
    
 ##########################################################################   

class STUDIED(BaseModel):
    label                   : ClassVar[str] = "STUDIED"
    source_label            : ClassVar[str] = "Student"
    target_label            : ClassVar[str] = "Learning_Session"
    studied_id              : str
    student_id              : str = Field(..., validation_alias="source_id")
    session_id              : str = Field(..., validation_alias="target_id")    
    start_time              : datetime
    end_time                : datetime
    duration                : float
    
    
class CONSULTED(BaseModel):
    label                   : ClassVar[str] = "CONSULTED"
    source_label            : ClassVar[str] = "Learning_Session"
    target_label            : ClassVar[str] = "Procedural_Information"
    consulted_id            : str
    session_id              : str = Field(..., validation_alias="source_id")
    pi_id                   : str = Field(..., validation_alias="target_id")
    start_time              : str
    end_time                : str
    time_spent              : str
    completion_time         : str
    
    
class TACKLED(BaseModel):
    label                   : ClassVar[str] = "TACKLED"
    source_label            : ClassVar[str] = "Learning_Session"
    target_label            : ClassVar[str] = "Learning_Task"
    tackled_id              : str
    session_id              : str = Field(..., validation_alias="source_id")
    task_id                 : str = Field(..., validation_alias="target_id")     
    start_time              : str
    end_time                : str
    time_spent              : str
    
    
class REVIEWED(BaseModel):
    label                   : ClassVar[str] = "REVIEWED"
    source_label            : ClassVar[str] = "Learning_Session"
    target_label            : ClassVar[str] = "Supportive_Information"
    reviewed_id             : str
    session_id              : str = Field(..., validation_alias="source_id")
    si_id                   : str = Field(..., validation_alias="target_id")     
    start_time              : str
    end_time                : str
    time_spent              : str
    completion_time         : str
    

    

    

 

    

    

 
    