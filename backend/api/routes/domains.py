"""
Domain endpoints
"""
from flask import Blueprint, jsonify
from backend.core.models import Domain

domains_bp = Blueprint("domains", __name__)


@domains_bp.route("/api/domains", methods=["GET"])
def domains():
    return jsonify({"domains": [d.to_dict() for d in Domain.query.all()]}), 200
