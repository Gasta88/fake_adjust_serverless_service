FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the dedicated directory contents into the container at /app
COPY executor_func /app/executor_func
COPY orchestrator_func /app/orchestrator_func
COPY requirements.txt /app/requirements.txt


# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run unit-tests
CMD ["python", "-m", "unittest", "discover"]
