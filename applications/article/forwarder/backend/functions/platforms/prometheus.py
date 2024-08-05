import os
import shutil
from prometheus_client import CollectorRegistry, Gauge, multiprocess, start_http_server
# Created and works
def get_prometheus_registry():
    return CollectorRegistry()
# Created and works
def set_prometheus_gauge(
    prometheus_registry: any,
    gauge_structure: any
) -> any:
    gauge = Gauge(
        name = gauge_structure['name'],
        documentation = gauge_structure['docs'],
        labelnames = gauge_structure['labels'],
        registry = prometheus_registry
    )
    return gauge
# Created and works
def create_prometheus_server():
    # This works, but each time that the backend is restarted
    # the gauge db is recreated
    # This means that the metrics can be recollected
    # which is why the set prometheus directory should be 
    # cleaned at restart 

    prometheus_directory = os.path.abspath('prometheus')
    os.environ['PROMETHEUS_MULTIPROC_DIR'] = prometheus_directory

    if os.path.exists(prometheus_directory):
        shutil.rmtree(prometheus_directory)

    os.makedirs(prometheus_directory, exist_ok=True)
    
    wanted_port = int(os.environ.get('PROMETHEUS_PORT'))
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    start_http_server(
        port = wanted_port, 
        registry = registry
    ) 