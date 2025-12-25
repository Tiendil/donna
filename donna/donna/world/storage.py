from typing import Iterable, Protocol


class StorageItem[ID](Protocol):
    id: ID


class Storage[ID, ITEM: StorageItem[ID]]:
    __slots__ = ("_items", "item_name")

    def __init__(self, item_name: str) -> None:
        self.item_name = item_name
        self._items: dict[ID, ITEM] = {}

    def add(self, item: ITEM) -> None:
        if item.id in self._items:
            raise NotImplementedError(f"{self.item_name} with id '{item.id}' already exists")

        self._items[item.id] = item

    def get(self, id: ID) -> ITEM:
        if id not in self._items:
            raise NotImplementedError(f"{self.item_name} with id '{id}' does not exist")

        return self._items[id]

    def has(self, id: ID) -> bool:
        return id in self._items

    def values(self) -> Iterable[ITEM]:
        return self._items.values()
