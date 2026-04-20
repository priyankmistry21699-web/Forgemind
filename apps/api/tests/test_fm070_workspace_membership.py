"""FM-070 aggregate — workspace & membership hardening smoke tests.

FM-051 → FM-070 cover workspace/member RBAC, project roles, invitations, and
the workspace + member service layer. This file encodes a contract-level
snapshot so audit evidence for the FM-070 milestone is grep-able.
"""


class TestFM070WorkspaceRoutesMounted:
    def test_workspace_and_member_routes_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any(p.startswith("/workspaces") for p in paths)
        assert any("/members" in p for p in paths)


class TestFM070MembershipModels:
    def test_workspace_member_and_roles_importable(self):
        from app.models.membership import (
            WorkspaceMember,
            WorkspaceRole,
            ProjectMember,
            ProjectRole,
        )

        # Role enums must cover the RBAC matrix FM-052/053 promised.
        assert {r.value for r in WorkspaceRole} >= {
            "owner",
            "admin",
            "operator",
            "reviewer",
            "viewer",
        }
        assert {r.value for r in ProjectRole} >= {
            "lead",
            "operator",
            "reviewer",
            "viewer",
        }
        assert WorkspaceMember.__tablename__ == "workspace_members"
        assert ProjectMember.__tablename__ == "project_members"


class TestFM070Services:
    def test_workspace_and_membership_services_importable(self):
        from app.services import workspace_service, membership_service

        assert workspace_service is not None
        assert membership_service is not None


class TestFM070WorkspaceSchema:
    def test_workspace_schemas_importable(self):
        from app.schemas.workspace import WorkspaceRead, WorkspaceCreate

        assert WorkspaceRead is not None
        assert WorkspaceCreate is not None
