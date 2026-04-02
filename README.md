
```text
.
├── Dockerfile - Python pipeline container instructions
├── README.md
├── data - Local CSVs files with simulated Moodle data
│   ├── competencies_knowledge_skills.csv
│   ├── course_structure.csv
│   ├── m_course_modules.csv
│   ├── m_course_modules_completion.csv
│   ├── m_grade_grades.csv
│   ├── m_grade_grades_history.csv
│   ├── m_hvp.csv
│   ├── m_hvp_libraries.csv
│   ├── m_hvp_xapi_results.csv
│   ├── m_logstore_standard_log.csv
│   ├── m_page.csv
│   └── m_user.csv
├── docker-compose.yml - Container orchestration blueprint
├── docker_data - Persistent database volume (auto-generated)
│   ├── data
│   │   ├── databases
│   │   │   ├── neo4j
│   │   │   │   ├── database_lock
│   │   │   │   ├── id-buffer.tmp.0
│   │   │   │   ├── neostore
│   │   │   │   ├── neostore.counts.db
│   │   │   │   ├── neostore.indexstats.db
│   │   │   │   ├── neostore.labeltokenstore.db
│   │   │   │   ├── neostore.labeltokenstore.db.id
│   │   │   │   ├── neostore.labeltokenstore.db.names
│   │   │   │   ├── neostore.labeltokenstore.db.names.id
│   │   │   │   ├── neostore.nodestore.db
│   │   │   │   ├── neostore.nodestore.db.id
│   │   │   │   ├── neostore.nodestore.db.labels
│   │   │   │   ├── neostore.nodestore.db.labels.id
│   │   │   │   ├── neostore.propertystore.db
│   │   │   │   ├── neostore.propertystore.db.arrays
│   │   │   │   ├── neostore.propertystore.db.arrays.id
│   │   │   │   ├── neostore.propertystore.db.id
│   │   │   │   ├── neostore.propertystore.db.index
│   │   │   │   ├── neostore.propertystore.db.index.id
│   │   │   │   ├── neostore.propertystore.db.index.keys
│   │   │   │   ├── neostore.propertystore.db.index.keys.id
│   │   │   │   ├── neostore.propertystore.db.strings
│   │   │   │   ├── neostore.propertystore.db.strings.id
│   │   │   │   ├── neostore.relationshipgroupstore.db
│   │   │   │   ├── neostore.relationshipgroupstore.db.id
│   │   │   │   ├── neostore.relationshipgroupstore.degrees.db
│   │   │   │   ├── neostore.relationshipstore.db
│   │   │   │   ├── neostore.relationshipstore.db.id
│   │   │   │   ├── neostore.relationshiptypestore.db
│   │   │   │   ├── neostore.relationshiptypestore.db.id
│   │   │   │   ├── neostore.relationshiptypestore.db.names
│   │   │   │   ├── neostore.relationshiptypestore.db.names.id
│   │   │   │   ├── neostore.schemastore.db
│   │   │   │   ├── neostore.schemastore.db.id
│   │   │   │   └── schema
│   │   │   │       └── index
│   │   │   │           └── token-lookup-1.0
│   │   │   │               ├── 1
│   │   │   │               │   └── index-1
│   │   │   │               └── 2
│   │   │   │                   └── index-2
│   │   │   ├── store_lock
│   │   │   └── system
│   │   │       ├── database_lock
│   │   │       ├── id-buffer.tmp.0
│   │   │       ├── neostore
│   │   │       ├── neostore.counts.db
│   │   │       ├── neostore.indexstats.db
│   │   │       ├── neostore.labeltokenstore.db
│   │   │       ├── neostore.labeltokenstore.db.id
│   │   │       ├── neostore.labeltokenstore.db.names
│   │   │       ├── neostore.labeltokenstore.db.names.id
│   │   │       ├── neostore.nodestore.db
│   │   │       ├── neostore.nodestore.db.id
│   │   │       ├── neostore.nodestore.db.labels
│   │   │       ├── neostore.nodestore.db.labels.id
│   │   │       ├── neostore.propertystore.db
│   │   │       ├── neostore.propertystore.db.arrays
│   │   │       ├── neostore.propertystore.db.arrays.id
│   │   │       ├── neostore.propertystore.db.id
│   │   │       ├── neostore.propertystore.db.index
│   │   │       ├── neostore.propertystore.db.index.id
│   │   │       ├── neostore.propertystore.db.index.keys
│   │   │       ├── neostore.propertystore.db.index.keys.id
│   │   │       ├── neostore.propertystore.db.strings
│   │   │       ├── neostore.propertystore.db.strings.id
│   │   │       ├── neostore.relationshipgroupstore.db
│   │   │       ├── neostore.relationshipgroupstore.db.id
│   │   │       ├── neostore.relationshipgroupstore.degrees.db
│   │   │       ├── neostore.relationshipstore.db
│   │   │       ├── neostore.relationshipstore.db.id
│   │   │       ├── neostore.relationshiptypestore.db
│   │   │       ├── neostore.relationshiptypestore.db.id
│   │   │       ├── neostore.relationshiptypestore.db.names
│   │   │       ├── neostore.relationshiptypestore.db.names.id
│   │   │       ├── neostore.schemastore.db
│   │   │       ├── neostore.schemastore.db.id
│   │   │       └── schema
│   │   │           └── index
│   │   │               ├── range-1.0
│   │   │               │   ├── 11
│   │   │               │   │   └── index-11
│   │   │               │   ├── 13
│   │   │               │   │   └── index-13
│   │   │               │   ├── 3
│   │   │               │   │   └── index-3
│   │   │               │   ├── 5
│   │   │               │   │   └── index-5
│   │   │               │   ├── 7
│   │   │               │   │   └── index-7
│   │   │               │   └── 9
│   │   │               │       └── index-9
│   │   │               └── token-lookup-1.0
│   │   │                   ├── 1
│   │   │                   │   └── index-1
│   │   │                   └── 2
│   │   │                       └── index-2
│   │   ├── dbms
│   │   │   └── auth.ini
│   │   ├── server_id
│   │   └── transactions
│   │       ├── neo4j
│   │       │   ├── checkpoint.0
│   │       │   └── neostore.transaction.db.0
│   │       └── system
│   │           ├── checkpoint.0
│   │           └── neostore.transaction.db.0
│   └── logs
│       ├── debug.log
│       ├── http.log
│       ├── neo4j.log
│       ├── query.log
│       └── security.log
├── neo4j_pipeline.py - The main execution script
├── requirements.txt - Python dependencies
└── src
    ├── __pycache__
    │   ├── config.cpython-311.pyc
    │   ├── database.cpython-311.pyc
    │   └── schema.cpython-311.pyc
    ├── config.py - Credentials, URIs, and Filepaths
    ├── database.py - Neo4j Driver communication
    ├── loaders - Functions that execute Cypher queries
    │   ├── __pycache__
    │   │   ├── edge_loader.cpython-311.pyc
    │   │   └── node_loader.cpython-311.pyc
    │   ├── edge_loader.py - Load edges into Neo4j
    │   └── node_loader.py - Load nodes into Neo4j
    ├── schema.py - Constraints and Pydantic models
    └── transformers - Extract data from CSVs and validate using Pydantic models
        ├── __init__.py
        ├── __pycache__
        │   ├── __init__.cpython-311.pyc
        │   ├── activity_transformer.cpython-311.pyc
        │   ├── competence_transformer.cpython-311.pyc
        │   ├── instructional_transformer.cpython-311.pyc
        │   ├── learning_transformer.cpython-311.pyc
        │   ├── structure_transformer.cpython-311.pyc
        │   ├── student_transformer.cpython-311.pyc
        │   └── teaching_teansformer.cpython-311.pyc
        ├── activity_transformer.py
        ├── competence_transformer.py
        ├── instructional_transformer.py
        ├── learning_transformer.py
        ├── structure_transformer.py
        ├── student_transformer.py
        └── teaching_teansformer.py
```
# Neo4j 4C/ID Schema Pipeline

