# Dockerfile for hrtool
# Builds a runtime environment for the hrtool HEAD Component Manager.
# Based on Python 3 with Debian packages needed for hrtool operation.
FROM python:3.8-slim

# Install system dependencies needed by hrtool and PySide
RUN apt-get update && apt-get install -y --no-install-recommends \
    dpkg \
    python3-yaml \
    && rm -rf /var/lib/apt/lists/*

# Install Python runtime dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
WORKDIR /hrtool
COPY . .

# Set default command - the GUI app will be run with `python manager.py`
# or headless hr commands can be invoked via: docker exec container hr cmd ...
CMD ["python", "manager.py"]