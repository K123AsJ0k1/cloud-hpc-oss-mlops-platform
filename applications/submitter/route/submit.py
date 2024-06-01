from flask import Blueprint, current_app, request, jsonify

import json

from functions.management.jobs import start_job

submit = Blueprint('submit', __name__)

# Refactored and works
@submit.route("/submit", methods=["POST"]) 
def submit_job():
    sent_payload = json.loads(request.json)

    job_submit = sent_payload['submit']
    payload = start_job(
        file_lock = current_app.file_lock,
        logger = current_app.logger,
        allas_client = current_app.allas_client,
        allas_bucket = current_app.allas_bucket,
        kubeflow_user = current_app.kubeflow_user,
        submit = job_submit
    )
    return jsonify(payload)