This project provides an automated data pipeline to import simulated Moodle data into a Neo4j knowledge graph using the 4C/ID instructional design model. 

The system relies on two Docker containers:
1. **`graph-db`**: A Neo4j database.
2. **`neo4j-pipeline`**: A Python container that extracts CSV data, validates it using Pydantic schemas, and loads the nodes and edges into the database.

---

## Project Structure

## Folder Structure
This section will be auto-populated.


```text
main/
├── data/                                   # Local CSVs files with simulated Moodle data
├── docker_data/                            # Persistent database volume (auto-generated)
├── src/
│   ├── config.py                           # Credentials, URIs, and Filepaths
│   ├── database.py                         # Neo4j Driver communication
│   ├── transformers/                       # Extract data from CSVs and validate using Pydantic models
│   │   ├── activity_transformer.py
│   │   ├── competence_transformers.py        # Skill, Knowledge, Competence
│   │   ├── instructional_transformers.py     # Learning Tasks, Procedural/Supportive Info, Part-Task Practice
│   │   ├── learning_transformer.py
│   │   ├── structure_transformer.py
│   │   ├── student_transformers.py           # Student, Learning Sessions
│   │   └── teaching_transformer.py
│   ├── loaders/                            # Functions that execute Cypher queries
│   │   ├── node_loader.py                    # Load nodes into Neo4j
│   │   └── edge_loader.py                    # Load edges into Neo4j
│   └── schema.py                           # Constraints and Pydantic models                    
├── requirements.txt                        # Python dependencies
├── .env                                    # Environment variables (Create this yourself!)
├── docker-compose.yml                      # Container orchestration blueprint
├── Dockerfile                              # Python pipeline container instructions
├── README.md                               
└── neo4j_pipeline.py                       # The main execution script
```

