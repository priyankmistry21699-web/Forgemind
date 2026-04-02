"""FM-078: Observability and metrics tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestMetrics:

    async def test_metrics_endpoint_exists(self, client: AsyncClient):
        """The /metrics endpoint should return Prometheus-format text."""
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers.get("content-type", "")

    async def test_metrics_after_request(self, client: AsyncClient):
        """After making a request, counters should appear in /metrics."""
        # Make a request that registers metrics
        await client.get("/health")
        resp = await client.get("/metrics")
        body = resp.text
        assert "http_requests_total" in body
        assert "http_request_duration_seconds" in body

    async def test_counter_increment(self):
        """Counter should increment correctly."""
        from app.core.metrics import inc_counter, get_counter, reset_metrics
        reset_metrics()

        inc_counter("test_counter")
        assert get_counter("test_counter") == 1.0

        inc_counter("test_counter", 5.0)
        assert get_counter("test_counter") == 6.0

        reset_metrics()

    async def test_labeled_counter(self):
        """Labeled counters should track independently."""
        from app.core.metrics import inc_counter, get_counter, reset_metrics
        reset_metrics()

        inc_counter("req", labels={"method": "GET", "path": "/a"})
        inc_counter("req", labels={"method": "POST", "path": "/b"})
        inc_counter("req", labels={"method": "GET", "path": "/a"})

        assert get_counter("req", labels={"method": "GET", "path": "/a"}) == 2.0
        assert get_counter("req", labels={"method": "POST", "path": "/b"}) == 1.0

        reset_metrics()

    async def test_histogram_observation(self):
        """Histogram should bucket observations correctly."""
        from app.core.metrics import observe_histogram, render_prometheus, reset_metrics
        reset_metrics()

        observe_histogram("test_hist", 0.05)
        observe_histogram("test_hist", 0.5)
        observe_histogram("test_hist", 2.0)

        output = render_prometheus()
        assert "test_hist_count" in output
        assert "test_hist_sum" in output
        assert "test_hist_bucket" in output

        reset_metrics()

    async def test_prometheus_format(self):
        """Render should output valid Prometheus text format."""
        from app.core.metrics import inc_counter, observe_histogram, render_prometheus, reset_metrics
        reset_metrics()

        inc_counter("http_requests_total", labels={"method": "GET", "status": "200"})
        observe_histogram("http_request_duration_seconds", 0.123)

        output = render_prometheus()
        # Type declarations
        assert "# TYPE http_requests_total counter" in output
        assert "# TYPE http_request_duration_seconds histogram" in output
        # Label format
        assert 'method="GET"' in output
        assert 'status="200"' in output

        reset_metrics()

    async def test_request_id_in_response_header(self, client: AsyncClient):
        """Every response should include X-Request-ID header."""
        resp = await client.get("/health")
        assert "X-Request-ID" in resp.headers
        assert len(resp.headers["X-Request-ID"]) == 8
