# Use Python 3.12.1 base image
FROM python:3.12.1-slim

# Disable Python output buffering for real-time logs
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /service-A

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY service-A-app.py .

# Run the app
CMD ["python", "service-A-app.py"]
