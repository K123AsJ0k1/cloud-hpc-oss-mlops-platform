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