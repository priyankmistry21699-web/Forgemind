"""forgemind-core — Core domain constants and LLM client.

Provides shared enums, domain constants, and a thin LLM wrapper.
"""

from forgemind_core.constants import (
    PROJECT_STATUSES,
    RUN_STATUSES,
    TASK_STATUSES,
    ARTIFACT_TYPES,
    AGENT_STATUSES,
)
from forgemind_core.llm import llm_completion, llm_json_completion

__all__ = [
    "PROJECT_STATUSES",
    "RUN_STATUSES",
    "TASK_STATUSES",
    "ARTIFACT_TYPES",
    "AGENT_STATUSES",
    "llm_completion",
    "llm_json_completion",
]
