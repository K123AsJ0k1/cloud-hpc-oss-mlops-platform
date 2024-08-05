import torch
import matplotlib.pyplot as plt

def first_columnsXrows_images(
    dataset: any,
    labels: any,
    columns: int,
    rows: int
):
    figure = plt.figure(figsize = (10,10))
    for i in range (1, columns * rows + 1):
        image, label = dataset[i]
        figure.add_subplot(
            rows, 
            columns, 
            i
        )
        plt.title(labels[label])
        plt.axis('off')
        plt.imshow(
            image.squeeze(), 
            cmap = 'gray'
        )
    plt.show()

def class_amounts(
    dataset: any,
    labels: any
):
    class_amounts = torch.bincount(dataset.targets)
    print('Class, amount:')
    for i in range(len(labels)):
        print(labels[i], class_amounts[i].item())
