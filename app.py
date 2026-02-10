import os
import time
import asyncio
import logging
import threading
from flask import Flask
import yt_dlp
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# --- إعدادات البيئة ---
nest_asyncio.apply()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# التوكن الخاص بك
BOT_TOKEN = "8338630448:AAGj2rYfAB-R8vh_NTLrRsLvHnqi794tMDA"
DOWNLOAD_DIR = "temp_downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- سيرفر الويب لمنع Render من النوم ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "🚀 SIN SERVER IS RUNNING AND HEALTHY", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- محرك التحميل الذكي (المحسن لتجاوز القيود) ---
class SinDownloader:
    @staticmethod
    def get_opts(mode, quality_tag=None):
        # إعدادات متقدمة لتجاوز حظر يوتيوب وطلب تسجيل الدخول
        base_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'outtmpl': f'{DOWNLOAD_DIR}/sin_%(title)s.%(ext)s',
            'restrictfilenames': True,
            # التمويه (Headers) لتبدو كمتصفح حقيقي
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/',
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            # تجاوز قيود العمر والمناطق الجغرافية
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'ios'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }

        if mode == 'audio':
            base_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # اختيار الجودة بدقة
            fmt = f"bestvideo[height<={quality_tag}]+bestaudio/best" if quality_tag else "bestvideo+bestaudio/best"
            base_opts.update({
                'format': fmt,
                'merge_output_format': 'mp4',
            })
        
        return base_opts

# --- معالجات البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    welcome_text = (
        f"👋 **أهلاً بك يا {user} في SIN SERVER**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚡ **سيرفر التحميل الأسرع يعمل الآن في الخلفية**\n"
        "📥 **أرسل رابط فيديو من يوتيوب، تيك توك، أو انستجرام:**"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    wait_msg = await update.message.reply_text("🔍 **جاري فحص الرابط وتجاوز القيود...**")
    
    try:
        # جلب معلومات الفيديو بدون تحميل للتأكد من الرابط
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            title = info.get('title', 'فيديو بدون عنوان')
            
        context.user_data['current_url'] = url
        
        keyboard = [
            [
                InlineKeyboardButton("🎬 1080p", callback_data="v_1080"),
                InlineKeyboardButton("🎬 720p", callback_data="v_720")
            ],
            [
                InlineKeyboardButton("🎬 480p", callback_data="v_480"),
                InlineKeyboardButton("🎵 MP3 Audio", callback_data="a_mp3")
            ]
        ]
        
        await wait_msg.edit_text(
            f"✅ **تم العثور على:**\n`{title[:50]}...`\n\n**إختر الجودة المطلوبة:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await wait_msg.edit_text("❌ **فشل في الوصول للفيديو.**\nقد يكون الفيديو خاصاً أو يتطلب تسجيل دخول صارم.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    url = context.user_data.get('current_url')
    
    if not url:
        await query.edit_message_text("⚠️ حدث خطأ، أرسل الرابط مرة أخرى.")
        return

    await query.edit_message_text("⚙️ **بدأ التحميل عبر سيرفر SIN... يرجى الانتظار**")

    mode = 'audio' if data == 'a_mp3' else 'video'
    quality = data.split('_')[1] if mode == 'video' else None
    
    try:
        opts = SinDownloader.get_opts(mode, quality)
        
        def download_sync():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info_dict)

        file_path = await asyncio.get_event_loop().run_in_executor(None, download_sync)
        
        # تصحيح الامتداد في حالة تحويل الصوت
        if mode == 'audio':
            actual_path = file_path.rsplit('.', 1)[0] + ".mp3"
        else:
            actual_path = file_path

        await query.edit_message_text("🚀 **تم التحميل! جاري الرفع إلى تيليجرام...**")
        
        with open(actual_path, 'rb') as f:
            if mode == 'audio':
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=InputFile(f), caption="✅ SIN SERVER - MP3")
            else:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=InputFile(f), supports_streaming=True, caption="✅ SIN SERVER - MP4")

        # تنظيف الملفات بعد الإرسال
        if os.path.exists(actual_path):
            os.remove(actual_path)
        await query.message.delete()

    except Exception as e:
        logger.error(f"Download Error: {e}")
        await query.edit_message_text(f"❌ **حدث خطأ أثناء المعالجة:**\n`يوتيوب يفرض قيوداً على هذا الرابط حالياً.`")

# --- التشغيل الرئيسي ---
def main():
    # تشغيل سيرفر الويب في الخلفية
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # بناء البوت
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_link))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("💎 SIN SERVER ULTIMATE IS NOW LIVE ON RENDER")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
