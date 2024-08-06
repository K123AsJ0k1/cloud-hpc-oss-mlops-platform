import subprocess

# created
def start_compose(
    file_path: str
) -> bool:
    compose_up_command = 'docker compose -f (file) up -d'
    modified_up_command = compose_up_command.replace('(file)', file_path)
    
    resulted_print = subprocess.run(
        modified_up_command,
        shell = True,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    print_split = resulted_print.stderr.decode('utf-8').split('\n')
    deployed = False
    if 'started' in print_split:
        deployed = True
    return deployed
# created
def stop_compose(
    file_path: str
) -> bool:
    compose_down_command = 'docker compose -f (file) down'
    modified_down_command = compose_down_command.replace('(file)', file_path)
    
    resulted_print = subprocess.run(
        modified_down_command,
        shell = True,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    print_split = resulted_print.stderr.decode('utf-8').split('\n')
    removed = False
    if 'started' in print_split:
        removed = True
    return removed
