from pathlib import Path

from flask import jsonify, send_file

from . import api_bp
from services.download_service import DownloadService
from services.plot_service import PlotService
from services.jobs_service import JobService


download_service: DownloadService
plot_service: PlotService
jobs_service: JobService


def init_data_api(
    download_srv: DownloadService,
    plot_srv: PlotService,
    jobs_srv: JobService,
) -> None:
    global download_service, plot_service, jobs_service
    download_service = download_srv
    plot_service = plot_srv
    jobs_service = jobs_srv


@api_bp.route("/download/<job_id>")
def download_file(job_id: str):
    job = jobs_service.get_job(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404
    if job.status != "completed" or not job.file_path:
        return jsonify({"success": False, "error": "File not ready for download"}), 400

    path = Path(job.file_path)
    if not path.exists():
        return jsonify({"success": False, "error": "File not found"}), 404

    return send_file(path, as_attachment=True, download_name=path.name)


@api_bp.route("/view/<job_id>")
def view_plot(job_id: str):
    result = plot_service.build_plot(job_id)
    status = 200 if result.get("success") else 400
    return jsonify(result), status
