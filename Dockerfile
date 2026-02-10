FROM python:3.10-slim

# تثبيت التحديثات و ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# تحديد المجلد
WORKDIR /app

# نسخ الملفات
COPY . .

# تثبيت المكتبات بشكل مباشر لضمان عدم حدوث خطأ
RUN pip install --no-cache-dir python-telegram-bot yt-dlp flask nest_asyncio

# تشغيل البوت
CMD ["python", "app.py"]
