def parse_list(s: str, delim: str) -> list[str]:
    return list(filter(None, map(lambda t: t.strip(), s.split(delim))))
