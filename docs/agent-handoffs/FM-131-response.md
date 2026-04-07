# FM-131 — Release Package Model & Generation

## Goal

Versioned release bundles with auto-generated manifests, changelogs, and confidence snapshots.

## What Was Implemented

- `ReleasePackage` ORM model with `ReleaseStatus` enum (draft, ready, gated, approved, deployed, rolled_back, failed)
- Auto-generation from run state: artifact manifest, changelog from completed tasks, confidence snapshot, rollback metadata
- CRUD service + auto-versioning (`0.{n}.0`)
- Pydantic schemas: `ReleasePackageCreate`, `ReleasePackageUpdate`, `ReleasePackageRead`, `ReleasePackageList`

## Key Files

- `apps/api/app/models/release_ops.py`
- `apps/api/app/schemas/release_ops.py`
- `apps/api/app/services/release_package_service.py`

## Status

✅ Complete
