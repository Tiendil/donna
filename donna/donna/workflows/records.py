from donna.domain.types import RecordKindId
from donna.primitives.records.pure_text import PureText, PureTextKind

pure_text = PureTextKind(id=RecordKindId("pure_text"), item_class=PureText)

story_developer_description = PureTextKind(id=RecordKindId("story_developer_description"), item_class=PureText)
story_work_description = PureTextKind(id=RecordKindId("story_work_description"), item_class=PureText)
story_goal = PureTextKind(id=RecordKindId("story_goal"), item_class=PureText)
story_objective = PureTextKind(id=RecordKindId("story_objective"), item_class=PureText)
story_constraint = PureTextKind(id=RecordKindId("story_constraint"), item_class=PureText)
story_acceptance_criteria = PureTextKind(id=RecordKindId("story_acceptance_criteria"), item_class=PureText)
story_deliverable = PureTextKind(id=RecordKindId("story_deliverable"), item_class=PureText)
story_plan_item = PureTextKind(id=RecordKindId("story_plan_item"), item_class=PureText)
