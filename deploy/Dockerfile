

FROM python:3.11-slim

# Install OS dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV AGENT_NAME=""

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app

# Expose port for FastAPI
EXPOSE 8080

# Startup command
CMD ["uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8080"]

