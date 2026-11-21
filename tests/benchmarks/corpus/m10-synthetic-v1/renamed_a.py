def moving_score(values, weight):
    count = len(values)
    total = sum(values)
    average = total / count
    weighted = average * weight
    adjusted = weighted + count
    message = "score"
    output = {message: adjusted, "count": count}
    return output
