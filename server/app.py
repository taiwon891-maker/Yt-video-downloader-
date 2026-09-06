from flask import Flask, render_template, request, send_from_directory, jsonify, current_app
from werkzeug.utils import secure_filename
import yt_dlp
import os
import requests
import logging

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Get API key from environment
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    logging.warning("YOUTUBE_API_KEY is not set in environment variables.")

@app.route('/')
def index():
    return render_template('index.html')

# YouTube search
@app.route('/search')
def search():
    query = request.args.get('q', 'Bangla hit songs')
    page_token = request.args.get('pageToken', '')
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "maxResults": 12,
        "q": query,
        "type": "video",
        "pageToken": page_token,
        "key": YOUTUBE_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        videos = []
        for item in data.get('items', []):
            videos.append({
                "title": item['snippet']['title'],
                "thumbnail": item['snippet']['thumbnails']['high']['url'],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        return jsonify({"videos": videos, "nextPageToken": data.get('nextPageToken', '')})
    except requests.RequestException:
        current_app.logger.exception("YouTube API request failed")
        return jsonify({"videos": [], "nextPageToken": ""}), 502

@app.route('/get_info', methods=['POST'])
def get_info():
    video_url = request.form.get('url')
    ydl_opts = {'quiet': True, 'noplaylist': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        formats = info.get('formats', [])
        play_url = None
        for f in formats[::-1]:
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4' and 'url' in f:
                play_url = f['url']
                break
        if not play_url:
            play_url = info.get('url')
        return jsonify({"title": info.get('title', 'Unknown'), "video_url": play_url, "url": video_url})
    except Exception:
        current_app.logger.exception("Failed to get video info")
        return jsonify({"error": "Failed to retrieve video info"}), 500

@app.route('/download')
def download():
    video_url = request.args.get('url')
    quality = request.args.get('quality', '720p')

    q_map = {
        '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'mp3': 'bestaudio/best'
    }

    ydl_opts = {
        'format': q_map.get(quality, 'best'),
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
    }

    if quality == 'mp3':
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            raw_name = ydl.prepare_filename(info)
            if quality == 'mp3':
                filename = os.path.splitext(raw_name)[0] + '.mp3'
            else:
                filename = raw_name
            safe = secure_filename(os.path.basename(filename))
            file_path = os.path.join(DOWNLOAD_FOLDER, safe)
            if os.path.exists(filename) and filename != file_path:
                os.replace(filename, file_path)
            if not os.path.exists(file_path):
                current_app.logger.error("Expected file not found: %s", file_path)
                return jsonify({"error": "File not found after download"}), 500
            return send_from_directory(DOWNLOAD_FOLDER, safe, as_attachment=True)
    except Exception:
        current_app.logger.exception("Download failed")
        return jsonify({"error": "Download failed"}), 500

@app.route('/get_downloads')
def get_downloads():
    try:
        files = os.listdir(DOWNLOAD_FOLDER)
        return jsonify(files)
    except Exception:
        current_app.logger.exception("Failed to list downloads")
        return jsonify([]), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
