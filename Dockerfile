# Slim မဟုတ်သော Full Version ကို သုံးမည် (SSL ပြဿနာ ကင်းရှင်းစေရန်)
FROM python:3.9

# ffmpeg ကို install လုပ်မည်
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Work Directory
WORKDIR /app

# Library များ သွင်းမည်
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Code များ ကူးထည့်မည်
COPY . .

# Start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
