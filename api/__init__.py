from flask import Blueprint

api_bp = Blueprint("api", __name__)

from . import jobs, data, meta  # noqa: E402,F401
