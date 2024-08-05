from flask import Blueprint, current_app, request, jsonify

from functions.management.artifacts import fetch_job_status, fetch_job_seff, fetch_job_sacct, fetch_job_logs

import json

artifacts = Blueprint('artifacts', __name__)

# Created and works
@artifacts.route("/job/status", methods=["GET"])
def get_status():
    payload = fetch_job_status(
        file_lock = current_app.file_lock,
        allas_client = current_app.allas_client,
        allas_bucket = current_app.allas_bucket,
        kubeflow_user = current_app.kubeflow_user
    )
    return jsonify(payload)
# Created and works
@artifacts.route("/job/seff", methods=["GET"])
def get_job_seff():
    sent_payload = json.loads(request.json)

    job_id = sent_payload['job-id']

    payload = fetch_job_seff(
        file_lock = current_app.file_lock,
        allas_client = current_app.allas_client,
        allas_bucket = current_app.allas_bucket,
        kubeflow_user = current_app.kubeflow_user,
        job_id = job_id
    )
    
    return jsonify(payload)
# Created and works
@artifacts.route("/job/sacct", methods=["GET"])
def get_job_sacct():
    sent_payload = json.loads(request.json)

    job_id = sent_payload['job-id']

    payload = fetch_job_sacct(
        file_lock = current_app.file_lock,
        allas_client = current_app.allas_client,
        allas_bucket = current_app.allas_bucket,
        kubeflow_user = current_app.kubeflow_user,
        job_id = job_id
    )
    
    return jsonify(payload)
# Created and works
@artifacts.route("/job/logs", methods=["GET"])
def get_job_logs():
    sent_payload = json.loads(request.json)

    job_id = sent_payload['job-id']

    payload = fetch_job_logs(
        file_lock = current_app.file_lock,
        allas_client = current_app.allas_client,
        allas_bucket = current_app.allas_bucket,
        kubeflow_user = current_app.kubeflow_user,
        job_id = job_id
    )
    
    return jsonify(payload)