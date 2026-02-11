import os
import asyncio
import logging
import threading
import random
import re
import time
from flask import Flask
import yt_dlp
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# --- إعدادات النظام المحصنة ---
nest_asyncio.apply()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIN_SYSTEM")

# الإعدادات الثابتة (لا تحتاج لتغييرها)
BOT_TOKEN = "8338630448:AAGj2rYfAB-R8vh_NTLrRsLvHnqi794tMDA"
PORT = 8000 
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- نظام الحفاظ على النشاط (Anti-Sleep System) ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return f"🚀 SIN DOWNLOADER CORE IS LIVE\nUptime: {time.strftime('%H:%M:%S')}", 200

def run_web_server():
    # يعمل على المنفذ 8000 ليتوافق مع Koyeb تلقائياً
    web_app.run(host='0.0.0.0', port=PORT)

# --- محرك التحميل المتطور (SIN ULTIMATE ENGINE) ---
class SinEngine:
    @staticmethod
    def get_dynamic_opts(mode, quality=None):
        # قائمة وكلاء مستخدمين لتبديل الهوية في كل طلب
        uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.164 Mobile Safari/537.36"
        ]
        
        opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'outtmpl': f'{DOWNLOAD_DIR}/sin_%(title)s.%(ext)s',
            'user_agent': random.choice(uas),
            'referer': 'https://www.google.com/',
            'geo_bypass': True,
            'wait_for_video': 5,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'tv'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }

        if mode == 'audio':
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # اختيار الجودة بذكاء مع دعم الدمج التلقائي
            best_fmt = f"bestvideo[height<={quality}]+bestaudio/best" if quality else "bestvideo+bestaudio/best"
            opts.update({
                'format': best_fmt,
                'merge_output_format': 'mp4',
            })
        return opts

# --- معالجات التفاعل (UX/UI) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🔥 **SIN DOWNLOADER v4.0**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "مرحباً بك في النظام السحابي المتكامل للتحميل.\n\n"
        "⚡ **المزايا المفعّلة الآن:**\n"
        "• تجاوز الحظر التلقائي (Anti-Block).\n"
        "• معالجة الفيديوهات بجميع الجودات.\n"
        "• استخراج الصوت بجودة Hi-Fi.\n"
        "• حماية كاملة للمحتوى والخصوصية.\n\n"
        "📥 **أرسل رابط الوسائط للبدء فوراً:**"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return

    status_msg = await update.message.reply_text("📡 **جاري فحص الرابط وتجاوز الجدران النارية...**")
    
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'nocheckcertificate': True}) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            title = info.get('title', 'Video Content')
            duration = info.get('duration_string', 'Unknown')
            
        context.user_data['url'] = url
        
        btns = [
            [InlineKeyboardButton("🎬 1080p", callback_data="res_1080"), InlineKeyboardButton("🎬 720p", callback_data="res_720")],
            [InlineKeyboardButton("🎬 480p", callback_data="res_480"), InlineKeyboardButton("🎵 MP3 Audio", callback_data="res_audio")]
        ]
        
        await status_msg.edit_text(
            f"✅ **تم العثور على المحتوى:**\n`{title[:60]}`\n⏱ **المدة:** {duration}\n\n**إختر التنسيق المطلوب:**",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text("❌ **فشل الوصول للرابط.**\nقد يكون المحتوى خاصاً أو يتطلب اشتراكاً.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('url')
    if not url: return

    choice = query.data.split('_')[1]
    mode = 'audio' if choice == 'audio' else 'video'
    quality = choice if mode == 'video' else None
    
    await query.edit_message_text("⚙️ **جاري سحب المحتوى ومعالجته سحابياً...**")
    
    try:
        opts = SinEngine.get_dynamic_opts(mode, quality)
        
        def run_download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info_dict)

        path = await asyncio.get_event_loop().run_in_executor(None, run_download)
        final_path = path.rsplit('.', 1)[0] + ".mp3" if mode == 'audio' else path

        await query.edit_message_text("🚀 **اكتمل التحميل! يتم الآن الرفع النهائي...**")
        
        with open(final_path, 'rb') as f:
            if mode == 'audio':
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=InputFile(f), caption="✅ @SIN_DOWNLOADER")
            else:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=InputFile(f), supports_streaming=True, caption="✅ @SIN_DOWNLOADER")

        if os.path.exists(final_path): os.remove(final_path)
        await query.message.delete()
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        await query.edit_message_text("❌ **حدث خطأ تقني أثناء التحميل.**\nحاول مجدداً مع رابط آخر.")

# --- بدء التشغيل الفعلي ---
def main():
    # تشغيل السيرفر في خيط مستقل لمنع Koyeb من إغلاق الخدمة
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # بناء تطبيق البوت
    app = Application.builder().token(BOT_TOKEN).build()
    
    # الروابط والأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("💎 SIN SYSTEM IS ONLINE AND SECURED ON KOYEB")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
