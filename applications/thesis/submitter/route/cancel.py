from flask import Blueprint, current_app, request, jsonify

import json

from functions.management.jobs import stop_job

cancel = Blueprint('cancel', __name__)

@cancel.route("/cancel", methods=["POST"])
def cancel_job():
    payload = stop_job(
        file_lock = current_app.file_lock,
        logger = current_app.logger,
        allas_client = current_app.allas_client,
        allas_bucket = current_app.allas_bucket,
        kubeflow_user = current_app.kubeflow_user
    )
    return jsonify(payload)