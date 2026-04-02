# forgemind-core

> Core domain constants, enums, and LLM client for the ForgeMind platform.

## Contents

| Module      | Description                                                                                                                  |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `constants` | Frozen sets for all domain statuses: `PROJECT_STATUSES`, `RUN_STATUSES`, `TASK_STATUSES`, `ARTIFACT_TYPES`, `AGENT_STATUSES` |
| `llm`       | Thin async LiteLLM wrapper: `llm_completion()`, `llm_json_completion()`, `LLMConfig` dataclass                               |

## Usage

```python
from forgemind_core import PROJECT_STATUSES, llm_completion, llm_json_completion
```
