FROM python:3.9-slim-buster

RUN apt-get update && apt-get install -y \
    build-essential \
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
    libglib2.0-0 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir numpy==1.21.6
RUN pip install --no-cache-dir opencv-python-headless==4.5.5.64
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p temp_uploads

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "300", "--max-requests", "1000", "app:app"]