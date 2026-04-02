# FM-074 — Real Authentication Integration

## Summary

Replaced the stub auth system with real JWT-based authentication across the entire platform. Backend routes now use real auth, a login/register flow exists on the frontend, and all dashboard pages are gated behind authentication.

## Backend Changes

### Auth Core (`apps/api/app/core/auth.py`)
- Refactored `_get_jwt_secret()` to always return the secret string
- Added `_is_dev_mode()` helper to detect default dev secret
- `create_access_token()` now works in both dev and prod modes (logs warning in dev)
- `get_current_user_id()`: verifies token if provided; falls back to stub only in dev mode with no token; returns 401 in prod with no token

### Auth Routes (`apps/api/app/api/routes/auth.py`)
- `POST /auth/register` — create new user with hashed password, return JWT
- `POST /auth/login` — verify credentials, return JWT
- `GET /auth/me` — return current user profile from token

### Auth Schemas (`apps/api/app/schemas/auth.py`)
- `RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserResponse`

### User Model (`apps/api/app/models/user.py`)
- Added nullable `password_hash` column

### Route Import Migration
- All 7 route files (activity, code_ops, members, notifications, projects, planner, workspaces) switched from `auth_stub` → `auth`

### Router (`apps/api/app/api/router.py`)
- Registered auth_router under `tags=["auth"]`

## Frontend Changes

### Auth Context (`apps/web/lib/auth-context.tsx`)
- `AuthProvider` with login/register/logout functions
- Token stored in localStorage (`forgemind_token`)
- `useAuth()` hook exposes user, token, loading, login, register, logout

### API Client (`apps/web/lib/api.ts`)
- Now attaches `Authorization: Bearer <token>` from localStorage on every request

### Login Page (`apps/web/app/login/page.tsx`)
- Login/register form with mode toggle, error display, redirect on success

### Auth Guard (`apps/web/components/auth-guard.tsx`)
- Redirects to `/login` if not authenticated, shows spinner while loading

### Providers Wrapper (`apps/web/components/providers.tsx`)
- Client-side wrapper for `AuthProvider` used in root layout

### Layout Updates
- `app/layout.tsx` — wrapped with `<Providers>`
- `app/dashboard/layout.tsx` — wrapped with `<AuthGuard>`
- `sidebar.tsx` — added user display + logout button

## Tests

- **10/10** new auth tests pass (`test_fm074_auth.py`)
- **34/34** regression tests pass (`test_fm046_050_v2.py`)
- **0** TypeScript errors

## Dependencies

- `python-jose[cryptography]` — JWT encode/decode
