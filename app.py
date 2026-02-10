import os
import asyncio
import logging
import threading
from flask import Flask
import yt_dlp
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# --- إعدادات النظام ---
nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8338630448:AAGj2rYfAB-R8vh_NTLrRsLvHnqi794tMDA"
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- واجهة الويب الاحترافية ---
web_app = Flask(__name__)
@web_app.route('/')
def home():
    return "🌐 SIN DOWNLOADER API IS ACTIVE", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- محرك التحميل الشامل (SIN ENGINE) ---
class SinEngine:
    @staticmethod
    def get_settings(mode, quality=None):
        settings = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            # تقنية التمويه المتقدمة لتجاوز القيود بدون كوكيز
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/',
            'nocheckcertificate': True,
            'geo_bypass': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios'], # محاكاة تطبيقات الهاتف للهرب من حظر المتصفحات
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }
        if mode == 'audio':
            settings.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            })
        else:
            fmt = f"bestvideo[height<={quality}]+bestaudio/best/best" if quality else "best"
            settings.update({'format': fmt, 'merge_output_format': 'mp4'})
        return settings

# --- معالجات البوت (الواجهة الإعلانية) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "⚡ **SIN DOWNLOADER** ⚡\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "أهلاً بك في أقوى بوت لتحميل الوسائط!\n\n"
        "✨ **مميزاتنا:**\n"
        "• 🚀 تحميل فائق السرعة من +1000 موقع.\n"
        "• 🎬 دعم جميع الجودات حتى 4K.\n"
        "• 🎵 تحويل مباشر إلى MP3 بجودة عالية.\n"
        "• 📱 يدعم TikTok, Instagram, YouTube, Facebook.\n\n"
        "📥 **فقط أرسل الرابط واترك الباقي لنا!**"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return

    status_msg = await update.message.reply_text("🔍 **جاري معالجة الرابط وتحليل البيانات...**")
    
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            title = info.get('title', 'Video')
            
        context.user_data['url'] = url
        buttons = [
            [InlineKeyboardButton("🎬 1080p", callback_data="v_1080"), InlineKeyboardButton("🎬 720p", callback_data="v_720")],
            [InlineKeyboardButton("🎬 480p", callback_data="v_480"), InlineKeyboardButton("🎵 MP3", callback_data="a_mp3")]
        ]
        await status_msg.edit_text(
            f"✅ **تم العثور على:**\n`{title[:60]}`\n\n**إختر الجودة المطلوبة للبدء:**",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        await status_msg.edit_text("❌ **عذراً، هذا الرابط محمي أو غير مدعوم حالياً.**\nجرب رابطاً آخر أو حاول لاحقاً.")

async def download_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    url = context.user_data.get('url')
    if not url: return

    await query.edit_message_text("⏳ **يتم الآن معالجة طلبك عبر سيرفرات SIN...**")

    mode = 'audio' if data == 'a_mp3' else 'video'
    q = data.split('_')[1] if mode == 'video' else None
    
    try:
        opts = SinEngine.get_settings(mode, q)
        def dl():
            with yt_dlp.YoutubeDL(opts) as ydl:
                res = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(res)

        path = await asyncio.get_event_loop().run_in_executor(None, dl)
        final_path = path.rsplit('.', 1)[0] + ".mp3" if mode == 'audio' else path

        await query.edit_message_text("🚀 **اكتمل التحميل! يتم الآن إرسال الملف...**")
        
        with open(final_path, 'rb') as f:
            if mode == 'audio':
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=InputFile(f), caption="✅ @SIN_DOWNLOADER")
            else:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=InputFile(f), caption="✅ @SIN_DOWNLOADER")

        if os.path.exists(final_path): os.remove(final_path)
        await query.message.delete()
    except:
        await query.edit_message_text("❌ **فشل النظام في تجاوز حماية الرابط.**\nهذا المحتوى يتطلب صلاحيات خاصة.")

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(download_action))
    print("💎 SIN DOWNLOADER IS ONLINE")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
