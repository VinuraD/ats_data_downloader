from flask import jsonify, request

from . import api_bp
from services.download_service import DownloadService


download_service: DownloadService  # Will be injected in app factory


def init_meta_api(service: DownloadService) -> None:
    global download_service
    download_service = service


@api_bp.route("/exchanges")
def get_exchanges():
    try:
        result = download_service.downloader.get_exchanges()
        return jsonify(result)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@api_bp.route("/symbols")
def get_symbols():
    try:
        search = request.args.get("search", "")
        exchange = request.args.get("exchange", "")
        result = download_service.downloader.get_symbols(search, exchange)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@api_bp.route("/resolutions")
def get_resolutions():
    try:
        result = download_service.downloader.get_resolutions()
        return jsonify(result)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
