```
repository_structure: >
  AISTOCKYOUTUBEBot/
  ├── README.md
  ├── requirements.txt
  ├── bot.py
  └── DownloadYoutube/
      ├── download_video.py
      ├── download_mp3.py
      ├── download_playlist.py
      └── download_playlist_mp3.py
readme: |
  # AISTOCKYOUTUBEBot

  AISTOCKYOUTUBEBot is a Telegram bot built in Python that provides several features:

  - **Stock Price Retrieval:**  
    Users can send messages containing stock symbols (prefixed with `$`), and the bot will reply with the latest stock prices. Prices are cached to reduce API calls.

  - **Ollama Integration (AI Query):**  
    Users can send queries to a local Ollama service via the `/o <message>` command.

  - **YouTube Video Download:**  
    Users can download a YouTube video using the `/YO <YouTube URL>` command. The bot uses `yt-dlp` to download videos.

  - **YouTube MP3 Download:**  
    Users can download the audio track of a YouTube video as an MP3 file using the `/MP3 <YouTube URL>` command. This feature uses pytube and pydub for conversion.  
    **Note:** Ensure that [ffmpeg](https://ffmpeg.org/download.html) is installed and available in your system PATH for proper audio conversion.

  ## Requirements

  To install the dependencies, run:

  ```bash
  pip install -r requirements.txt
  ```

  ## Setup

  1. **Clone the Repository:**

     ```bash
     git clone https://github.com/yourusername/AISTOCKYOUTUBEBot.git
     cd AISTOCKYOUTUBEBot
     ```

  2. **Install Dependencies:**

     ```bash
     pip install -r requirements.txt
     ```

  3. **Configure ffmpeg (for MP3 conversion):**

     Download and install ffmpeg, and ensure that the `ffmpeg` executable is added to your system PATH. Verify with:

     ```bash
     ffmpeg -version
     ```

  4. **Configure Your Bot Token:**

     Open `bot.py` and replace `"YOUR_ACTUAL_BOT_TOKEN"` with your Telegram bot token (obtained from BotFather).

  ## Running the Bot

  To start the bot, run:

  ```bash
  python bot.py
  ```

  The bot will begin polling for updates and support the following commands:

  - **/start**: Display a welcome message and list available commands.
  - **/help**: Show a list of commands.
  - **/o <message>**: Send a query to the Ollama service (AI).
  - **/YO <YouTube URL>**: Download a YouTube video.
  - **/MP3 <YouTube URL>**: Download the audio of a YouTube video as an MP3 file.
  - Additionally, users can type stock symbols prefixed with `$` (e.g., `$AAPL`, `$GOOGL`) to retrieve the latest stock prices.

  ## Download Modules

  The `DownloadYoutube` folder contains several scripts for downloading YouTube content:
  - `download_video.py`: Downloads a single YouTube video using yt-dlp.
  - `download_mp3.py`: Downloads and converts the audio of a single YouTube video to MP3 using pytube and pydub.
  - `download_playlist.py` and `download_playlist_mp3.py`: For downloading entire playlists (optional).

  ## License

  This project is licensed under the MIT License.

  ## Contributing

  Contributions are welcome! Feel free to open issues or submit pull requests.

requirements: |
  python-telegram-bot==21.10
  nest_asyncio
  yfinance
  requests
  yt-dlp
  pytube
  pydub
  apscheduler
  pytz
```
