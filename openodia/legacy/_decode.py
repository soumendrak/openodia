def decode(data: bytes) -> str:
    """Decode legacy font bytes into keystroke characters.

    Defined bytes use cp1252. The five bytes that codec leaves undefined,
    0x81, 0x8D, 0x8F, 0x90 and 0x9D, stay as those code points.

    Raises:
        TypeError: ``data`` is not ``bytes`` or ``bytearray``.
    """
    if not isinstance(data, bytes | bytearray):
        raise TypeError("legacy font bytes are required")
    chars: list[str] = []
    for byte in data:
        try:
            chars.append(bytes((byte,)).decode("cp1252"))
        except UnicodeDecodeError:
            chars.append(chr(byte))
    return "".join(chars)
