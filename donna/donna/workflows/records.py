from donna.domain import types
from donna.domain.types import RecordKindId
from donna.primitives.records.pure_text import PureText, PureTextKind

pure_text = PureTextKind(id=RecordKindId(types.Slug("pure_text")), item_class=PureText)

session_developer_description = PureTextKind(
    id=RecordKindId(types.Slug("session_developer_description")),
    item_class=PureText,
)
session_work_description = PureTextKind(
    id=RecordKindId(types.Slug("session_work_description")),
    item_class=PureText,
)
session_goal = PureTextKind(id=RecordKindId(types.Slug("session_goal")), item_class=PureText)
session_objective = PureTextKind(id=RecordKindId(types.Slug("session_objective")), item_class=PureText)
session_constraint = PureTextKind(id=RecordKindId(types.Slug("session_constraint")), item_class=PureText)
session_acceptance_criteria = PureTextKind(
    id=RecordKindId(types.Slug("session_acceptance_criteria")),
    item_class=PureText,
)
session_deliverable = PureTextKind(id=RecordKindId(types.Slug("session_deliverable")), item_class=PureText)
session_plan_item = PureTextKind(id=RecordKindId(types.Slug("session_plan_item")), item_class=PureText)
