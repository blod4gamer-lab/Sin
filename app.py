import os
import asyncio
import logging
import threading
import random
import re
from flask import Flask
import yt_dlp
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# --- إعدادات النظام الأساسية ---
nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SinDownloader")

BOT_TOKEN = "8338630448:AAGj2rYfAB-R8vh_NTLrRsLvHnqi794tMDA"
DOWNLOAD_DIR = "storage"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- نظام التمويه والوكلاء (Dynamic Stealth System) ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.143 Mobile Safari/537.36"
]

# --- خادم استدامة الخدمة (Keep-Alive Server) ---
web_app = Flask(__name__)
@web_app.route('/')
def status():
    return "🚀 SIN DOWNLOADER CORE IS ONLINE", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- المحرك القوي (SIN CORE ENGINE) ---
class SinCore:
    @staticmethod
    def get_optimized_opts(mode, quality=None):
        ua = random.choice(USER_AGENTS)
        opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            'user_agent': ua,
            'referer': 'https://www.google.com/',
            'geo_bypass': True,
            'getcomments': False,
            # تقنية المراوغة عبر بروتوكولات مختلفة
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'tv'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }
        
        if mode == 'audio':
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            })
        else:
            # جلب أفضل جودة متاحة بناءً على الاختيار
            video_fmt = f"bestvideo[height<={quality}]+bestaudio/best" if quality else "bestvideo+bestaudio/best"
            opts.update({'format': video_fmt, 'merge_output_format': 'mp4'})
            
        return opts

# --- معالجات الذكاء الاصطناعي للبوت ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "🔥 **SIN DOWNLOADER v3.0** 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "مرحباً بك في النظام الأكثر استقراراً للتحميل.\n\n"
        "✅ **القدرات الحالية:**\n"
        "• تجاوز حظر العناوين (Anti-Ban System).\n"
        "• استخراج الوسائط بجودة الأصلية.\n"
        "• معالجة سحابية فورية.\n\n"
        "📥 **أرسل أي رابط فيديو للبدء فوراً:**"
    )
    await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)

async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not re.match(r'https?://', url): return

    status_msg = await update.message.reply_text("📡 **جاري الاتصال بالسيرفرات وتجاوز القيود...**")
    
    try:
        # فحص الرابط بذكاء
        with yt_dlp.YoutubeDL({'quiet': True, 'nocheckcertificate': True}) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            title = info.get('title', 'Video Content')
            
        context.user_data['active_url'] = url
        
        buttons = [
            [InlineKeyboardButton("🎬 1080p", callback_data="res_1080"), InlineKeyboardButton("🎬 720p", callback_data="res_720")],
            [InlineKeyboardButton("🎬 480p", callback_data="res_480"), InlineKeyboardButton("🎵 MP3 Audio", callback_data="res_audio")]
        ]
        
        await status_msg.edit_text(
            f"✅ **تم التحقق من الرابط:**\n`{title[:60]}`\n\n**إختر نمط المعالجة:**",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text("⚠️ **يوتيوب يفرض قيوداً صارمة على هذا الرابط.**\nالنظام سيحاول التجاوز تلقائياً، يرجى المحاولة مرة أخرى بعد دقيقة.")

async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    choice = query.data
    url = context.user_data.get('active_url')
    if not url: return

    await query.edit_message_text("⚡ **بدأت عملية السحب السحابي... يرجى الانتظار.**")

    mode = 'audio' if choice == 'res_audio' else 'video'
    quality = choice.split('_')[1] if mode == 'video' else None
    
    try:
        settings = SinCore.get_optimized_opts(mode, quality)
        
        def run_dl():
            with yt_dlp.YoutubeDL(settings) as ydl:
                meta = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(meta)

        raw_file = await asyncio.get_event_loop().run_in_executor(None, run_dl)
        final_file = raw_file.rsplit('.', 1)[0] + ".mp3" if mode == 'audio' else raw_file

        await query.edit_message_text("📦 **اكتملت المعالجة! جاري الرفع لتيليجرام...**")
        
        with open(final_file, 'rb') as file_data:
            if mode == 'audio':
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=InputFile(file_data), caption="✅ @SIN_DOWNLOADER")
            else:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=InputFile(file_data), supports_streaming=True, caption="✅ @SIN_DOWNLOADER")

        if os.path.exists(final_file): os.remove(final_file)
        await query.message.delete()
        
    except Exception as e:
        logger.error(f"Critical Error: {e}")
        await query.edit_message_text("❌ **فشل النظام في تجاوز حماية المنصة حالياً.**\nنصيحة: جرب فيديوهات TikTok أو Instagram فهي تعمل دائماً.")

# --- تشغيل المحرك الرئيسي ---
def start_engine():
    # تشغيل نظام الـ Keep-Alive
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # بناء البوت بنظام الـ Pooling الحديث
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_request))
    app.add_handler(CallbackQueryHandler(process_download))
    
    print("💎 SIN DOWNLOADER ULTIMATE IS LIVE")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    start_engine()
