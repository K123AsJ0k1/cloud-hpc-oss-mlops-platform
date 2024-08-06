# 6-3-1

import requests
import json
import time
# Created and works
def set_route(
    route_type: str,
    route_name: str,
    path_replacers: any,
    path_names: any
): 
    routes = {
        'root': 'TYPE:/name',
        'logs': 'GET:/general/logs/name',
        'structure': 'GET:/general/structure',
        'setup': 'POST:/setup/config',
        'start': 'POST:/setup/start',
        'stop': 'POST:/setup/stop',
        'job-submit': 'POST:/requests/submit/job',
        'job-run': 'PUT:/requests/run/job/user/key',
        'job-cancel': 'PUT:/requests/cancel/job/user/key',
        'forwarding-submit': 'POST:/requests/submit/forwarding',
        'forwarding-cancel': 'PUT:/requests/cancel/type/user/key',
        'task-request': 'PUT:/tasks/request/signature',
        'task-result': 'GET:/tasks/result/id',
        'job-artifact': 'GET:/artifacts/job/type/name',
        'forwarding-artifact': 'GET:/artifacts/forwarding/type/user/key'
    }

    route = None
    if route_name in routes:
        i = 0
        route = routes[route_name].split('/')
        for name in route:
            if name in path_replacers:
                replacer = path_replacers[name]
                if 0 < len(replacer):
                    route[i] = replacer
            i = i + 1

        if not len(path_names) == 0:
            route.extend(path_names)

        if not len(route_type) == 0:
            route[0] = route_type + ':'
        
        route = '/'.join(route)
    print('Used route: ' + str(route))
    return route
# Created and works
def get_response(
    route_type: str,
    route_url: str,
    route_input: any
) -> any:
    route_response = None
    if route_type == 'POST':
        route_response = requests.post(
            url = route_url,
            json = route_input
        )
    if route_type == 'PUT':
        route_response = requests.put(
            url = route_url
        )
    if route_type == 'GET':
        route_response = requests.get(
            url = route_url
        )
    return route_response
# Created and works
def set_full_url(
    address: str,
    port: str,
    used_route: str
) -> str:
    url_prefix = 'http://' + address + ':' + port
    route_split = used_route.split(':')
    url_type = route_split[0]
    used_path = route_split[1]
    full_url = url_prefix + used_path
    return url_type, full_url
# Created and works
def request_route(
    address: str,
    port: str,
    route_type: str,
    route_name: str,
    path_replacers: any,
    path_names: any,
    route_input: any,
    timeout: any
) -> any:
    used_route = set_route(
        route_type = route_type,
        route_name = route_name,
        path_replacers = path_replacers,
        path_names = path_names
    )

    url_type, full_url = set_full_url(
        address = address,
        port = port,
        used_route = used_route
    )

    route_response = get_response(
        route_type = url_type,
        route_url = full_url,
        route_input = route_input
    )

    route_status_code = None
    route_returned_text = {}
    if not route_response is None:
        route_status_code = route_response.status_code
        if route_status_code == 200:
            route_text = json.loads(route_response.text)

            if 'id' in route_text: 
                task_result_route = set_route(
                    route_type = '',
                    route_name = 'task-result',
                    path_replacers = {
                        'id': route_text['id']
                    },
                    path_names = []
                )

                task_url_type, task_full_url = set_full_url(
                    address = address,
                    port = port,
                    used_route = task_result_route
                )

                start = time.time()
                while time.time() - start <= timeout:
                    task_route_response = get_response(
                        route_type = task_url_type,
                        route_url = task_full_url,
                        route_input = {}
                    )
                    
                    task_status_code = route_response.status_code
                        
                    if task_status_code == 200:
                        task_text = json.loads(task_route_response.text)
    
                        if task_text['status'] == 'FAILED':
                            break
                        
                        if task_text['status'] == 'SUCCESS':
                            route_returned_text = task_text['result']
                            break
                    else:
                        break
            else:
                route_returned_text = route_text
    return route_status_code, route_returned_text
                    