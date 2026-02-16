from donna.protocol.cells import Cell, MetaValue


def operation_succeeded(message: str, **meta: MetaValue) -> Cell:
    return Cell.build(kind="operation_succeeded", media_type="text/markdown", content=message, **meta)


def operation_failed(message: str, **meta: MetaValue) -> Cell:
    return Cell.build(kind="operation_failed", media_type="text/markdown", content=message, **meta)


def info(message: str, **meta: MetaValue) -> Cell:
    return Cell.build(kind="info", media_type="text/markdown", content=message, **meta)
