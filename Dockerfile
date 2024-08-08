FROM python:3.12.5-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    PYTHONPATH="/app:${PYTHONPATH}"

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m appuser

# Set up the working directory in the container
WORKDIR /app

# Gather all requirements into a single file
COPY requirements.txt /tmp/requirements.txt

# Combine all requirements into a single master requirements file
RUN pip3 install --no-cache-dir --default-timeout=360 -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

# Copy the .env file into the container
COPY .env .

# Copy the rest of the application code
COPY webapp/ /app/webapp/

# Change ownership of the app directory
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Command to start an interactive shell
CMD ["python3", "webpapp/main.py"]