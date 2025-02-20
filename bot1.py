import sys
# Add the path to the DownloadYoutube repository so that its modules can be imported.
sys.path.append("E:/git/bot/telegrambot/DownloadYoutube")

# Attempt to import the MP3 download function.
_download_mp3 = None
try:
    import download_mp3
    if hasattr(download_mp3, 'download_youtube_mp3'):
        _download_mp3 = download_mp3.download_youtube_mp3
    else:
        _download_mp3 = None
except ImportError:
    _download_mp3 = None

def download_mp3_wrapper_result(url: str, output_path: str = "./downloads") -> str:
    """
    Calls the download_youtube_mp3 function and returns the most recently created
    MP3 file in the output folder.
    """
    if _download_mp3 is None:
        return "DownloadYoutube MP3 module not installed or function not found."
    try:
        import os
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        # Call the MP3 download function; it should return the new file path.
        mp3_file = _download_mp3(url, output_path=output_path)
        # Wait a bit for the file system to update.
        import time
        time.sleep(5)
        # List all .mp3 files in the folder for debugging.
        import glob
        files = glob.glob(f"{output_path}/*.mp3")
        print("DEBUG: MP3 files found:", files)
        if mp3_file and os.path.isfile(mp3_file):
            return mp3_file
        elif files:
            latest_file = max(files, key=os.path.getctime)
            return latest_file
        else:
            return "No MP3 file found after download. Please check the downloads folder."
    except Exception as e:
        return f"Error in MP3 download function: {e}"

def download_mp3_wrapper(url: str, output_path: str = "./downloads") -> str:
    return download_mp3_wrapper_result(url, output_path)

# (The rest of the bot.py remains unchanged for video download, stock price, and Ollama integration.)

import re
import nest_asyncio
nest_asyncio.apply()

import logging
import pytz
import asyncio
import apscheduler.util as aps_util  # For patching APScheduler
import subprocess  # For running CLI commands
import requests    # For HTTP requests
import yfinance as yf  # To get stock prices

# Patch get_localzone to always return pytz.UTC.
aps_util.get_localzone = lambda: pytz.UTC

from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    JobQueue
)

# Configure logging.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

#######################################
# Stock Price Functionality with Caching
#######################################
import time

price_cache = {}

def get_stock_price(stock_symbol: str, cache_duration=300):
    current_time = time.time()
    if stock_symbol in price_cache:
        timestamp, price = price_cache[stock_symbol]
        if current_time - timestamp < cache_duration:
            return price
    try:
        ticker = yf.Ticker(stock_symbol)
        if hasattr(ticker, "fast_info"):
            price = ticker.fast_info.last_price
            if price is not None:
                price_cache[stock_symbol] = (current_time, price)
                return price
        df = ticker.history(period='1d')
        if df.empty:
            df = ticker.history(period='1mo')
        if not df.empty:
            price = df['Close'].iloc[-1]
            price_cache[stock_symbol] = (current_time, price)
            return price
        return None
    except Exception as e:
        error_message = str(e)
        print(f"Error fetching stock price for {stock_symbol}: {error_message}")
        if "Too Many Requests" in error_message:
            return "Rate limited. Try again later."
        return None

#######################################
# Ollama Integration via CLI
#######################################
def query_ollama(prompt: str) -> str:
    try:
        proc = subprocess.Popen(
            ["ollama", "run", "deepseek-r1:14b"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(input=(prompt + "\n").encode("utf-8"), timeout=30)
        result = stdout.decode("utf-8").strip()
        if result:
            return result
        else:
            return f"No response received. Stderr: {stderr.decode('utf-8').strip()}"
    except Exception as e:
        return f"Error contacting Ollama CLI: {e}"

#######################################
# Telegram Bot Handlers
#######################################
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Welcome to Mehran Bot.\n"
        "To get a stock price, type the stock symbol prefixed with $, e.g., $AAPL or $GOOGL.\n"
        "To interact with Ollama, use the command /o <your message>.\n"
        "To download a YouTube video, use the command /YO <YouTube URL>.\n"
        "To download a YouTube video as MP3, use the command /MP3 <YouTube URL>.\n"
        "You can also send a stock symbol with $ to get its price."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/o <message> - Send a query to Ollama via CLI\n"
        "/YO <YouTube URL> - Download a YouTube video\n"
        "/MP3 <YouTube URL> - Download a YouTube video as MP3\n"
        "You can also send a stock symbol with $ to get its price."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    pattern = r'\$[A-Za-z]+'
    matches = re.findall(pattern, text)
    if matches:
        responses = []
        for match in matches:
            stock_symbol = match.lstrip('$').upper()
            price = get_stock_price(stock_symbol)
            if price is not None:
                responses.append(f"{stock_symbol} price: {price}")
            else:
                responses.append(f"No price found for {stock_symbol}.")
        await update.message.reply_text("\n".join(responses))
    else:
        await update.message.reply_text(f"You wrote: {text}")

async def ollama_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Please enter a message, e.g., /o Hello, how are you?")
        return
    answer = query_ollama(prompt)
    await update.message.reply_text(f"Ollama response:\n{answer}")

async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a YouTube URL, e.g., /YO https://www.youtube.com/watch?v=...")
        return
    url = context.args[0]
    output_folder = "./downloads"
    try:
        result = download_video_wrapper(url, output_folder)
        import os
        if os.path.isfile(result):
            await update.message.reply_text("Video downloaded successfully. Uploading...")
            with open(result, "rb") as video_file:
                await update.message.reply_video(video=InputFile(video_file), caption="Here is your video!")
        else:
            await update.message.reply_text(f"Download failed: {result}")
    except Exception as e:
        await update.message.reply_text(f"Error during download: {e}")

async def download_mp3_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a YouTube URL, e.g., /MP3 https://www.youtube.com/watch?v=...")
        return
    url = context.args[0]
    output_folder = "./downloads"
    try:
        result = download_mp3_wrapper(url, output_folder)
        import os
        if os.path.isfile(result):
            await update.message.reply_text("MP3 downloaded successfully. Uploading...")
            with open(result, "rb") as audio_file:
                await update.message.reply_audio(audio=InputFile(audio_file), caption="Here is your MP3!")
        else:
            await update.message.reply_text(f"MP3 download failed: {result}")
    except Exception as e:
        await update.message.reply_text(f"Error during MP3 download: {e}")

#######################################
# Main function to run the bot
#######################################
async def main():
    job_queue = JobQueue()
    application = (
        ApplicationBuilder()
        .token("7783488437:AAF1xOSs9-o7kVh7JJ8VMD3ED907CZn9rcE")  # Replace with your actual bot token
        .job_queue(job_queue)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("o", ollama_command))
    application.add_handler(CommandHandler("YO", download_command))
    application.add_handler(CommandHandler("MP3", download_mp3_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await application.run_polling(close_loop=False)

if __name__ == '__main__':
    asyncio.run(main())
