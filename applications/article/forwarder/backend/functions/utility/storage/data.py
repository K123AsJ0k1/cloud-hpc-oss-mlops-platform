# Communication object = High writes and reads with small size
# Artifact object = Low append only writes with occational reads with large size

# Created
def forwarding_status_communication_object_data():
    # Per job, so not key cumulative due to conditions
    forwarding_status_data = {
        'created': False,
        'cancel': False,
        'deleted': False,
        'connections': [],
        'services': []
    }
    return forwarding_status_data
# Created
def collection_index_communication_object():
    # Per generator source, so list cumulative
    collection_index_data = {
        'keys': []
    }
    return collection_index_data
#
def collected_time_data():
    # Per group
    # Might need refactoring later
    collected_time = {
        'id': {
            'name': '',
            'begin-time': 0,
            'end-time': 0,
            'total-seconds': 0 
        }
    }
    return 


