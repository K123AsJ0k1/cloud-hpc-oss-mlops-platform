def parse_torchmetrics(
    metrics: any,
    lables: any
):
    collected_metrics = {}
    for key,value in metrics.items():
        if key == 'name':
            continue
        if 'class-' in key:
            image_labels = {
                0: 'top',
                1: 'trouser',
                2: 'pullover',
                3: 'dress',
                4: 'coat',
                5: 'sandal',
                6: 'shirt',
                7: 'sneaker',
                8: 'bag',
                9: 'ankle-boot',
            }
            #logger.info('')
            i = 0
            for class_value in value:
                formatted_key = key.replace('class', lables[i])
                rounded_value = round(class_value,5)
                #logger.info(str(formatted_key) + '=' + str(rounded_value))
                collected_metrics[formatted_key] = rounded_value
                i += 1
            continue
        rounded_value = round(value,5)
        #logger.info(str(key) + '=' + str(rounded_value))
        collected_metrics[key] = rounded_value
    return collected_metrics