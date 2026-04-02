# forgemind-security

> Authentication and authorization primitives for the ForgeMind platform.

## Contents

| Module | Description                                                                                                                                                                  |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `jwt`  | Stateless JWT create/decode helpers using python-jose (`JWTConfig`, `create_token`, `decode_token`)                                                                          |
| `rbac` | Pure RBAC permission engine: `Action` enum (20 actions), `WorkspaceRole`/`ProjectRole` enums, permission matrices, `is_workspace_action_allowed`/`is_project_action_allowed` |

## Usage

```python
from forgemind_security import create_token, JWTConfig, Action, is_workspace_action_allowed
```
