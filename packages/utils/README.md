# forgemind-utils

> Shared Python utilities, middleware, and observability for the ForgeMind platform.

## Contents

| Module               | Description                                                         |
| -------------------- | ------------------------------------------------------------------- |
| `metrics`            | Thread-safe in-memory Prometheus-compatible counters and histograms |
| `rate_limit`         | Token-bucket per-IP rate limiting middleware                        |
| `error_handlers`     | Structured JSON error responses for FastAPI                         |
| `logging_middleware` | Request logging with timing and X-Request-ID header                 |

## Usage

```python
from forgemind_utils import inc_counter, RateLimitMiddleware, register_error_handlers
```
