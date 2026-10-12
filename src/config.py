import os

EXCLUDED_USER_IDS =["-1", "u43a4c7d2345b9c4be712", "u6f1e349c2816259b7e8d"]

DATA_DIR                = os.path.join(os.path.dirname(__file__), "..", "data")
COMPETENCE_CSV_PATH     = os.path.join(DATA_DIR,  "c_competence.csv")
SKILLS_CSV_PATH         = os.path.join(DATA_DIR,  "c_skills.csv")
KNOWLEDGE_CSV_PATH      = os.path.join(DATA_DIR,  "c_knowledge.csv")
HVP_CSV_PATH            = os.path.join(DATA_DIR,  "m_hvp.csv")
LOGFILE_CSV_PATH        = os.path.join(DATA_DIR,  "m_logstore_standard_log.csv")
TASK_CSV_PATH           = os.path.join(DATA_DIR,  "a_lernaufgaben.csv")
CLASSES_CSV_PATH        = os.path.join(DATA_DIR,  "a_task_class.csv")
PTP_CSV_PATH            = os.path.join(DATA_DIR,  "a_part_task_practice.csv")
INFORMATION_CSV_PATH    = os.path.join(DATA_DIR,  "a_lehrmaterial.csv")
FRAMEWORK_CSV_PATH      = os.path.join(DATA_DIR,  "c_competence_framework.csv")
TARGET_CSV_PATH         = os.path.join(DATA_DIR,  "a_lernziele.csv")
GRADE_GRADES_CSV_PATH   = os.path.join(DATA_DIR,  "m_grade_grades.csv")



COMPLETED_CSV_PATH      = os.path.join(DATA_DIR,  "m_course_modules_completion.csv")





COURSE_MODULE_CSV_PATH  = os.path.join(DATA_DIR,  "m_course_modules.csv")
COURSE_CSV_PATH         = os.path.join(DATA_DIR,  "course_structure.csv")
XAPI_CSV_PATH           = os.path.join(DATA_DIR,  "m_hvp_xapi_results.csv")
PAGES_CSV_PATH          = os.path.join(DATA_DIR,  "m_page.csv")





ANALYTICS_DIR           = os.path.join(os.path.dirname(__file__), "analytics")
CQ_PATH                 = os.path.join(ANALYTICS_DIR, "competence_questions.csv")
QUERIES_PATH            = os.path.join(ANALYTICS_DIR, "cypher_queries.yaml")


