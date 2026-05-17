import pydantic
import pytest

from donna.core.entities import BaseEntity


class _NestedEntity(BaseEntity):
    values: list[int]


class _SampleEntity(BaseEntity):
    name: str
    nested: _NestedEntity


class TestBaseEntity:
    def test_model_config__strips_strings_and_forbids_extra_fields(self) -> None:
        entity = _SampleEntity(name="  value  ", nested=_NestedEntity(values=[]))

        assert entity.name == "value"

        with pytest.raises(pydantic.ValidationError):
            _SampleEntity(name="value", nested=_NestedEntity(values=[]), extra=True)

    def test_model_config__is_frozen(self) -> None:
        entity = _SampleEntity(name="value", nested=_NestedEntity(values=[]))

        with pytest.raises(pydantic.ValidationError):
            entity.name = "changed"

    def test_replace__returns_deep_copy_with_changes(self) -> None:
        entity = _SampleEntity(name="before", nested=_NestedEntity(values=[1]))

        replaced = entity.replace(name="after")
        replaced.nested.values.append(2)

        assert entity.name == "before"
        assert entity.nested.values == [1]
        assert replaced.name == "after"
        assert replaced.nested.values == [1, 2]

    def test_to_json__serializes_entity(self) -> None:
        entity = _SampleEntity(name="value", nested=_NestedEntity(values=[1, 2]))

        assert (
            entity.to_json()
            == '{\n  "name": "value",\n  "nested": {\n    "values": [\n      1,\n      2\n    ]\n  }\n}'
        )

    def test_from_json__deserializes_entity(self) -> None:
        entity = _SampleEntity.from_json('{"name": "value", "nested": {"values": [1]}}')

        assert entity == _SampleEntity(name="value", nested=_NestedEntity(values=[1]))
