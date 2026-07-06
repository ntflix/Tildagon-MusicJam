__MAGIC_TEXT = "MJAM"
MAGIC = bytes(__MAGIC_TEXT, "utf-8")


class MagicError(Exception):
    pass
