FROM python:3.11-slim

# Set workdir
WORKDIR /src

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

# Set environment variable
ENV PYTHONUNBUFFERED=1

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]