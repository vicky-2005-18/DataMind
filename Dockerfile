FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.lock.txt .
COPY requirements-dev.lock.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.lock.txt
RUN pip install --no-cache-dir -r requirements-dev.lock.txt

# Copy application code
COPY . .

# Install package in editable mode
RUN pip install -e .

# Create storage directory
RUN mkdir -p storage logs

# Expose Streamlit port
EXPOSE 8501

# Run the application
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
