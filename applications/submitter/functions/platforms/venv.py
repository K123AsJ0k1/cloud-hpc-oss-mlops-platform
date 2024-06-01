
import time
import re

from functions.platforms.ssh import run_remote_commands,remote_folders_and_files

# Created and works
def check_python_version(
    logger: any,
    target:str
) -> any:
    version_print = run_remote_commands(
        logger = logger,
        target = target,
        commands = ['python3 -V']
    )
    formatted_version = version_print[0].split('\n')[:-1][0]
    if 'Python' in formatted_version:
        version = formatted_version.split(' ')[1]
        return version
    return None
# Created and works
def check_venv(
    logger: any,
    target: str,
    name: str
) -> bool:
    folders, _ = remote_folders_and_files(
        logger = logger,
        target = target
    )
    if not name in folders:
        return False
    return True
# Created and works
def list_venv_packages(
    logger: any,
    target: str,
    name: str
) -> bool:
    packages = {}
    command = 'source venv/bin/activate && pip list && deactivate'
    modified_command = command.replace('venv', name)
    
    package_list = run_remote_commands(
        logger = logger,
        target = target,
        commands = [
            modified_command
        ]
    )
    formatted_list = package_list[0].split('\n')[2:]
    # Doesn't work due to python-data chancing format
    for package in formatted_list:
        split = package.split(' ')
        package_name = split[0]
        version = split[-1]
        if not len(package_name) == 0:
            packages[package_name] = version
    return packages
# Created
def check_venv_packages(
    logger: any,
    target: str,
    name: str,
    wanted_packages: any
):
    installed_packages = list_venv_packages(
        logger = logger,
        target = target,
        name = name
    )
    wanted_state = True
    for package_info in wanted_packages:
        used_package_info = package_info
        if '-f' in used_package_info:
            used_package_info = used_package_info.replace(' ', '')
            used_package_info = used_package_info.split('-f')[0]
        if '"' in used_package_info:
            used_package_info = used_package_info.replace('"','')
        if '[' in package_info:    
            used_package_info = re.sub(r'\[.*\]', '', used_package_info)
        if '==' in used_package_info:
            info_split = used_package_info.split('==')
            formatted_name = info_split[0]
            formatted_version = info_split[1]
        else:
            formatted_name = used_package_info
            formatted_version = None
        
        if not formatted_name in installed_packages:
            logger.info(name + ' does not have ' + str(formatted_name))
            wanted_state = False
        else:
            if not formatted_version is None:
                if not installed_packages[formatted_name] == formatted_version:
                    logger.info(name + ' does not have ' + str(formatted_name) + ' of ' + str(formatted_version))
                    wanted_state = False
    return wanted_state
# Refactored and works
def create_venv(
    logger: any,
    target: str,
    name: str
) -> bool:
    venv_exists = check_venv(
        logger = logger,
        target = target,
        name = name
    )

    if venv_exists:
        return False
    
    # The first two commands are required to enable fabric use module commands
    # From these the module load python-data reduces the amount of venv files
    # Additionaly, most of the Ray packages are already in this module, which
    # makes installing even easier
    template_command = 'source /appl/profile/zz-csc-env.sh && module load pytorch && python3 -m venv --system-site-packages ' 
    command = 'venv && source venv/bin/activate && pip install --upgrade pip && deactivate'
    modified_command = command.replace('venv', name)
    creation_command = template_command + modified_command
    
    run_print = run_remote_commands(
        logger = logger,
        target = target,
        commands = [
            creation_command
        ]
    )

    # Maybe needs a better way to check
    if 'Successfully installed' in run_print[0]:
        return True

    return False
# Refactored and works
def install_packages(
    logger: any,
    target: str,
    name: str,
    packages: any
) -> bool:
    venv_exists = check_venv(
        logger = logger,
        target = target,
        name = name
    )

    if not venv_exists:
        return False

    # The first two commands are required to enable fabric use module commands
    # From these the module load python-data reduces the amount of venv files
    template_command = 'source /appl/profile/zz-csc-env.sh && module load pytorch && source venv/bin/activate && pip install '
    modified_command = template_command.replace('venv', name)
    #for package in packages:
    #    modified_command = modified_command + package + ' '
    #install_command = modified_command + '&& deactivate'
    
    install_separation = []
    line_packages = ''
    for package in packages:
        if '-f' in package:
            if 0 < len(line_packages):
                install_separation.append(line_packages)
                line_packages = ''
            install_separation.append(package + ' ')
            continue
        line_packages += package + ' '
    if 0 < len(line_packages):
        install_separation.append(line_packages)

    success = True
    for separation in install_separation:
        install_command = modified_command + separation + '&& deactivate'
        
        run_print = run_remote_commands(
            logger = logger,
            target = target,
            commands = [
                install_command
            ]
        )
        
        # Needs a better way to check
        if not 'Successfully installed' in run_print[0]:
            success = False
        time.sleep(5)
    return success