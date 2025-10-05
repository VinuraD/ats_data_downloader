#!/usr/bin/env python3
"""Application entry point."""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_socketio import SocketIO

from downloader import DownloaderFactory
from services.jobs_service import JobService
from services.download_service import DownloadService
from services.plot_service import PlotService
from services.models import DownloadJob
from api import api_bp
from api.jobs import init_jobs_api
from api.data import init_data_api
from api.meta import init_meta_api


load_dotenv()

DATA_FOLDER = Path(os.getenv("DATA_FOLDER", "data"))
STORAGE_FOLDER = Path(os.getenv("STORAGE_FOLDER", "local_storage"))
RUN_LOG_FILE = STORAGE_FOLDER / "run_log.json"
DOWNLOADER_PLATFORM = os.getenv("DOWNLOADER_PLATFORM", "coinapi").lower()
API_KEY = os.getenv("COINAPI_KEY")
BASE_URL = os.getenv("COINAPI_BASE_URL")
PORT = int(os.getenv("PORT", 3010))

DATA_FOLDER.mkdir(parents=True, exist_ok=True)
STORAGE_FOLDER.mkdir(parents=True, exist_ok=True)

if not API_KEY or API_KEY == "your_coinapi_key_here":
    raise SystemExit("API key not configured. See .env settings.")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
socketio = SocketIO(app, cors_allowed_origins="*")

downloader = DownloaderFactory.create_downloader(DOWNLOADER_PLATFORM, API_KEY, BASE_URL)
print(BASE_URL, API_KEY)

jobs_service = JobService(str(RUN_LOG_FILE))
jobs_service.load_jobs()

download_service = DownloadService(downloader, jobs_service, str(DATA_FOLDER), socketio)
plot_service = PlotService(jobs_service)

init_jobs_api(download_service, jobs_service)
init_data_api(download_service, plot_service, jobs_service)
init_meta_api(download_service)

app.register_blueprint(api_bp, url_prefix="/api")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    print(f"🚀 Starting Crypto Data Downloader on port {PORT}")
    print(f"📱 Open your browser to: http://localhost:{PORT}")
    socketio.run(app, debug=True, host="0.0.0.0", port=PORT, allow_unsafe_werkzeug=True)
