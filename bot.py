import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# تنظیم logging برای مشاهده خطاها
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'سلام! به ربات آموزش زبان خوش آمدید.\nلطفاً زبان مورد نظر خود را انتخاب کنید.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'دستورات:\n/start - شروع ربات\n/help - راهنمای دستورات'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # در اینجا می‌توانید منطق آموزشی زبان را اضافه کنید؛ برای مثال ترجمه یا تمرین‌های لغت‌سازی
    translated = translate_text(text)
    await update.message.reply_text(
        f"شما نوشتید: {text}\nترجمه (نمونه): {translated}"
    )

def translate_text(text: str) -> str:
    # در این نمونه تنها متن ورودی را برمی‌گرداند.
    return text

async def main():
    # جایگزین کردن 'YOUR_TELEGRAM_BOT_TOKEN' با توکن واقعی دریافتی از BotFather
    application = ApplicationBuilder().token("7783488437:AAF1xOSs9-o7kVh7JJ8VMD3ED907CZn9rcE").build()

    # ثبت هندلرهای دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # شروع polling برای دریافت به‌روزرسانی‌ها
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
