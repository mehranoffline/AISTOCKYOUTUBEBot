import sys

import os

import logging

import asyncio

import subprocess

from pathlib import Path

from typing import Optional

import pytz

import yfinance as yf

import requests

from dotenv import load_dotenv

import re  # Import the re module for regex



# Optionally apply nest_asyncio if needed (e.g. in notebook environments)

try:

    import nest_asyncio

    nest_asyncio.apply()

except ImportError:

    pass



# Load environment variables from .env file

load_dotenv()



# Configure logging

logging.basicConfig(

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",

    level=logging.INFO,

)

logger = logging.getLogger(__name__)



# Constants

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB (Telegram file size limit)

DOWNLOADS_DIR = Path("./downloads")

DOWNLOADS_DIR.mkdir(exist_ok=True)



# Add module path dynamically for YouTube download module

current_dir = Path(__file__).parent

sys.path.append(str(current_dir / "DownloadYoutube"))



# Import YouTube download module

try:

    from download_video import download_with_ytdlp as _download_video

except ImportError:

    _download_video = None

    logger.warning("YouTube download module not found. Video download functionality will be disabled.")



# Telegram imports

from telegram import Update, InputFile

from telegram.ext import (

    ApplicationBuilder,

    CommandHandler,

    ContextTypes,

    MessageHandler,

    filters,

)



async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Handle errors in Telegram handlers."""

    logger.error("Exception while handling update:", exc_info=context.error)

    if update and update.effective_message:

        try:

            await update.effective_message.reply_text(

                "An error occurred while processing your request. Please try again later."

            )

        except Exception as e:

            logger.error(f"Failed to send error message: {e}")



def get_stock_price(stock_symbol: str) -> Optional[float]:

    """Retrieve current stock price using yfinance."""

    try:

        ticker = yf.Ticker(stock_symbol)

        data = ticker.history(period="1d", interval="1m")

        if not data.empty:

            return data["Close"].iloc[-1]

        # Fallback to fast_info if history is empty

        return getattr(ticker.fast_info, "last_price", None)

    except Exception as e:

        logger.error(f"Error fetching stock price for {stock_symbol}: {e}")

        return None



async def query_ollama(prompt: str) -> str:

    """Query Ollama using an asynchronous subprocess."""

    try:

        proc = await asyncio.create_subprocess_exec(

            "ollama", "run", "deepseek-r1:14b",

            stdin=subprocess.PIPE,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

        )

        try:

            stdout, stderr = await asyncio.wait_for(

                proc.communicate(input=f"{prompt}\n".encode()),

                timeout=30,

            )

        except asyncio.TimeoutError:

            proc.kill()

            return "Error: Request timed out after 30 seconds"



        if proc.returncode != 0:

            error_message = stderr.decode().strip()

            logger.error(f"Ollama returned non-zero exit code: {error_message}")

            return f"Error: {error_message}"

        return stdout.decode().strip()

    except Exception as e:

        logger.error(f"Ollama query error: {e}")

        return "Error processing your request"



async def download_video(url: str) -> Path:

    """Download a YouTube video with error handling."""

    if not _download_video:

        raise RuntimeError("YouTube download module not available")

    try:

        file_path = await asyncio.to_thread(

            _download_video,

            url,

            output_path=str(DOWNLOADS_DIR),

        )

        return Path(file_path)

    except Exception as e:

        logger.error(f"Video download failed for URL {url}: {e}")

        raise



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Send welcome/help message with available commands."""

    message = (

        "📈 Welcome to FinanceBot!\n\n"

        "Available commands:\n"

        "$SYMBOL - Get stock price (e.g., $AAPL)\n" # Changed to $SYMBOL

        "/OL [PROMPT] - Query AI assistant\n" # Changed to /OL

        "/YO [URL] - Download YouTube video\n" # Changed to /YO

        "/help - Show help"

    )

    await update.message.reply_text(message)



# Removed handle_stock function



async def handle_ol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # Renamed to handle_ol

    """Handle /OL command to send a prompt to the AI assistant.""" # Updated description

    if not context.args:

        await update.message.reply_text("Please provide a query. Usage: /OL What is the market trend?") # Updated usage

        return



    prompt = " ".join(context.args)

    logger.info(f"Querying Ollama with prompt: {prompt}")

    response = await query_ollama(prompt)

    await update.message.reply_text(f"🤖 AI Response:\n\n{response}")



async def handle_yo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # Renamed to handle_yo

    """Handle /YO command to download a YouTube video.""" # Updated description

    if not context.args:

        await update.message.reply_text("Please provide a YouTube URL. Usage: /YO <URL>") # Updated usage

        return



    url = context.args[0]

    logger.info(f"Starting download for URL: {url}")

    message = await update.message.reply_text("⏳ Starting download...")

    file_path: Optional[Path] = None

    try:

        file_path = await download_video(url)

        await message.edit_text("✅ Download complete! Uploading...")

        if file_path.stat().st_size > MAX_FILE_SIZE:

            await message.edit_text("❌ File too large to send via Telegram.")

            return

        with file_path.open("rb") as f:

            await update.message.reply_video(

                video=InputFile(f),

                caption="Here's your video!",

                supports_streaming=True,

            )

        await message.delete()

    except Exception as e:

        logger.error(f"Error in handle_download: {e}") # Keep original logger message for clarity, though function name changed locally

        await message.edit_text(f"❌ Download failed: {e}")

    finally:

        if file_path is not None and file_path.exists():

            try:

                file_path.unlink()

                logger.info(f"Temporary file {file_path} removed.")

            except Exception as e:

                logger.error(f"Failed to remove temporary file {file_path}: {e}")



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Handle text messages to check for stock symbols."""

    text = update.message.text

    # Recognize stock symbols using Regex (symbols starting with $)

    pattern = r'\$[A-Za-z]+'

    matches = re.findall(pattern, text)



    if matches:

        responses = []

        for match in matches:

            stock_symbol = match.lstrip('$').upper()

            price = await asyncio.to_thread(get_stock_price, stock_symbol)

            if price is not None:

                responses.append(f"Price of {stock_symbol}: ${price:.2f}") # Updated response message

            else:

                responses.append(f"Could not fetch price for {stock_symbol}.") # Updated response message

        await update.message.reply_text('\n'.join(responses))

    else:

        await update.message.reply_text(f"You wrote: {text}") # Uncommented and indented



async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Handle unknown commands."""

    await update.message.reply_text("Sorry, I didn't understand that command. Use /help to see available commands.")



async def _post_init(app: ApplicationBuilder): # Make it an async function

    logger.info("Bot started successfully.")



def main() -> None:

    """Initialize and run the Telegram bot."""

    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:

        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")

        return



    application = (

        ApplicationBuilder()

        .token(token)

        .post_init(_post_init) # Pass the async function itself

        .build()

    )



    # Register command handlers

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("help", start))

    # application.add_handler(CommandHandler("stock", handle_stock)) # Removed /stock command handler

    application.add_handler(CommandHandler("OL", handle_ol)) # Changed to OL, and handle_ol

    application.add_handler(CommandHandler("YO", handle_yo)) # Changed to YO, and handle_yo

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)) # Keep message handler for $SYMBOL



    # Catch-all for unknown commands (should be the last handler)

    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))



    # Register error handler

    application.add_error_handler(error_handler)



    logger.info("Starting bot polling...")

    application.run_polling()



if __name__ == "__main__":

    main()