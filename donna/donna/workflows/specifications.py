
from donna.machine.specifications import SpecificationSource, Specification, SpecificationIndexItem
from donna.primitives.specifications.static import StaticSpecificationSource


spec_planning = Specification(
    item=SpecificationIndexItem(
        namespace="donna/workflows",
        id="basic_planning",
        name="Basic Planning Specification",
        description="A specification outlining the fundamental principles of planning.",
    ),
    content="""
    Some planning is the act of thinking about and organizing the activities required to achieve a desired goal.
    """
)


donna_workflows = StaticSpecificationSource(
    id="donna_workflows",
    specifications=[
        spec_planning
    ])