---

## Initial Setup

Before running the project, you must define your database password. 

In the root folder of this project (next to this README), create a new text file named exactly `.env` and add the following line:

```text
NEO4J_PASSWORD=your_secure_password_here
```
*(Note: Do not use spaces around the equals sign.)*

---

## How to Run This Project

You can run this project in two different ways depending on your workflow.

### Option 1: The Quick Way (Using Docker)
*Best for anyone who wants a fully automated setup.*

If you have [Docker Desktop](https://www.docker.com/products/docker-desktop) installed, you do not need to install Python or set up a local database.

1. Open a terminal in this folder.
2. Run the following command to build the pipeline and start the database:
   ```bash
   docker compose up --build
   ```
3. Docker will automatically start Neo4j, wait for it to be fully loaded (healthcheck), and then execute the Python pipeline to import the Moodle data.
4. Once the pipeline finishes, open **http://localhost:7474** in your web browser.
5. Log in using the username **`neo4j`** and the password you defined in your `.env` file.

### Option 2: The Manual Way (Local Python Development)
*Best for anyone who wants to add their own data or modify the schema.*

If you prefer to run the Python code locally using your own virtual environment:

1. Start **only** the database container in the background:
   ```bash
   docker compose up -d graph-db
   ```
2. Wait about 15-20 seconds for Neo4j to fully boot up. You can verify it is ready by visiting `http://localhost:7474`.
3. In your local Python environment, install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Open the project in your preferred IDE and run the `neo4j_pipeline.py` script locally.

---

## Common Troubleshooting

**Issue: `Connection Refused` or `Cannot resolve address graph-db:7687`**
* **Cause:** The Python script ran before the database finished booting up. Neo4j takes about 15–30 seconds to start.
* **Fix:** Wait a few seconds and run `docker compose run --rm neo4j-pipeline` to execute the script again. (If using `docker compose up`, the built-in healthcheck should prevent this automatically).

