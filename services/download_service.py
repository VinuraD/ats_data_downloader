"""Download workflow service"""

from __future__ import annotations

import os
import threading
import uuid
from datetime import datetime
from typing import Optional

from flask_socketio import SocketIO

from downloader import BaseDownloader
from .jobs_service import JobService
from .models import DownloadJob


class DownloadService:
    """Orchestrates background downloads"""

    def __init__(
        self,
        downloader: BaseDownloader,
        job_service: JobService,
        data_folder: str,
        socketio: SocketIO,
    ):
        self.downloader = downloader
        self.jobs = job_service
        self.data_folder = data_folder
        self.socketio = socketio

    def create_job(
        self,
        symbol: str,
        period_id: str,
        start_date: Optional[str],
        end_date: Optional[str],
        limit: Optional[int] = None,
    ) -> DownloadJob:
        job_id = str(uuid.uuid4())
        job = DownloadJob(
            job_id=job_id,
            symbol=symbol,
            period_id=period_id,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )
        self.jobs.add_job(job)
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()
        return job

    def _run_job(self, job_id: str) -> None:
        job = self.jobs.get_job(job_id)
        if not job:
            return

        try:
            job.status = "running"
            job.started_at = datetime.now()
            job.message = f"Fetching data from {self.downloader.platform_name}..."
            self._notify(job)

            job.progress = 25
            job.message = "Making API request..."
            self._notify(job)

            result = self.downloader.download_ohlcv(
                job.symbol,
                job.period_id,
                job.start_date,
                job.end_date,
                job.limit,
            )
            if not result["success"]:
                raise RuntimeError(result["error"])

            data = result["data"]
            job.candle_count = result.get("count", len(data)) if data else 0

            job.progress = 50
            job.message = "Processing data..."
            self._notify(job)

            processed_df = self.downloader.process_ohlcv_data(data)

            job.progress = 75
            job.message = "Saving to CSV..."
            self._notify(job)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{job.symbol}_{job.period_id}_{timestamp}.csv"
            filepath = os.path.join(self.data_folder, filename)
            processed_df.to_csv(filepath, index=False)

            job.progress = 100
            job.status = "completed"
            job.message = f"Download completed - {job.start_date or 'start?'}"
            job.file_path = filepath
            job.completed_at = datetime.now()
            self._notify(job)
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            job.message = f"Error: {exc}"
            self._notify(job)
        finally:
            self.jobs.update_job(job)

    def delete_job(self, job_id: str) -> Optional[DownloadJob]:
        job = self.jobs.delete_job(job_id)
        if job and job.file_path and os.path.exists(job.file_path):
            try:
                os.remove(job.file_path)
            except OSError as exc:
                print(f"⚠️ Failed to delete file {job.file_path}: {exc}")
        return job

    def _notify(self, job: DownloadJob) -> None:
        self.jobs.update_job(job)
        self.socketio.emit("job_update", job.to_dict())
