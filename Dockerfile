FROM python:3.9-slim-buster

# Install essential system dependencies
# Combine related packages for efficiency and clarity.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \ # pkg-config is often helpful for C/C++ libraries
    gcc \
    g++ \
    gfortran \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libzbar0 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    libavcodec58 \
    libavformat58 \
    libavutil56 \
    libswscale5 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Upgrade pip, setuptools, wheel first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install core scientific stack dependencies first, in a specific order
# This often helps resolve complex binary linking issues.
RUN pip install --no-cache-dir numpy==1.23.5 # Match the version in requirements.txt
RUN pip install --no-cache-dir scipy==1.7.3 # Match the version in requirements.txt
RUN pip install --no-cache-dir opencv-python-headless==4.5.5.64 # Match the version in requirements.txt

# Install the rest of the dependencies from requirements.txt
# Using --requirement again ensures everything else is installed.
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure 'temp_uploads' directory exists if your app needs it
RUN mkdir -p temp_uploads

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

# Use the full path for gunicorn for robustness
CMD ["/usr/local/bin/gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "300", "--max-requests", "1000", "app:app"]
