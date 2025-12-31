from donna.domain.types import RecordKindId
from donna.primitives.records.pure_text import PureText, PureTextKind

pure_text = PureTextKind(id=RecordKindId("pure_text"), item_class=PureText)

story_goal = PureTextKind(id=RecordKindId("story_goal"), item_class=PureText)
story_objective = PureTextKind(id=RecordKindId("story_objective"), item_class=PureText)
