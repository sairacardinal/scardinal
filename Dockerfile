# Select the python image as the base image
FROM python:3.12.9-slim-bookworm

# Set the working directory within the container
WORKDIR /app

# Copy all files into the working directory
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
RUN apt-get update \
  && apt-get install -y --no-install-recommends wkhtmltopdf \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Expose port 5000 for the Flask application
EXPOSE 5000

# Define the command to run the Flask application using Gunicorn
# CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000", "-w", "4"]