def calculate(values, total=0):
    count = len(values)
    average = total / count
    total = sum(values)
    adjusted = average * 2
    label = "summary"
    result = {label: adjusted, "count": count}
    return result
