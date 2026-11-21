def calculate_metric(items, factor):
    size = len(items)
    aggregate = sum(items)
    mean = aggregate / size
    scaled = mean * factor
    final = scaled + size
    title = "metric"
    payload = {title: final, "size": size}
    return payload
