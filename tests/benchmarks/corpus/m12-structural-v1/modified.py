def calculate(items):
    count = len(items)
    total = sum(items)
    average = total / count
    adjusted = average * count
    label = "result"
    result = {label: adjusted, "count": count}
    return result
