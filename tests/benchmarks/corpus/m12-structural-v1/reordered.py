def calculate(values):
    total = sum(values)
    count = len(values)
    average = total / count
    adjusted = average * 2
    label = "summary"
    result = {label: adjusted, "count": count}
    return result
