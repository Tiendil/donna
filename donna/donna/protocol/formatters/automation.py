import json

from donna.protocol.cells import Cell


class Formatter:

    def format_cell(self, cell: Cell) -> bytes:
        data = {'id': cell.short_id()}

        for meta_key, meta_value in sorted(cell.meta.items()):
            data[meta_key] = meta_value

        data['content'] = cell.content.strip()

        return json.dumps(data, ensure_ascii=False, indent=None, separators=(',', ':'), sort_keys=True).encode()

    def format_cells(self, cells: list[Cell]) -> bytes:
        formatted_cells = [self.format_cell(cell) for cell in cells]
        return "\n".join(formatted_cells).encode()
