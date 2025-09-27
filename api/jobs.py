from flask import jsonify, request

from . import api_bp
from services.download_service import DownloadService
from services.jobs_service import JobService


download_service: DownloadService
jobs_service: JobService


def init_jobs_api(download_srv: DownloadService, jobs_srv: JobService) -> None:
    global download_service, jobs_service
    download_service = download_srv
    jobs_service = jobs_srv


@api_bp.route("/jobs")
def list_jobs():
    jobs = [job.to_dict() for job in jobs_service.list_jobs()]
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    return jsonify({"success": True, "jobs": jobs})


@api_bp.route("/jobs", methods=["POST"])
def create_job():
    payload = request.json or {}
    symbol = payload.get("symbol")
    period_id = payload.get("period_id")
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")
    limit = payload.get("limit")

    if not symbol or not period_id:
        return jsonify({"success": False, "error": "Symbol and period_id are required"}), 400

    job = download_service.create_job(symbol, period_id, start_date, end_date, limit)
    return jsonify({"success": True, "job_id": job.job_id, "message": "Download job started"})


@api_bp.route("/jobs/<job_id>", methods=["DELETE"])
def delete_job(job_id: str):
    job = download_service.delete_job(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404
    return jsonify({"success": True, "message": "Job deleted successfully"})
