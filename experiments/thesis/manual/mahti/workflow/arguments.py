input_parameters = {
    "pre_auth_url": str(_pre_auth_url),
    "pre_auth_token": str(given_token),
    "user_domain_name": str(_user_domain_name),
    "project_domain_name": str(_project_domain_name),
    "project_name": str(_project_name),
    'auth_version': str(_auth_version),
    'allas-bucket': allas_bucket,
    'run-name': 'local'
}
dumped_parameters = json.dumps(input_parameters)
print(dumped_parameters)

# run scripts/exp_train.py ''