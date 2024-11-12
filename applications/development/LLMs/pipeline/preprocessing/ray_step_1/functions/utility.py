from math import ceil

def divide_list(
    target_list: any, 
    number: int
):
  size = ceil(len(target_list) / number)
  return list(
    map(lambda x: target_list[x * size:x * size + size],
    list(range(number)))
  )

def get_storage_prefix(
    repository_owner: str,
    repository_name: str
) -> str:
    return repository_owner + '|' + repository_name + '|'

def get_path_database_and_collection(
    repository_owner: str,
    repository_name: str,
    path: str
) -> str:
    path_split = path.split('/')
    database_name = get_storage_prefix(repository_owner, repository_name) + path_split[-1].split('.')[-1]
    collection_name = ''
    for word in path_split[:-1]:
        collection_name += word[:2] + '|'
    collection_name += path_split[-1].split('.')[0]
    return database_name, collection_name