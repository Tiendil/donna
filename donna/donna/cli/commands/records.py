from typing import List

import typer

from donna.cli.application import app
from donna.cli.types import RecordIdArgument, StoryIdArgument
from donna.cli.utils import output_cells
from donna.domain import types
from donna.domain.ids import next_id
from donna.domain.types import RecordId, RecordKindId, StoryId
from donna.machine import records as r_domain
from donna.world.primitives_register import register

records_cli = typer.Typer()


@records_cli.command()
def list(story_id: StoryIdArgument) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))
    output_cells(index.cells())


@records_cli.command()
def create(story_id: StoryIdArgument, description: str) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))

    record_id = next_id(StoryId(story_id), RecordId)

    index.create_record(
        id=record_id,
        description=description,
    )

    index.save()

    typer.echo(f'record "{record_id}" created')


@records_cli.command()
def delete(story_id: StoryIdArgument, record_id: RecordIdArgument) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))

    index.delete_record(record_id)

    index.save()

    typer.echo(f"record '{record_id}' deleted from story '{story_id}'")


@records_cli.command()
def kind_set(
    story_id: StoryIdArgument,
    record_id: RecordIdArgument,
    record_kind: str,
    item: str,
) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))

    record_kind_id = RecordKindId(types.slug_parser(record_kind))

    if not index.has_record(record_id):
        raise NotImplementedError(f"Record '{record_id}' does not exist in story '{story_id}'")

    kind = register().records.get(record_kind_id)
    if kind is None:
        raise NotImplementedError(f"Record kind '{record_kind}' is not registered")

    index.set_record_kind_item(
        record_id=record_id,
        record_item=kind.item_class.from_json(item),
    )

    index.save()

    typer.echo(f"Set kind '{record_kind}' for record '{record_id}' in story '{story_id}'")


@records_cli.command()
def kind_delete(
    story_id: StoryIdArgument,
    record_id: RecordIdArgument,
    record_kinds: List[str],
) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))

    index.remove_record_kind_items(
        record_id,
        [RecordKindId(types.slug_parser(kind)) for kind in record_kinds],
    )

    index.save()

    typer.echo(f"Removed kinds '{', '.join(record_kinds)}' from record '{record_id}' in story '{story_id}'")


@records_cli.command()
def kind_get(
    story_id: StoryIdArgument,
    record_id: RecordIdArgument,
    record_kinds: List[str],
) -> None:
    index = r_domain.RecordsIndex.load(StoryId(story_id))

    record = index.get_record(record_id)

    if record is None:
        raise NotImplementedError(f"Record '{record_id}' does not exist in story '{story_id}'")

    record_kind_items = index.get_record_kind_items(
        record_id,
        [RecordKindId(types.slug_parser(kind)) for kind in record_kinds],
    )

    for record_kind_item in record_kind_items:
        if record_kind_item is None:
            continue
        output_cells(record_kind_item.cells(record))


app.add_typer(records_cli, name="records", help="Manage records")
