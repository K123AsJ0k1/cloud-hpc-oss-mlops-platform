from math import ceil

from functions.minio_os import minio_check_object, minio_get_object_data_and_metadata, minio_create_or_update_object

def divide_list(
    target_list: any, 
    number: int
):
  size = ceil(len(target_list) / number)
  return list(
    map(lambda x: target_list[x * size:x * size + size],
    list(range(number)))
  )

def get_github_storage_prefix(
    repository_owner: str,
    repository_name: str
) -> str:
    return repository_owner + '|' + repository_name + '|'

def get_checked_documents(
    object_client: any,
    configuration: any,
    prefix: str
):
    used_object_bucket = configuration['object-bucket']
    used_object_path = configuration['object-path'] + '-' + prefix
    
    object_exists = minio_check_object(
        minio_client = object_client,
        bucket_name = used_object_bucket, 
        object_path = used_object_path
    )

    ids = []
    if object_exists:
        ids = minio_get_object_data_and_metadata(
            minio_client = object_client,
            bucket_name = used_object_bucket, 
            object_path = used_object_path
        )['data']
        
    return ids

def store_checked_documents(
    object_client: any,
    configuration: any,
    prefix: str,
    checked_documents: any
):
    used_object_bucket = configuration['object-bucket']
    used_object_path = configuration['object-path'] + '-' + prefix
    
    minio_create_or_update_object(
        minio_client = object_client,
        bucket_name = used_object_bucket, 
        object_path = used_object_path,
        data = checked_documents, 
        metadata = {}
    )