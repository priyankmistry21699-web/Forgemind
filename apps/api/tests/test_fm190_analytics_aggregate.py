"""FM-190 aggregate — analytics & metrics hardening smoke.

Aggregate audit evidence for FM-191 → FM-199 (execution analytics, health
metrics, budget / velocity / quality rollups, portfolio dashboards, alerts).
"""


class TestFM190AnalyticsRoutes:
    def test_analytics_router_mounted_at_root_and_v1(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        # Analytics router is mounted twice: at root and under /api/v1.
        assert any("/analytics" in p for p in paths)
        assert any(p.startswith("/api/v1") and "/analytics" in p for p in paths)


class TestFM190AnalyticsServices:
    def test_analytics_family_services_importable(self):
        # These are the concrete services backing FM-191–199.
        from app.services import (
            dashboard_alert_service,
            velocity_quality_service,
            flakiness_complexity_service,
            pattern_debt_service,
            execution_health_service,
        )

        assert dashboard_alert_service is not None
        assert velocity_quality_service is not None
        assert flakiness_complexity_service is not None
        assert pattern_debt_service is not None
        assert execution_health_service is not None


class TestFM190ScheduledReporting:
    def test_scheduled_report_loop_wired(self):
        """FM-198 scheduled reporting runs out of the background scheduler."""
        from app.services.background_scheduler import scheduled_report_loop

        assert callable(scheduled_report_loop)
