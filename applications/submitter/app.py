from flask import Flask

import threading

from apscheduler.schedulers.background import BackgroundScheduler

import os
import logging

def create_app():
    app = Flask(__name__)

    app.file_lock = threading.Lock()
    
    os.makedirs('logs', exist_ok=True)
    os.makedirs('artifacts', exist_ok=True)

    submitter_log_path = 'logs/submitter.log'
    if os.path.exists(submitter_log_path):
        os.remove(submitter_log_path)

    logger = logging.getLogger('submitter-logger')
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(submitter_log_path)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    app.logger = logger

    app.scheduler = BackgroundScheduler(daemon = True)
    
    from route.general import general
    from route.setup import setup
    from route.submit import submit
    from route.cancel import cancel
    from route.artifacts import artifacts

    app.register_blueprint(general)
    app.register_blueprint(setup)
    app.register_blueprint(submit)
    app.register_blueprint(cancel)
    app.register_blueprint(artifacts)
    
    app.logger.info('Routes registered')
    
    app.logger.info('Submitter ready')
    return app