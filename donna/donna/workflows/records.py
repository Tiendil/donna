
from donna.domain.types import RecordId, RecordKindId
from donna.primitives.records.pure_text import PureTextKind, PureText


pure_text = PureTextKind(id=RecordKindId("pure_text"), item_class=PureText)
