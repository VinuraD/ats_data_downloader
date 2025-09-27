"""Plot generation service"""

from __future__ import annotations

import os
from typing import Dict

import pandas as pd
from flask import jsonify
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from .jobs_service import JobService


class PlotService:
    """Produces plot data from stored CSV files"""

    def __init__(self, job_service: JobService):
        self.jobs = job_service

    def build_plot(self, job_id: str) -> Dict:
        job = self.jobs.get_job(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}
        if job.status != "completed" or not job.file_path:
            return {"success": False, "error": "Data not ready for viewing"}
        if not os.path.exists(job.file_path):
            return {"success": False, "error": "Data file not found"}

        df = pd.read_csv(job.file_path)
        df["time"] = pd.to_datetime(df["time"])
        if len(df) > 500:
            df = df.tail(500)
        df = df.reset_index(drop=True)
        df["time_str"] = df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(f"{job.symbol} - {job.period_id}", "Volume"),
            row_heights=[0.7, 0.3],
        )

        fig.add_trace(
            go.Candlestick(
                x=df["time_str"].tolist(),
                open=df["open"].tolist(),
                high=df["high"].tolist(),
                low=df["low"].tolist(),
                close=df["close"].tolist(),
                name="OHLC",
                showlegend=False,
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Bar(
                x=df["time_str"].tolist(),
                y=df["volume"].tolist(),
                name="Volume",
                marker_color="rgba(0, 150, 255, 0.6)",
                showlegend=False,
            ),
            row=2,
            col=1,
        )

        fig.update_layout(
            title=f"{job.symbol} - {job.period_id} Candlestick Chart with Volume",
            template="plotly_white",
            height=700,
            hovermode="x unified",
            xaxis_rangeslider_visible=False,
        )
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_xaxes(title_text="Time", row=2, col=1)

        plot_dict = fig.to_dict()
        return {
            "success": True,
            "plot_data": plot_dict,
            "job_info": {
                "symbol": job.symbol,
                "period_id": job.period_id,
                "limit": job.limit,
                "records": len(df),
            },
        }
