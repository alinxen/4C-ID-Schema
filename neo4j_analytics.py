import yaml
import pandas as pd
import nbformat as nbf

from src.config import CQ_PATH, QUERIES_PATH



def build_jupyter_notebook(questions, queries):
    """
    Creates a notebook with formatted questions and code blocks.
    """
    nb = nbf.v4.new_notebook()

    # ==========================================
    # 1. INTRODUCTION & INSTRUCTIONS CELL (MARKDOWN)
    # ==========================================
    intro_markdown = """
# 4C/ID Schema: Evaluating Competence Questions 
Welcome to the interactive analytics notebook. This environment allows you to test the Competence Questions (CQs) against the simulated Neo4j graph database. 
The Competence Questions cover four areas: (1) general course analytics, (2) individual student tracking, (3)
4C/ID component analysis, and (4) competence acquisition.

### How to use this notebook:
1. **Run the Setup Cell** directly below this text to connect to the database.
2. Scroll down to evaluate each Competence Question.
3. Click on a code cell and press `Shift + Enter` to execute the Cypher query.
    """
    nb.cells.append(nbf.v4.new_markdown_cell(intro_markdown))
    
    # ==========================================
    # SETUP CELL (PYTHON)
    # ==========================================
    setup_code = """import pandas as pd
#from IPython.display import display, HTML
from src.database import GraphDB

# --- Connect to Neo4jGraph ---
db = GraphDB()

# --- Helper Function for Queries ---
def execute_query(query, params=None):
    
    result, summary, keys = db.driver.execute_query(query,params)
    print(f"Query executed in {summary.result_available_after} ms\\n")
    return pd.DataFrame([r.data() for r in result])
"""
    nb.cells.append(nbf.v4.new_code_cell(setup_code))
    
    # ==========================================
    # 3. DYNAMIC CQ GENERATION
    # ==========================================

    for index, row in questions.iterrows():
        cq_id    = row['Question_ID']  
        question = row['Question'] 
        
        # Look up the query by ID in queries DataFrame
        match = queries[queries['id'] == cq_id]
        
        # 1. Initialize notes as None so it's always defined
        notes = None 
        
        if not match.empty:
            # Get the 'query' value from the first matching row
            cypher_code = match.iloc[0]['query']
            notes       = match.iloc[0]['note']
            parameters  = match.iloc[0]['parameters']
            if pd.notna(parameters) and str(notes).strip() != "":
                code_text = f"""query = \"\"\"
{cypher_code}\"\"\"

parameters = {parameters}
    
execute_query(query, parameters)
            """
        
            else: code_text = f"""query = \"\"\"
{cypher_code}\"\"\"
            
execute_query(query)
        """
        else:
            code_text = ""
        
        
            
        
    
        # --- Beautiful Markdown Formatting for each CQ ---
        # 2. Build the base markdown first
        cq_markdown = f"""---
### CQ {cq_id}
    
**Question:** {question}"""
    
        # 3. Conditionally add the notes block if it exists and isn't empty/NaN
        if pd.notna(notes) and str(notes).strip() != "":
            cq_markdown += f"""
    
> **Note:**
> *{notes}*"""
    
        nb.cells.append(nbf.v4.new_markdown_cell(cq_markdown))
        nb.cells.append(nbf.v4.new_code_cell(code_text))
        
    # ==========================================
    # 4. SAVE NOTEBOOK
    # ==========================================
    filename = "Schema_Evaluation.ipynb"
    with open(filename, 'w') as f:
        nbf.write(nb, f)
    
    print(f"{filename} successfully generated.")
    
    





def main():
    print("\nStarting Notebook Generator.\n" + "=" * 40)
       
    # 1. Load Competence Questions
    competence_questions = pd.read_csv(CQ_PATH, sep=";", dtype={'Question_ID': str})
    print(f"Successfully loaded {len(competence_questions)} Competence Questions.")
    
    # 2. Load YAML Queries
    with open(QUERIES_PATH, "r") as file:
        queries_data = yaml.safe_load(file)
    cypher_queries = pd.DataFrame(queries_data['queries'])
    print(f"Successfully loaded {len(cypher_queries)} Cypher Queries.")
    
    # 3. Build and save the notebook
    build_jupyter_notebook(competence_questions, cypher_queries)

    print("=" * 40 + "\nNotebook Generator finished.\n")


if __name__ == "__main__":
    main()