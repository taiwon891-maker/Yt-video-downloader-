# Yt-video-downloader-

A small Flask web app to search and download YouTube videos using yt-dlp.

Important: DO NOT commit your real API keys. Set the YOUTUBE_API_KEY environment variable before running.

Quick start

1. Install system deps: ffmpeg is required for audio extraction.
   - Ubuntu: sudo apt install ffmpeg
2. Create a virtualenv and install requirements:
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
3. Set environment variable and run:
   export YOUTUBE_API_KEY=YOUR_KEY
   python server/app.py

Notes
- This initial branch provides a simple synchronous implementation. For production you should:
  - Rotate API keys and store secrets in environment/config management.
  - Move downloads to a background worker (Celery/RQ) and stream files to users.
  - Add authentication and rate limiting to prevent abuse.
