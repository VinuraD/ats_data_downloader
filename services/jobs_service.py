"""Job management service"""

import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional

from .models import DownloadJob


class JobService:
    """Handles job storage and retrieval"""

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.jobs: Dict[str, DownloadJob] = {}
        self.lock = threading.Lock()

    def load_jobs(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r") as f:
                raw_jobs = json.load(f)
            with self.lock:
                for job_data in raw_jobs:
                    job = DownloadJob.from_dict(job_data)
                    self.jobs[job.job_id] = job
        except Exception as exc:
            print(f"❌ Failed to load jobs: {exc}")

    def save_jobs(self) -> None:
        try:
            with self.lock:
                payload = [job.to_dict() for job in self.jobs.values()]
            with open(self.storage_path, "w") as f:
                json.dump(payload, f, indent=2)
        except Exception as exc:
            print(f"❌ Failed to save jobs: {exc}")

    def add_job(self, job: DownloadJob) -> None:
        with self.lock:
            self.jobs[job.job_id] = job
        self.save_jobs()

    def update_job(self, job: DownloadJob) -> None:
        self.add_job(job)

    def delete_job(self, job_id: str) -> Optional[DownloadJob]:
        with self.lock:
            job = self.jobs.pop(job_id, None)
        if job:
            self.save_jobs()
        return job

    def list_jobs(self) -> List[DownloadJob]:
        with self.lock:
            return list(self.jobs.values())

    def get_job(self, job_id: str) -> Optional[DownloadJob]:
        with self.lock:
            return self.jobs.get(job_id)
