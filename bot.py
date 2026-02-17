import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# الإعدادات (سيتم جلبها من Render Environment Variables)
TOKEN = os.getenv("BOT_TOKEN")
VT_API_KEY = "2f910adde235ae2d78052362bec7ab3af7e8fadd5f07c16e73a303d18b4040c1"

# 1. وظيفة فحص الروابط عبر VirusTotal
def check_vt_url(url):
    headers = {"x-apikey": VT_API_KEY}
    # إرسال الرابط للتحليل
    payload = {"url": url}
    try:
        response = requests.post("https://www.virustotal.com/api/v3/urls", data=payload, headers=headers)
        if response.status_code == 200:
            analysis_id = response.json()['data']['id']
            # جلب التحليل الفوري
            analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
            res = requests.get(analysis_url, headers=headers).json()
            stats = res['data']['attributes']['stats']
            
            malicious = stats['malicious']
            suspicious = stats['suspicious']
            harmless = stats['harmless']
            
            if malicious > 0:
                return f"❌ **تحذير خطير!**\nتم اكتشاف {malicious} محركات تعتبر هذا الرابط خبيثاً!"
            elif suspicious > 0:
                return f"⚠️ **تنبيه:** الرابط مشبوه وفقاً لـ {suspicious} محركات."
            else:
                return f"✅ **آمن:** {harmless} محرك فحص أكدوا سلامة الرابط."
        return "❌ خطأ في الاتصال بقاعدة بيانات VirusTotal."
    except Exception as e:
        return f"❌ حدث خطأ تقني: {str(e)}"

# 2. وظيفة فحص ثغرات إعدادات الموقع
def scan_headers(url):
    try:
        if not url.startswith('http'): url = 'http://' + url
        response = requests.get(url, timeout=10)
        h = response.headers
        report = "🛡️ **تقرير أمن الموقع:**\n"
        
        checks = {
            'X-Frame-Options': 'ثغرة Clickjacking (إخفاء الواجهة)',
            'Content-Security-Policy': 'ثغرات الحقن و XSS',
            'Strict-Transport-Security': 'تشفير HSTS'
        }
        
        found_issues = 0
        for header, desc in checks.items():
            if header not in h:
                report += f"⚠️ مفقود: {desc}\n"
                found_issues += 1
        
        if found_issues == 0:
            report += "✅ إعدادات الحماية الأساسية ممتازة!"
        return report
    except:
        return "❌ لم أتمكن من الوصول للموقع لفحص ثغراته."

# --- أوامر البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ **مرحباً بك في بوت الأمن السيبراني الذكي!**\n\n"
        "أرسل لي أي رابط الآن وسأقوم بـ:\n"
        "1️⃣ فحص الرابط عبر +70 برنامج حماية.\n"
        "2️⃣ كشف ثغرات الإعدادات في الموقع.\n\n"
        "مثال: `https://google.com`"
    )

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "http" in text:
        await update.message.reply_text("⏳ جاري التحليل العميق... انتظر ثانية.")
        
        # تنفيذ الفحوصات
        vt_result = check_vt_url(text)
        header_result = scan_headers(text)
        
        final_msg = f"🔍 **نتائج الفحص لـ:** {text}\n\n{vt_result}\n\n{header_result}"
        await update.message.reply_text(final_msg, parse_mode='Markdown')
    else:
        await update.message.reply_text("الرجاء إرسال رابط صحيح ليبدأ الفحص.")

def main():
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت!")
        return
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))
    
    print("🚀 البوت انطلق...")
    app.run_polling()

if __name__ == "__main__":
    main()
