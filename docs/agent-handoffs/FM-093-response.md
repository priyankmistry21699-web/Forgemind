# FM-093 — Local Chat Over Codebase

## Summary

Implemented local codebase Q&A that answers developer questions using the repo index, file content snippets, and optional LLM integration. Works fully offline with rule-based keyword matching as fallback.

## Deliverables

### Service (`apps/local/forgemind_local/local_chat.py` — 155 lines)

- **`answer_question(repo_root, question)`** — returns `{"answer": str, "citations": list[str]}`
- **Keyword search** — scores files against query keywords by path and content matching
- **Intent detection** — regex patterns for "show me" (file display) and "where is" (file location)
- **File snippets** — reads first N lines of matched files for inline display
- **LLM integration** — optional LiteLLM via `FORGEMIND_LLM_MODEL` env var; graceful degradation when unavailable
- **Offline fallback** — rule-based answers from keyword matching when no LLM

### CLI

- **`forgemind ask "question"`** — queries codebase and prints answer with citations

## Design Notes

- Without LLM, the chat is effectively "grep with formatting" — functional but not intelligent
- LLM path truncates context to 8000 chars to stay within token limits
- System prompt identifies as "ForgeMind Local, a developer workstation assistant"

## Tests

3 tests in `TestLocalChat`:

- answer_question_returns_dict, answer_without_index_falls_back, answer_with_matching_files

## Test Results

- **Total**: 535 passing
