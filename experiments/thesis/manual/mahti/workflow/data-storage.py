train_loader_status = create_or_update_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = 'EXPERIMENT/DATA/train',
    data = train_loader
)
print(train_loader_status)

test_loader_status = create_or_update_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = 'EXPERIMENT/DATA/test',
    data = test_loader
)
print(test_loader_status)