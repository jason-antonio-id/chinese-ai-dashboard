# Use official Python image
FROM python:3.10-slim

# Install system dependencies (Tesseract + Chinese language)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (Hugging Face expects 7860)
EXPOSE 7860

# Set Tesseract path
ENV TESSERACT_CMD=/usr/bin/tesseract

# Run with gunicorn (production server)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--timeout", "120"]
