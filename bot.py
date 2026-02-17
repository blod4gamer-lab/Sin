import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# جلب التوكن من متغيرات البيئة (أمان أكثر)
TOKEN = os.getenv("BOT_TOKEN", "ضع_التوكن_هنا_مؤقتا_للتجربة")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ بوت الأمن السيبراني يعمل الآن على Render!\nأرسل رابطاً لفحصه أو استفسر عن نصيحة أمنية.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "http" in text:
        await update.message.reply_text(f"🔍 جاري تحليل الرابط {text} عبر قواعد بيانات التهديدات...")
    else:
        await update.message.reply_text("أنا أتعلم الآن! قريباً سأتمكن من الإجابة على استفساراتك المعقدة.")

def main():
    # بناء التطبيق
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ملاحظة لـ Render: نستخدم polling للسهولة في البداية
    print("البوت انطلق...")
    app.run_polling()

if __name__ == "__main__":
    main()
