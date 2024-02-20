# Base image
FROM python:3.9-slim

RUN apt-get update && apt-get install -y wget gnupg2 initscripts unzip
# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \ 
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get -y install google-chrome-stable

# Install ChromeDriver
RUN wget -q "https://storage.googleapis.com/chrome-for-testing-public/121.0.6167.184/linux64/chromedriver-linux64.zip" \
    && unzip chromedriver-linux64.zip -d /usr/local/bin/ \
    && rm chromedriver-linux64.zip


# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

EXPOSE 8000

# Set environment variables
ENV MONGO_HOST=mongodb
ENV DISPLAY=:99

# Run the Python application
CMD ["uvicorn", "main:app","--host", "0.0.0.0", "--port", "8000", "--reload"]