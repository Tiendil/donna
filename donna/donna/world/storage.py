from typing import Generic, Iterable, Protocol, TypeVar, cast

ID = TypeVar("ID")
ITEM = TypeVar("ITEM")


class StorageItem(Protocol[ID]):
    id: ID


class Storage(Generic[ID, ITEM]):
    __slots__ = ("_items", "item_name")

    def __init__(self, item_name: str) -> None:
        self.item_name = item_name
        self._items: dict[ID, ITEM] = {}

    def add(self, item: ITEM) -> None:
        storage_item = cast(StorageItem[ID], item)
        if storage_item.id in self._items:
            raise NotImplementedError(f"{self.item_name} with id '{storage_item.id}' already exists")

        self._items[storage_item.id] = item

    def get(self, id: ID) -> ITEM:
        if id not in self._items:
            raise NotImplementedError(f"{self.item_name} with id '{id}' does not exist")

        return self._items[id]

    def has(self, id: ID) -> bool:
        return id in self._items

    def values(self) -> Iterable[ITEM]:
        return self._items.values()
