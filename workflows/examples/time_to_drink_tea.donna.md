# Is it time to drink tea?

This workflow checks the current time, asks the agent whether it is tea time,
and branches on the answer.

## Get Current Time

```toml donna
id = "get_current_time"
kind = "donna.lib.run_script"
save_stdout_to = "current_time"
goto_on_success = "ask_about_tea"
goto_on_failure = "finish"
```

```bash donna script
#!/usr/bin/env bash
date +%H:%M
```

## Ask About Tea

```toml donna
id = "ask_about_tea"
kind = "donna.lib.request_action"
```

The current time is:

```text
{{ donna.lib.task_variable("current_time") }}
```

Is it time to drink tea?

1. If yes, `{{ donna.lib.goto("turn_on_kettle") }}`.
1. If no, `{{ donna.lib.goto("finish") }}`.

## Turn On Kettle

```toml donna
id = "turn_on_kettle"
kind = "donna.lib.request_action"
```

Turn on the kettle, then `{{ donna.lib.goto("finish") }}`.

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

The workflow is complete. Report the result to the developer.
