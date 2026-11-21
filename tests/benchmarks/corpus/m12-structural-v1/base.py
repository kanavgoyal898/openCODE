def calculate(values):
    count = len(values)
    total = sum(values)
    average = total / count
    adjusted = average * 2
    label = "summary"
    result = {label: adjusted, "count": count}
    return result
