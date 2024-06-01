train_transform = T.Compose([
    T.ToTensor(),
    T.Normalize((0.5,), (0.5,))
])

test_transform = T.Compose([
    T.ToTensor(),
    T.Normalize((0.5,), (0.5,))
])

train_data = datasets.FashionMNIST(
    root = './data', 
    train = True, 
    download = True, 
    transform = train_transform
)

test_data = datasets.FashionMNIST(
    root = './data', 
    train = False, 
    download = True, 
    transform = test_transform
)

first_columnsXrows_images(
    dataset = train_data,
    labels = image_labels,
    columns = 3,
    rows = 3
)

first_columnsXrows_images(
    dataset = test_data,
    labels = image_labels,
    columns = 3,
    rows = 3
)

train_batch_size = 4
test_batch_size = 4

train_loader = torch.utils.data.DataLoader(
    train_data, 
    batch_size = train_batch_size, 
    shuffle = True
)

test_loader = torch.utils.data.DataLoader(
    test_data, 
    batch_size = test_batch_size, 
    shuffle = False
)