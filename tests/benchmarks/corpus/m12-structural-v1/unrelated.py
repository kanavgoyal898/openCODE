def emit_message(name):
    if not name:
        return None
    for character in name:
        print(character)
    return name.upper()
