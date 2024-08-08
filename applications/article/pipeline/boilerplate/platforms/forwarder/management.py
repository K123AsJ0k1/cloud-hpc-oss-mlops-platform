# Created
def start_forwarder(
    address: str,
    port: str,
    configuration: any,
    scheduler_request: any
) -> bool:
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
    configured = False
    if route_code == 200 and route_text:
        route_code, route_text  = request_route(
            address = address,
            port = port,
            route_type = '',
            route_name = 'start',
            path_replacers = {},
            path_names = [],
            route_input = scheduler_request,
            timeout = 120
        )

        if route_code == 200 and route_text:
            configured == True
    return configured