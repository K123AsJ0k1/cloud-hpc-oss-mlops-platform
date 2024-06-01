from flask import Blueprint, jsonify, current_app

from prometheus_client import generate_latest

from functions.general import get_porter_logs
from functions.platforms.kubernetes import get_cluster_structure

general = Blueprint('general', __name__)

@general.route('/demo', methods=["GET"]) 
def demo():
    return 'Ok', 200

@general.route('/metrics') 
def metrics():
    return generate_latest(current_app.prometheus_registry)
# Complete and works
@general.route('/structure', methods=["GET"]) 
def cluster_structure():
    structure = get_cluster_structure()
    return jsonify(structure) 
# Created
@general.route('/logs', methods=["GET"]) 
def porter_logs():
    payload = get_porter_logs()
    return jsonify(payload)