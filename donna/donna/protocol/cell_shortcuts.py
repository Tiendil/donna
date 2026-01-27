from donna.protocol.cells import Cell, MetaValue


def operation_succeeded(message: str, **meta: MetaValue) -> Cell:
    return Cell.build(kind="operation_succeeded", media_type="text/markdown", content=message, **meta)
