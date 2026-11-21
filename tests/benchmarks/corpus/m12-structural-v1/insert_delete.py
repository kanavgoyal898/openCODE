def calculate(items):
    count = len(items)
    total = sum(items)
    average = total / count
    adjusted = average * 2
    adjusted = adjusted + 1
    result = {"summary": adjusted, "count": count}
    return result
