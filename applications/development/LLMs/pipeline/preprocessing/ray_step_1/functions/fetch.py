
from functions.minio_os import minio_check_object, minio_create_or_update_object, minio_get_object_data_and_metadata
from functions.pygithub import pygithub_get_repo_paths

def fetch_repository_paths(
    object_client: any,
    github_token: str,
    repository_owner: str,
    repository_name: str,
    object_bucket: str,
    repo_paths_object: str,
    relevant_files: any,
    replace: bool
) -> any:
    print('Fetching paths')

    object_exists = minio_check_object(
        minio_client = object_client,
        bucket_name = object_bucket, 
        object_path = repo_paths_object
    )
 
    repo_paths = []
    if replace == 'true' or not object_exists:
        print('Getting github paths')

        repo_paths = pygithub_get_repo_paths(
            token = github_token,
            owner = repository_owner, 
            name = repository_name
        )

        print('Storing paths')

        minio_create_or_update_object(
            minio_client = object_client,
            bucket_name = object_bucket, 
            object_path = repo_paths_object,
            data = repo_paths, 
            metadata = {}
        )

        print('Paths stored')
    else:
        print('Getting stored paths')
        repo_paths = minio_get_object_data_and_metadata(
            minio_client = object_client,
            bucket_name = object_bucket, 
            object_path = repo_paths_object
        )['data']

    print('Filtering paths')
    relevant_paths = []
    for path in repo_paths:
        path_split = path.split('/')
        file_end = path_split[-1].split('.')[-1].rstrip()
        if file_end in relevant_files:
            relevant_paths.append(path.rstrip())
    print('Paths filtered')

    return relevant_paths
