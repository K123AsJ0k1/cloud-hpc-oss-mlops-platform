from functions.matplotlib import first_columnsXrows_images,class_amounts

from torchvision import datasets
import torchvision.transforms as T

image_labels = {
    0: 'Top',
    1: 'Trouser',
    2: 'Pullover',
    3: 'Dress',
    4: 'Coat',
    5: 'Sandal',
    6: 'Shirt',
    7: 'Sneaker',
    8: 'Bag',
    9: 'Ankle Boot',
}

regular_transform = T.Compose([
    T.ToTensor()
])

source_train_data = datasets.FashionMNIST(
    root = './data', 
    train = True, 
    download = True, 
    transform = regular_transform
)

source_test_data = datasets.FashionMNIST(
    root = './data', 
    train = False, 
    download = True, 
    transform = regular_transform
)

first_columnsXrows_images(
    dataset = source_train_data,
    labels = image_labels,
    columns = 3,
    rows = 3
)
print('Train set has {} instances'.format(len(source_train_data)))
class_amounts(
    dataset = source_train_data,
    labels = image_labels
)

first_columnsXrows_images(
    dataset = source_test_data,
    labels = image_labels,
    columns = 3,
    rows = 3
)
print('Test set has {} instances'.format(len(source_test_data)))
class_amounts(
    dataset = source_test_data,
    labels = image_labels
)