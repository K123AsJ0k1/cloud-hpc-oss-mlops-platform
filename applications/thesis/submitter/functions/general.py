import json
from datetime import timedelta

# Created and works
def get_submitter_logs():
    logs_path = 'logs/submitter.log'
    listed_logs = {'submitter-logs':[]}
    with open(logs_path, 'r') as f:
        for line in f:
            listed_logs['submitter-logs'].append(line.strip())
    return listed_logs
# Created and works
def get_docker_compose_secrets():
    with open('/run/secrets/metadata', 'r') as f:
        secret_metadata = json.load(f)
    return secret_metadata
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