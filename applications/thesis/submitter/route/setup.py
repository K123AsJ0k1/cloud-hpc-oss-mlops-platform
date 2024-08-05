from flask import Blueprint, current_app, request

import json

from functions.management.tasks import submitter, monitor
from functions.platforms.allas import setup_client
from functions.initilization import initilize_submitter_objects

setup = Blueprint('setup', __name__)

# Refactored and works
@setup.route("/setup", methods=["POST"])
def setup_configuration():
    sent_payload = json.loads(request.json)
    allas_parameters = sent_payload['allas-parameters']
    allas_bucket = allas_parameters['allas-bucket']
    kubeflow_user = sent_payload['kubeflow-user']
    remote_target = sent_payload['remote-target']
    allas_client = setup_client(
        parameters = allas_parameters
    )  
    current_app.allas_client = allas_client
    current_app.allas_bucket = allas_bucket
    current_app.kubeflow_user = kubeflow_user
    current_app.target = remote_target
    
    initilize_submitter_objects(
        file_lock = current_app.file_lock,
        allas_client = current_app.allas_client,
        allas_bucket = current_app.allas_bucket,
        kubeflow_user = kubeflow_user
    )

    return 'Ok', 200
# Refactored and works 
@setup.route("/start", methods=["POST"])
def start_scheduler():
    if current_app.scheduler.state == 0 and hasattr(current_app, 'allas_client'):
        given_args = [
            current_app.file_lock,
            current_app.logger,
            current_app.allas_client,
            current_app.allas_bucket,
            current_app.target,
            current_app.kubeflow_user
        ] 
        current_app.scheduler.add_job(
            func = submitter,
            trigger = "interval",
            seconds = 50,
            args = given_args 
        )
        
        given_args = [
            current_app.file_lock,
            current_app.logger,
            current_app.allas_client,
            current_app.allas_bucket,
            current_app.target,
            current_app.kubeflow_user
        ] 
        current_app.scheduler.add_job(
            func = monitor,
            trigger = "interval",
            seconds = 40,
            args = given_args 
        )

        current_app.scheduler.start()
        current_app.logger.info('Scheduler running')
    if current_app.scheduler.state == 2:
        current_app.scheduler.resume()
        current_app.logger.info('Scheduler resumed')
    return 'Ok', 200
# Created and works
@setup.route("/stop", methods=["POST"])
def stop_scheduler():
    if current_app.scheduler.state == 1:
        current_app.scheduler.pause()
        current_app.logger.info('Scheduler stopped')
    return 'Ok', 200