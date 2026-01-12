FROM python:3.10-slim

# Install system dependencies for ffmpeg and git (for some pip packages)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

COPY . .

# Create downloads directory
RUN mkdir -p downloads

CMD ["flask", "run", "--host=0.0.0.0"]
