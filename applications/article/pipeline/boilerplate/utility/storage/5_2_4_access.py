from decouple import Config,RepositoryEnv
from keystoneauth1 import loading, session

def get_storage_parameters(
    env_path: str,
    auth_url: str,
    pre_auth_url: str,
    auth_version: str,
    bucket_prefix: str,
    ice_id: str,
    user: str
):
    env_config = Config(RepositoryEnv(env_path))
    swift_auth_url = auth_url
    swift_user = env_config.get('CSC_USERNAME')
    swift_key = env_config.get('CSC_PASSWORD')
    swift_project_name = env_config.get('CSC_PROJECT_NAME')
    swift_user_domain_name = env_config.get('CSC_USER_DOMAIN_NAME')
    swift_project_domain_name = env_config.get('CSC_USER_DOMAIN_NAME')

    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(
        auth_url = swift_auth_url,
        username = swift_user,
        password = swift_key,
        project_name = swift_project_name,
        user_domain_name = swift_user_domain_name,
        project_domain_name = swift_project_domain_name
    )

    keystone_session = session.Session(
        auth = auth
    )
    swift_token = keystone_session.get_token()

    swift_pre_auth_url = pre_auth_url
    swift_auth_version = auth_version

    storage_parameters = {
        'bucket-prefix': bucket_prefix,
        'ice-id': ice_id,
        'user': user,
        'used-client': 'swift',
        'pre-auth-url': str(swift_pre_auth_url),
        'pre-auth-token': str(swift_token),
        'user-domain-name': str(swift_user_domain_name),
        'project-domain-name': str(swift_project_domain_name),
        'project-name': str(swift_project_name),
        'auth-version': str(swift_auth_version)
    }

    return storage_parameters