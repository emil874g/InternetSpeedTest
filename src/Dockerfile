FROM python:3.10-slim

WORKDIR /app

# Install dependencies (same as before)
RUN apt-get update && apt-get install -y curl && \
    curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash && \
    apt-get install -y speedtest && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything (preserving your new folder structure)
COPY . .

RUN speedtest --accept-license --accept-gdpr

# UPDATE THE COMMAND to run from the new location
CMD ["python", "-u", "scripts/logger.py"]
