# 8-4-2

from ..compose.utility import start_compose, stop_compose
from ...utility.requests.utility import request_route
# Created
def start_submitter(
    file_paths: any,
    address: str,
    port: str,
    configuration: any
) -> bool:
    
    deployed = start_compose(
        file_path = file_paths[0]
    )

    if deployed:
        route_code, route_text  = request_route(
            address = address,
            port = port,
            route_type = '',
            route_name = 'setup',
            path_replacers = {},
            path_names = [],
            route_input = configuration,
            timeout = 120
        )

        if route_code == 200 and route_text:
            deployed = start_compose(
                file_path = file_paths[1]
            )

    return deployed    