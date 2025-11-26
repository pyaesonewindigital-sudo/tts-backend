# Python Image ကို အခြေခံယူမည်
FROM python:3.9-slim

# System တွင် ffmpeg ကို install လုပ်မည် (SRT timing အတွက် မရှိမဖြစ်)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Work Directory သတ်မှတ်မည်
WORKDIR /app

# Library များ သွင်းမည်
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code များ ကူးထည့်မည်
COPY . .

# Port ဖွင့်ပြီး Start မည်
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]