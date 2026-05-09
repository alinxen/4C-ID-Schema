
# Neo4j 4C/ID Schema Pipeline

This project provides an automated data pipeline to import simulated Moodle data into a Neo4j knowledge graph using the 4C/ID instructional design model. 

The system relies on two Docker containers:
1. **`graph-db`**: A Neo4j database.
2. **`neo4j-pipeline`**: A Python container that extracts CSV data, validates it using Pydantic schemas, and loads the nodes and edges into the database.

---

## Project Structure

```
main/
├── data/                            # Local CSV files containing simulated Moodle data
├── docker_data/                     # Volume for the Neo4j database
├── src/
│   ├── analytics/
│   │   ├── competence_questions.csv # CQs used for evaluating the schema
│   │   └── cypher_queries.py        # Cypher queries matching CQs
│   ├── extractors/
│   │   └── data_extractor.py        # Handles extraction of raw data from CSV files
│   ├── loaders/
│   │   ├── edge_loader.py           # Loads transformed DataFrames as edges into Neo4j
│   │   ├── node_loader.py           # Loads transformed DataFrames as nodes into Neo4j 
│   │   └── graph_loader.py          # Master class combining edge and node loaders
│   ├── transformers/              
│   │   ├── edge_transformers_1.py   # Base class and transformations for graph edges
│   │   ├── edge_transformers_2.py   # Handles FINISHED and ATTEMPTED edges
│   │   ├── edge_transformers_3.py   # Handles STUDIED, TACKLED, REVIEWED, and CONSULTED edges
│   │   └── node_transformers.py     # Base class and transformations for graph nodes
│   ├── validators/                
│   │   └── pydantic_validator.py    # Validates data against Pydantic schema
│   ├── config.py                    # Filepaths and Stuff
│   ├── database.py                  # Manages Neo4j/Python connection
│   └── schema.py                    # Defines Pydantic data models and Neo4j constraints
├── docker-compose.yml               # Orchestrating the Docker containers
├── Dockerfile                       # Instructions for building the Python ETVL pipeline container
├── neo4j_analytics.py               # Evaluates the Neo4j graph using the CQs
├── neo4j_pipeline.py                # EVTL pipeline to process and load nodes/edges into Neo4j
├── README.md                        # Project documentation and setup instructions
├── requirements.txt                 # List of required Python dependencies
└── .env                             # Local environment variables (needs zo be created manually)
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

