import uuid
from typing import List

import typer

from donna.cli.application import app
from donna.cli.utils import output_cells, template_is_not_allowed
from donna.domain.types import RecordId, RecordKindId, StoryId
from donna.machine import records as r_domain
from donna.world.primitives_register import register

records_cli = typer.Typer()


@records_cli.command()
def list(story_id: str) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))
    output_cells(index.cells())


@records_cli.command()
def create(story_id: str, record_id_template: str, description: str) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))

    record_id = RecordId(record_id_template.format(uid=uuid.uuid4().hex))

    index.create_record(
        id=record_id,
        description=description,
    )

    index.save()

    typer.echo(f'record "{record_id}" created')


@records_cli.command()
def delete(story_id: str, record_id: str) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))

    template_is_not_allowed("record_id", record_id)

    record_id_value = RecordId(record_id)

    index.delete_record(record_id_value)

    index.save()

    typer.echo(f"record '{record_id}' deleted from story '{story_id}'")


@records_cli.command()
def kind_set(
    story_id: str,
    record_id: str,
    record_kind: str,
    item: str,
) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))

    template_is_not_allowed("record_id", record_id)

    record_kind_id = RecordKindId(record_kind)
    record_id_value = RecordId(record_id)

    if not index.has_record(record_id_value):
        raise NotImplementedError(f"Record '{record_id}' does not exist in story '{story_id}'")

    kind = register().records.get(record_kind_id)

    index.set_record_kind_item(
        record_id=record_id_value,
        record_item=kind.item_class.from_json(item),
    )

    index.save()

    typer.echo(f"Set kind '{record_kind}' for record '{record_id}' in story '{story_id}'")


@records_cli.command()
def kind_delete(
    story_id: str,
    record_id: str,
    record_kinds: List[str],
) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))

    template_is_not_allowed("record_id", record_id)

    record_id_value = RecordId(record_id)

    index.remove_record_kind_items(record_id_value, [RecordKindId(kind) for kind in record_kinds])

    index.save()

    typer.echo(f"Removed kinds '{', '.join(record_kinds)}' from record '{record_id}' in story '{story_id}'")


@records_cli.command()
def kind_get(
    story_id: str,
    record_id: str,
    record_kinds: List[str],
) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))

    template_is_not_allowed("record_id", record_id)

    record_id_value = RecordId(record_id)
    record = index.get_record(record_id_value)

    if record is None:
        raise NotImplementedError(f"Record '{record_id}' does not exist in story '{story_id}'")

    record_kind_items = index.get_record_kind_items(record_id_value, [RecordKindId(kind) for kind in record_kinds])

    for record_kind_item in record_kind_items:
        if record_kind_item is None:
            continue
        output_cells(record_kind_item.cells(record))


app.add_typer(records_cli, name="records", help="Manage records")
