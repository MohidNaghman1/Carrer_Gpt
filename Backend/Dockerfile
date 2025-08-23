# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed system dependencies and the Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
# The 'src' folder, alembic, faiss_index etc.
COPY . .

# Tell Docker what command to run when the container starts
# This command runs your Alembic migrations and then starts the Uvicorn server
CMD ["sh", "-c", "python -m alembic upgrade head && export PYTHONPATH=/app && uvicorn main:app --host 0.0.0.0 --port $PORT"]
