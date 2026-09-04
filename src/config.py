import os

DATA_DIR                = os.path.join(os.path.dirname(__file__), "..", "data")
COMPETENCE_CSV_PATH     = os.path.join(DATA_DIR,  "c_competence.csv")
SKILLS_CSV_PATH         = os.path.join(DATA_DIR,  "c_skills.csv")
KNOWLEDGE_CSV_PATH      = os.path.join(DATA_DIR,  "c_knowledge.csv")
FRAMEWORK_CSV_PATH      = os.path.join(DATA_DIR,  "c_competence_framework.csv")
HVP_CSV_PATH            = os.path.join(DATA_DIR,  "m_hvp.csv")
TASK_CSV_PATH           = os.path.join(DATA_DIR,  "a_lernaufgaben.csv")
TARGET_CSV_PATH         = os.path.join(DATA_DIR,  "a_lernziele.csv")

PAGES_CSV_PATH          = os.path.join(DATA_DIR, "m_page.csv")
LOGFILE_CSV_PATH        = os.path.join(DATA_DIR,  "m_logstore_standard_log.csv")
XAPI_CSV_PATH           = os.path.join(DATA_DIR,  "m_hvp_xapi_results.csv")
COURSE_CSV_PATH         = os.path.join(DATA_DIR,  "course_structure.csv")
COMPLETED_CSV_PATH      = os.path.join(DATA_DIR,  "m_course_modules_completion.csv")
COURSE_MODULE_CSV_PATH  = os.path.join(DATA_DIR,  "m_course_modules.csv")
GRADE_GRADES_CSV_PATH   = os.path.join(DATA_DIR,  "m_grade_grades.csv")

ANALYTICS_DIR           = os.path.join(os.path.dirname(__file__), "analytics")
CQ_PATH                 = os.path.join(ANALYTICS_DIR, "competence_questions.csv")
QUERIES_PATH            = os.path.join(ANALYTICS_DIR, "cypher_queries.yaml")


