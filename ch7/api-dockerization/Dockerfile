# Use an official lightweight Python runtime as a base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the application code into the container
COPY . .

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    libffi-dev libssl-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port on which the FastAPI app will run
EXPOSE 8000

# Command to run the FastAPI app with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
