def sizeof_fmt(num, suffix="B", radix=1024.0, radix_suffix="i"):
    for unit in [""] + list(map(lambda item: item + radix_suffix, ["K", "M", "G", "T", "P", "E", "Z"])):
        if abs(num) < radix:
            return f"{num:3.1f}{unit}{suffix}"
        num /= radix
    return f'{num:.1f}{"Y" + radix_suffix}{suffix}'
