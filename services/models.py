"""Data models for the services layer"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class DownloadJob:
    job_id: str
    symbol: str
    period_id: str
    limit: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    candle_count: int = 0
    status: str = "pending"
    progress: int = 0
    message: str = "Job created"
    file_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "symbol": self.symbol,
            "period_id": self.period_id,
            "limit": self.limit,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "candle_count": self.candle_count,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DownloadJob":
        job = cls(
            job_id=data["job_id"],
            symbol=data["symbol"],
            period_id=data["period_id"],
            limit=data.get("limit"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            candle_count=data.get("candle_count", 0),
            status=data.get("status", "pending"),
            progress=data.get("progress", 0),
            message=data.get("message", "Job created"),
            file_path=data.get("file_path"),
            error=data.get("error"),
        )
        if "created_at" in data:
            job.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            job.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            job.completed_at = datetime.fromisoformat(data["completed_at"])
        return job
