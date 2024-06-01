from flask import Blueprint, jsonify, current_app

general = Blueprint('general', __name__)

from functions.general import get_submitter_logs

@general.route('/demo', methods=["GET"]) 
def demo():
    return 'Ok', 200
# Created
@general.route('/logs', methods=["GET"]) 
def submitter_logs():
    payload = get_submitter_logs()
    return jsonify(payload)