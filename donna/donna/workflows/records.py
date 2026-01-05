from donna.domain import types
from donna.domain.types import RecordKindId
from donna.primitives.records.pure_text import PureText, PureTextKind

pure_text = PureTextKind(id=RecordKindId(types.Slug("pure_text")), item_class=PureText)

story_developer_description = PureTextKind(
    id=RecordKindId(types.Slug("story_developer_description")),
    item_class=PureText,
)
story_work_description = PureTextKind(
    id=RecordKindId(types.Slug("story_work_description")),
    item_class=PureText,
)
story_goal = PureTextKind(id=RecordKindId(types.Slug("story_goal")), item_class=PureText)
story_objective = PureTextKind(id=RecordKindId(types.Slug("story_objective")), item_class=PureText)
story_constraint = PureTextKind(id=RecordKindId(types.Slug("story_constraint")), item_class=PureText)
story_acceptance_criteria = PureTextKind(
    id=RecordKindId(types.Slug("story_acceptance_criteria")),
    item_class=PureText,
)
story_deliverable = PureTextKind(id=RecordKindId(types.Slug("story_deliverable")), item_class=PureText)
story_plan_item = PureTextKind(id=RecordKindId(types.Slug("story_plan_item")), item_class=PureText)
