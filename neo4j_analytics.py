import pandas as pd
import nbformat as nbf

#from src.analytics.cypher_queries import QUERIES




def build_jupyter_notebook(competence_questions):#, queries):
    
    nb = nbf.v4.new_notebook()
    cells = []
    
    for index, row in competence_questions.iterrows():
        
        cq_id    = row['Question_ID']
        question = row['Question']

        #query = queries.get(cq_id, "// Query not written yet")

        cells.append(nbf.v4.new_markdown_cell(f"{cq_id}: {question}"))
#         code = f"""
# query = \"\"\"
# {query_string}
# \"\"\"
# # Run query with parameters here
# """
#     cells.append(nbf.v4.new_code_cell(code))
    
    
    nb['cells'] = cells
    with open('Schema_Evaluation.ipynb', 'w') as f:
        nbf.write(nb, f)



def main():
    # Load Competence Questions
    competence_questions = pd.read_csv("/home/andrea/Documents/Docker/4cid-schema/src/analytics/competence_questions.csv", sep = ";")

    # Load Queries
    
    # Create Jupyter-Notebook
    build_jupyter_notebook(competence_questions)
    
#     # 1. Initialize neomodel before querying
#     manager = NeomodelManager()
#     manager.connect_neomodel()
#     cool_things_that_neomodel_can_do()


# # Create helper function such as get all nodes of type or get all skills of type


if __name__=="__main__":
    main()
    
    
    
    
    
    
# The functions are divided into four main categories based on their primary purpose: formatting helpers, name/ID mapping, string aggregators (which build and return complex text), and standard output functions (which build and `print()` text to the console).

# ### 1. Grammar and Formatting Snippets
# These helper functions return specific text strings (often handling German grammar rules, pluralization, or time formatting) to be inserted into larger text blocks:
# * `h_grammar_correction_task(number)`
# * `h_grammar_correction_attempt(number)`
# * `h_grammar_correction_student_nom(number)`
# * `h_grammar_correction_student_dat(number)`
# * `h_grammar_correction_haben(is_singular)`
# * `h_grammar_correction_wurden(is_singular)`
# * `h_grammar_correction_waren(is_singular)`
# * `h_normalize_duration(duration_record)`
# * `h_change_minutes_to_hours(minutes_to_convert)`
# * `h_change_taxonomy_level_for_print(relation_name)`
# * `h_change_knowledge_dimension_for_print(relation_name)`

# ### 2. Name and ID Translators
# These helper functions look up dictionaries and return strings (names or IDs). They also print text error messages to the console if a match isn't found:
# * `h_get_skill_name_for_id(skill_id)`
# * `h_get_skill_id_for_name(skill_name)`
# * `h_get_knowledge_name_for_id(knowledge_id)`
# * `h_get_knowledge_id_for_name(knowledge_name)`
# * `h_get_competence_name_for_id(competence_id)`
# * `h_get_competence_id_for_name(competence_name)`

# ### 3. Text Aggregators (Returning Complex Strings)
# These functions query the Neo4j database, evaluate the logic, and dynamically construct a comprehensive report string (often stored in a variable like `text_to_print`) which is returned by the function:
# * `h_get_wrong_answers_for_task(task_name)`
# * `h_get_competences_taught_in_task(task_name)`
# * `h_get_skills_taught_in_task(task_name)`
# * `h_get_knowledge_taught_in_task(task_name)`
# * `get_practice_of_competence_knowledge_skill()`
# * `h_get_information_on_competence(competence_id)`
# * `h_get_information_on_knowledge(knowledge_id)`
# * `h_get_information_on_skill(skill_id)`

# *(Note: `h_get_students_last_response_for_task` technically returns a string as well, though it retrieves a student's text response directly from the database rather than generating it).*

# ### 4. Output / Print Functions
# These functions assemble large, dynamic blocks of text internally and output them directly to the console via `print()`. 
# * `print_general_information_on_student(last_name)`
# * `print_content_of_learning_sessions(last_name)`
# * `print_learning_order_of_student_everything(last_name)`
# * `print_information_on_difficult_tasks_for_student(last_name)`
# * `print_information_on_students_performance_with_task(last_name, task_name)`
# * `print_last_practice_of_skill(last_name, skill_name)`
# * `print_last_practice_of_knowledge(last_name, knowledge_name)`
# * `print_last_practice_of_competence(last_name, competence_name)`
# * `print_general_information_on_competence_from_id(competence_id)`
# * `print_general_information_on_competence_from_name(competence_name)`
# * `print_difficulties_with_competences()`
# * `print_general_information_on_knowledge_from_id(knowledge_id)`
# * `print_general_information_on_knowledge_from_name(knowledge_name)`
# * `print_difficulties_with_knowledge_items()`
# * `print_general_information_on_skill_from_id(skill_id)`
# * `print_general_information_on_skill_from_name(skill_name)`
# * `print_difficulties_with_skills()`
# * `print_general_information_on_task(task_name)`
# * `print_general_information_on_information_material(im_name)`
# * `print_information_on_difficult_tasks()`
# * `print_information_on_success_in_course()`
# * `print_information_on_time_spent_in_course()`
# * `print_general_information_on_course()`
# * `print_information_on_similar_learning_profiles()`
# * `print_information_on_related_material()`
