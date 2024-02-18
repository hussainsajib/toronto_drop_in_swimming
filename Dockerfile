# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

EXPOSE 8000

# Set environment variables
ENV MONGO_HOST=mongodb

# Run the Python application
CMD ["uvicorn", "main:app","--host", "0.0.0.0", "--port", "8000", "--reload"]