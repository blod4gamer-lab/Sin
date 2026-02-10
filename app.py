import os, time, asyncio, logging, threading
from flask import Flask
import yt_dlp
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# --- إعداد سيرفر ويب صغير لمنع Render من النوم ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "SIN SERVER IS ONLINE"

def run_web_server():
    # Render يتطلب الاستماع على المنفذ 10000 أو المنفذ المخصص في البيئة
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- إعدادات البوت ---
nest_asyncio.apply()
BOT_TOKEN = "8338630448:AAGj2rYfAB-R8vh_NTLrRsLvHnqi794tMDA"
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

class SinEngine:
    @staticmethod
    def download(url, mode, quality=None, progress_hook=None):
        opts = {
            'format': f'{quality}+bestaudio/best' if mode == 'video' else 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_DIR}/sin_%(title)s.%(ext)s',
            'progress_hooks': [progress_hook] if progress_hook else [],
            'quiet': True,
        }
        if mode == 'audio':
            opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            return path.rsplit('.', 1)[0] + ".mp3" if mode == 'audio' else path

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **SIN SERVER LIVE 24/7**\n━━━━━━━━━━━━━━\nأرسل أي رابط للتحميل فوراً:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return
    context.user_data['url'] = url
    kb = [[InlineKeyboardButton("🎬 Video 720p", callback_data="v_720"), InlineKeyboardButton("🎵 Audio MP3", callback_data="a_mp3")]]
    await update.message.reply_text("📥 **إختر الصيغة:**", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('url')
    mode = 'audio' if query.data == 'a_mp3' else 'video'
    q = 'bestvideo[height<=720]' if query.data == 'v_720' else None
    
    msg = await query.edit_message_text("⚡ **SIN SERVER PROCESSING...**")
    
    try:
        path = await asyncio.get_event_loop().run_in_executor(None, SinEngine.download, url, mode, q)
        await query.message.reply_chat_action("upload_document")
        with open(path, 'rb') as f:
            if mode == 'audio':
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=InputFile(f))
            else:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=InputFile(f), supports_streaming=True)
        os.remove(path)
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)[:50]}")

def main():
    # تشغيل سيرفر الويب في خيط (Thread) منفصل
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # تشغيل البوت
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("💎 SERVER STARTED ON RENDER")
    app.run_polling()

if __name__ == "__main__":
    main()
