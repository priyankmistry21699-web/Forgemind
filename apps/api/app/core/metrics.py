"""Observability metrics — in-memory counters and histograms.

FM-078: Provides lightweight Prometheus-compatible metrics without
requiring an external metrics library. Metrics are exposed via /metrics
in Prometheus text exposition format.
"""

import time
import threading
from collections import defaultdict
from typing import Any

_lock = threading.Lock()

# ── Counters ─────────────────────────────────────────────────────
_counters: dict[str, float] = defaultdict(float)
_counter_labels: dict[str, dict[str, dict[str, float]]] = {}

# ── Histograms (simple bucket-based) ─────────────────────────────
_DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
_histograms: dict[str, dict[str, Any]] = {}


def inc_counter(name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
    """Increment a counter metric."""
    with _lock:
        if labels:
            if name not in _counter_labels:
                _counter_labels[name] = {}
            key = _label_key(labels)
            if key not in _counter_labels[name]:
                _counter_labels[name][key] = {"labels": labels, "value": 0.0}
            _counter_labels[name][key]["value"] += value
        else:
            _counters[name] += value


def observe_histogram(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    """Record a value in a histogram."""
    with _lock:
        key = _label_key(labels) if labels else ""
        if name not in _histograms:
            _histograms[name] = {}
        if key not in _histograms[name]:
            _histograms[name][key] = {
                "labels": labels or {},
                "buckets": {b: 0 for b in _DEFAULT_BUCKETS},
                "sum": 0.0,
                "count": 0,
                "inf": 0,
            }
        h = _histograms[name][key]
        h["sum"] += value
        h["count"] += 1
        h["inf"] += 1
        for b in _DEFAULT_BUCKETS:
            if value <= b:
                h["buckets"][b] += 1


def get_counter(name: str, labels: dict[str, str] | None = None) -> float:
    """Get the current value of a counter."""
    with _lock:
        if labels:
            key = _label_key(labels)
            entry = (_counter_labels.get(name, {}).get(key))
            return entry["value"] if entry else 0.0
        return _counters.get(name, 0.0)


def render_prometheus() -> str:
    """Render all metrics in Prometheus text exposition format."""
    lines: list[str] = []
    with _lock:
        # Simple counters
        for name, value in sorted(_counters.items()):
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        # Labeled counters
        for name, entries in sorted(_counter_labels.items()):
            lines.append(f"# TYPE {name} counter")
            for entry in entries.values():
                lbl = _format_labels(entry["labels"])
                lines.append(f"{name}{lbl} {entry['value']}")

        # Histograms
        for name, entries in sorted(_histograms.items()):
            lines.append(f"# TYPE {name} histogram")
            for entry in entries.values():
                lbl_base = entry["labels"]
                for bucket, count in sorted(entry["buckets"].items()):
                    lbl = _format_labels({**lbl_base, "le": str(bucket)})
                    lines.append(f"{name}_bucket{lbl} {count}")
                lbl_inf = _format_labels({**lbl_base, "le": "+Inf"})
                lines.append(f"{name}_bucket{lbl_inf} {entry['inf']}")
                lbl = _format_labels(lbl_base) if lbl_base else ""
                lines.append(f"{name}_sum{lbl} {entry['sum']}")
                lines.append(f"{name}_count{lbl} {entry['count']}")

    lines.append("")
    return "\n".join(lines)


def reset_metrics() -> None:
    """Reset all metrics (for testing)."""
    with _lock:
        _counters.clear()
        _counter_labels.clear()
        _histograms.clear()


# ── Helpers ──────────────────────────────────────────────────────

def _label_key(labels: dict[str, str] | None) -> str:
    if not labels:
        return ""
    return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


def _format_labels(labels: dict[str, str]) -> str:
    if not labels:
        return ""
    parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
    return "{" + ",".join(parts) + "}"
