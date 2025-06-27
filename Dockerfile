# Use a slim Python base
FROM python:3.9-slim
# Install system dependencies (for Pillow, Matplotlib, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libjpeg-dev \
      libfreetype6-dev \
      libpng-dev \
      libssl-dev \
      libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy & install Python deps globally
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# Copy in your code
COPY . .

# Expose Shiny’s port
EXPOSE 8000

# Launch the app
CMD ["python", "app.py"]
