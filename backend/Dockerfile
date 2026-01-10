FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OCR and database drivers
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy English model (for NLP)
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create directory for temporary files
RUN mkdir -p /app/temp

# Expose port
EXPOSE 8000

# Default command (overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
