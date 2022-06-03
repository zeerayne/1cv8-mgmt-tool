def sizeof_fmt(num, suffix='B', radix=1024.0):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < radix:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= radix
    return "%.1f%s%s" % (num, 'Yi', suffix)
