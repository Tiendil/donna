
# Artifacts capabilities

Currently we define artifacts via their kinds and the kind defines what operations can be done with the artifact.

So, we have cli commands like

- The command `donna artifacts text write <artifact-id> <content>` will work only for plain text artifacts
- The command `donna artifacts list add-item <artifact-id> <item-id> <item-content>` will work only for list and graph artifacts

It works for now, but we may want to switch to capability-based approach in the future. It may be more flexible and simplify extending the system with new artifact kinds.

# Capabilities

Donna can define a list of default capabilities for artifacts, like

- `read-as-text`
- `write-as-text`
- `add-item`
- `remove-item`

So the artifact implementation can declare what capabilities it supports.

That will give us a simpler and unified CLI interface for artifacts, like

- The command `donna artifacts write <artifact-id> <content>` will work for all artifacts that support `write-as-text` capability.
- The command `donna artifacts add-item <artifact-id> <item-id> <item-content>` will work for all artifacts that support `add-item` capability.

# Questions

1. Some developers may want to introduce very specific artifact kinds with very specific operations over them.

It may be weired to define custom capabilities for them.

Also, some capability names may intersect with default capabilities. That can be normal from the semantic point of view, but may lead to confusion of agents and developers.

2. There may be difficult for agents to keep in mind what capabilities are supported for the artifact they work with.

We may need to introduce a powerfull but simple way to introspect artifact capabilities.
