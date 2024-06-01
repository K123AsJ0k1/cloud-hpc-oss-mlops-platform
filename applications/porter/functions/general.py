from flask import current_app
from typing import Dict
from datetime import timedelta

# Complete and works
def sub_index_to_int(
    sent_data: Dict[str, Dict[str,int]]
) -> Dict[str, Dict[int,int]]: 
    # This function makes string keys of subdicts 
    # into integers in received json payloads 
    current_app.logger.info('Fixing the format of json dict payload')
    updated_dict = {}
    for column in sent_data.keys():
        updated_sub_dict = {}
        for index, value in sent_data[column].items():
            updated_sub_dict[int(index)] = value
        updated_dict[column] = updated_sub_dict
    return updated_dict
# Created and works
def format_metadata_dict(
    given_metadata: dict
) -> dict:
    # MinIO metadata is first characeter capitalized 
    # and their values are strings due to AMZ format, 
    # which is why the key strings must be made lower
    # and their stirng integers need to be changed to integers 
    current_app.logger.info('Fixing the format of given MinIO metadata')
    fixed_dict = {}
    for key, value in given_metadata.items():
        if value.replace('.','',1).isdigit():
            fixed_dict[key.lower()] = int(value)
        else: 
            fixed_dict[key.lower()] = value
    fixed_dict = decode_metadata_strings_to_lists(fixed_dict)
    return fixed_dict
# Created and works
def encode_metadata_lists_to_strings(
    given_metadata: dict
) -> dict:
    # MinIO metadata only accepts strings and integers, 
    # that have keys without _ characters
    # which is why saving lists in metadata requires
    # making them strings
    modified_dict = {}
    for key,value in given_metadata.items():
        if isinstance(value, list):
            modified_dict[key] = 'list=' + ','.join(map(str, value))
            continue
        modified_dict[key] = value
    return modified_dict 
# Created and works
def decode_metadata_strings_to_lists(
    given_metadata: dict
) -> dict:
    modified_dict = {}
    for key, value in given_metadata.items():
        if isinstance(value, str):
            if 'list=' in value:
                string_integers = value.split('=')[1]
                values = string_integers.split(',')
                if len(values) == 1 and values[0] == '':
                    modified_dict[key] = []
                else:
                    try:
                        modified_dict[key] = list(map(int, values))
                    except:
                        modified_dict[key] = list(map(str, values))
                continue
        modified_dict[key] = value
    return modified_dict
# Created
def get_porter_logs():
    logs_path = 'logs/porter.log'
    listed_logs = {'porter-logs':[]}
    with open(logs_path, 'r') as f:
        for line in f:
            listed_logs['porter-logs'].append(line.strip())
    return listed_logs
# Created and works
def unit_converter(
    value: str,
    bytes: bool
) -> any:
    units = {
        'K': {
            'normal': 1000,
            'bytes': 1024
        },
        'M': {
            'normal': 1000**2,
            'bytes': 1024**2
        },
        'G': {
            'normal': 1000**3,
            'bytes': 1024**3
        },
        'T': {
            'normal': 1000**4,
            'bytes': 1024**4
        },
        'P': {
            'normal': 1000**5,
            'bytes': 1024**5
        }
    }
    
    converted_value = 0
    unit_letter = ''

    character_index = 0
    for character in value:
        if character.isalpha():
            unit_letter = character
            break
        character_index += 1
    
    if 0 < len(unit_letter):
        if not bytes:
            converted_value = int(float(value[:character_index]) * units[unit_letter]['normal'])
        else:
            converted_value = int(float(value[:character_index]) * units[unit_letter]['bytes'])
    else:
        converted_value = value
    return converted_value
# Created and works
def convert_into_seconds(
    given_time: str
) -> int:
    days = 0
    hours = 0
    minutes = 0
    seconds = 0
    milliseconds = 0

    day_split = given_time.split('-')
    if '-' in given_time:
        days = int(day_split[0])

    millisecond_split = day_split[-1].split('.')
    if '.' in given_time:
        milliseconds = int(millisecond_split[1])
    
    hour_minute_second_split = millisecond_split[0].split(':')

    if len(hour_minute_second_split) == 3:
        hours = int(hour_minute_second_split[0])
        minutes = int(hour_minute_second_split[1])
        seconds = int(hour_minute_second_split[2])
    else:
        minutes = int(hour_minute_second_split[0])
        seconds = int(hour_minute_second_split[1])
    
    result = timedelta(
        days = days,
        hours = hours,
        minutes = minutes,
        seconds = seconds,
        milliseconds = milliseconds
    ).total_seconds()
    return result