def gather_time(
    storage_client: any,
    storage_name: any,
    time_group: any,
    time_name: any,
    start_time: int,
    end_time: int
):
    time_object = get_object(
        storage_client = storage_client,
        bucket_name = storage_name,
        object_name = 'time',
        path_replacers = {
            'name': time_group
        },
        path_names = []
    )

    time_data = {}
    time_metadata = {} 
    if time_object is None:
        time_data = {}
        time_metadata = general_object_metadata()
    else:
        time_data = time_object['data']
        time_metadata = time_object['custom-meta']
    
    current_key_amount = len(time_data)
    current_key_full = False
    current_key = str(current_key_amount)
    if 0 < current_key_amount:
        time_object = time_data[current_key]
        if 0 < time_object['total-seconds']:
            current_key_full = True
    
    changed = False
    if 0 < end_time and 0 < current_key_amount and not current_key_full:
        stored_start_time = time_data[current_key]['start-time']
        time_diff = (end_time-stored_start_time)
        time_data[current_key]['end-time'] = end_time
        time_data[current_key]['total-seconds'] = round(time_diff,5)
        changed = True
    else:
        next_key_amount = len(time_data) + 1
        new_key = str(next_key_amount)
    
        if 0 < start_time and 0 == end_time:
            time_data[new_key] = {
                'name': time_name,
                'start-time': start_time,
                'end-time': 0,
                'total-seconds': 0
            }
            changed = True

        if 0 < start_time and 0 < end_time:
            time_diff = (end_time-start_time)
            time_data[new_key] = {
                'name': time_name,
                'start-time': start_time,
                'end-time': end_time,
                'total-seconds': round(time_diff,5)
            }
            changed = True

    if changed:
        time_metadata['version'] = time_metadata['version'] + 1
        set_object(
            storage_client = storage_client,
            bucket_name = storage_name,
            object_name = 'time',
            path_replacers = {
                'name': time_group
            },
            path_names = [],
            overwrite = True,
            object_data = time_data,
            object_metadata = time_metadata 
        )