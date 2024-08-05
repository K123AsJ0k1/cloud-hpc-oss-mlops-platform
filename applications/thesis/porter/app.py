from flask import Flask

import os
import logging
import threading

from kubernetes import client, config
from prometheus_client import CollectorRegistry

from apscheduler.schedulers.background import BackgroundScheduler

def create_app():
    app = Flask(__name__)

    app.file_lock = threading.Lock()

    os.makedirs('logs', exist_ok=True)

    porter_log_path = 'logs/porter.log'
    if os.path.exists(porter_log_path):
        os.remove(porter_log_path)

    logger = logging.getLogger('porter-logger')
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(porter_log_path)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    app.logger = logger

    # Here we configure the kubernetes client and required APIs 
    # by checking kube config (Usual works outside the cluster) 
    # and in cluster config options (Usually works inside the cluster),
    # which is used to configure the enviroment
    enviroment = 'PROD'
    try:
        config.load_kube_config()
        app.logger.info('Choosen kubernetes client config is kube config')
        enviroment = 'DEV'
    except Exception as e:
        app.logger.warning('Kube config error')
        app.logger.warning(e)
    try:
        config.load_incluster_config()
        app.logger.info('Choosen kubernetes client config is incluster config')
        enviroment = 'PROD'
    except Exception as e:
        app.logger.warning('Incluster config error')
        app.logger.warning(e)

    if enviroment == 'DEV':
        app.logger.info('Choosen enviroment is development')
    elif enviroment == 'PROD':
        app.logger.info('Choosen enviroment is production')
    
    app.regular_kubernetes_client = client.CoreV1Api()
    app.custom_kubernetes_client = client.CustomObjectsApi()
    app.kubernetes_delete_options = client.V1DeleteOptions()
    app.logger.info('Kubernetes client regular, custom and delete options ready')
    app.allas_client = None
    app.allas_bucket = None

    registry = CollectorRegistry()
    app.prometheus_registry = registry
    app.prometheus_metrics = {
        'seff': None,
        'seff-names': None,
        'sacct': None,
        'sacct-names': None,
        'time': None,
        'time-names': None
    }

    from functions.initilization import initilize_prometheus_gauges
    initilize_prometheus_gauges(
        prometheus_registry = app.prometheus_registry,
        prometheus_metrics = app.prometheus_metrics
    )

    app.scheduler = BackgroundScheduler(daemon = True)
    
    from route.general import general
    from route.setup import setup
    from route.submit import submit
    from route.cancel import cancel
    from route.artifacts import artifacts
    app.logger.info('Routes imported')

    app.register_blueprint(general)
    app.register_blueprint(setup)
    app.register_blueprint(submit)
    app.register_blueprint(cancel)
    app.register_blueprint(artifacts)
    app.logger.info('Routes registered')
    
    app.logger.info('Porter ready')
    return app