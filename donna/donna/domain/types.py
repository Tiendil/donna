from typing import Callable, NewType


# Ids that are lowercase ASCII without spaces

Slug = NewType("Slug", str)

OperationResultId = NewType("OperationResultId", Slug)


def slug_parser(text: str) -> Slug:
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789-_"

    if not all(c in allowed_chars for c in text):
        raise ValueError(f"Invalid slug '{text}'. Allowed characters are: {allowed_chars}")

    return Slug(text)


def child_slug_parser[T: Slug](type_id: Callable[[Slug], T]) -> Callable[[str], T]:
    def parser(text: str) -> T:
        return type_id(slug_parser(text))

    return parser
