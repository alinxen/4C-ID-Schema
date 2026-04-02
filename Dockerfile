# Start with a lightweight version of Python
FROM python:3.11-slim

# Tell Docker to do all following work inside a folder called /app
WORKDIR /app

# Install the ultra-fast 'uv' package manager
RUN pip install uv

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy the CSV data into the container
COPY ./data ./data

# Copy your modules into the container
COPY ./src ./src

# Copy the main pipeline script
COPY neo4j_pipeline.py .

# Run the pipeline when the container starts
CMD ["python", "neo4j_pipeline.py"]
