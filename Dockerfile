FROM python:3.10-slim

# تثبيت ffmpeg لتشغيل عمليات التحويل الصوتي
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# تحديد مجلد العمل
WORKDIR /app

# نسخ جميع الملفات إلى السيرفر
COPY . .

# تثبيت المكتبات من ملف requirements
RUN pip install --no-cache-dir -r requirements.txt

# أمر تشغيل البوت
CMD ["python", "app.py"]
