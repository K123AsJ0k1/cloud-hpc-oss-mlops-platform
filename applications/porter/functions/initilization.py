from functions.platforms.prometheus import sacct_gauge, seff_gauge, time_gauge
from functions.management.objects import get_objects, set_objects
# Created and works
def monitor_status_template():
    monitor_status = {
        'bridge-times': {},
        'porter-times': {},
        'submitter-metrics': {},
        'submitter-times': {}
    } 
    return monitor_status
# Created
def porter_status_template():
    porter_status = {}
    return porter_status
# Created and works
def initilize_porter_objects(
    file_lock: any,
    allas_client: any,
    allas_bucket: any
):
    # Check user path concurrency
    objects = {
        'monitor-status': {
            'path': 'monitor-status',
            'replacers': {},
            'template': monitor_status_template()
        },
        'porter-status': {
            'path': 'porter-status',
            'replacers': {},
            'template': porter_status_template()
        }
    }

    for object in objects.keys():
        path = objects[object]['path']
        replacers = objects[object]['replacers']
        template = objects[object]['template']

        data = get_objects(
            file_lock = file_lock,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            object = path,
            replacers = replacers
        )

        perform = False
        if data is None:
            data = template
            perform = True
        
        if perform:
            set_objects(
                file_lock = file_lock,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                object = path,
                replacers = replacers,
                overwrite = True,
                object_data = data  
            )
# Refactored and works
def initilize_prometheus_gauges(
    prometheus_registry: any,
    prometheus_metrics: any,
):
    seff, seff_names = seff_gauge(
        prometheus_registry = prometheus_registry
    )
    prometheus_metrics['seff'] = seff
    prometheus_metrics['seff-name'] = seff_names
    sacct, sacct_names = sacct_gauge(
        prometheus_registry = prometheus_registry
    )
    prometheus_metrics['sacct'] = sacct
    prometheus_metrics['sacct-name'] = sacct_names
    time, time_names = time_gauge(
        prometheus_registry = prometheus_registry
    )
    prometheus_metrics['time'] = time
    prometheus_metrics['time-name'] = time_names